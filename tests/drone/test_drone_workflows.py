"""
Integration Tests for Drone Detection Workflows
Tests end-to-end workflow execution with drone nodes
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.workflows.drone_executor import DroneWorkflowExecutor
from backend.models.drone_detection import DroneDetection
from backend.workflows.drone_schema import validate_drone_node_config


class TestDroneNodeSchemaValidation:
    """Tests for drone node configuration validation"""
    
    def test_valid_drone_input_config(self):
        """Test valid DroneInputNode configuration"""
        config = {
            "receiver_id": "mesh-receiver-01",
            "min_rssi": -95,
            "update_rate": 1.0
        }
        
        is_valid, error = validate_drone_node_config("droneInput", config)
        assert is_valid is True
        assert error == ""
    
    def test_missing_required_field(self):
        """Test configuration missing required field"""
        config = {
            "min_rssi": -95
            # Missing receiver_id
        }
        
        is_valid, error = validate_drone_node_config("droneInput", config)
        assert is_valid is False
        assert "receiver_id" in error.lower()
    
    def test_valid_filter_config(self):
        """Test valid DroneFilterNode configuration"""
        config = {
            "altitude_min": 0,
            "altitude_max": 500,
            "speed_min": 0,
            "speed_max": 50,
            "geofence_ids": ["airport_approach"],
            "filter_mode": "pass_violations"
        }
        
        is_valid, error = validate_drone_node_config("droneFilter", config)
        assert is_valid is True
    
    def test_invalid_altitude_range(self):
        """Test invalid altitude range (min >= max)"""
        config = {
            "altitude_min": 500,
            "altitude_max": 100  # Invalid: min > max
        }
        
        is_valid, error = validate_drone_node_config("droneFilter", config)
        assert is_valid is False
        assert "altitude" in error.lower()
    
    def test_valid_action_config(self):
        """Test valid DroneActionNode configuration"""
        config = {
            "action_type": "alarm",
            "alarm_severity": "critical",
            "alarm_title": "Drone Violation: {remote_id}"
        }
        
        is_valid, error = validate_drone_node_config("droneAction", config)
        assert is_valid is True
    
    def test_invalid_action_type(self):
        """Test invalid action type"""
        config = {
            "action_type": "invalid_action"
        }
        
        is_valid, error = validate_drone_node_config("droneAction", config)
        assert is_valid is False
    
    def test_valid_map_config(self):
        """Test valid DroneMapNode configuration"""
        config = {
            "center_lat": 37.422,
            "center_lon": -122.084,
            "initial_zoom": 14,
            "show_geofences": True
        }
        
        is_valid, error = validate_drone_node_config("droneMap", config)
        assert is_valid is True
    
    def test_invalid_coordinates(self):
        """Test invalid map coordinates"""
        config = {
            "center_lat": 95,  # Invalid: > 90
            "center_lon": -122.084
        }
        
        is_valid, error = validate_drone_node_config("droneMap", config)
        assert is_valid is False


@pytest.mark.asyncio
class TestDroneWorkflowExecution:
    """Tests for complete drone workflow execution"""
    
    async def test_simple_workflow(self):
        """Test simple workflow: input → filter → action"""
        workflow_config = {
            "nodes": [
                {
                    "id": "input1",
                    "type": "droneInput",
                    "data": {"receiver_id": "receiver-01"}
                },
                {
                    "id": "filter1",
                    "type": "droneFilter",
                    "data": {
                        "altitude_min": 0,
                        "altitude_max": 200,
                        "filter_mode": "pass_matching"
                    }
                },
                {
                    "id": "action1",
                    "type": "droneAction",
                    "data": {
                        "action_type": "alarm",
                        "alarm_severity": "high"
                    }
                }
            ],
            "edges": [
                {"source": "input1", "target": "filter1"},
                {"source": "filter1", "target": "action1"}
            ]
        }
        
        # Mock managers
        mock_drone_manager = Mock()
        mock_alarm_manager = AsyncMock()
        
        executor = DroneWorkflowExecutor(
            workflow_id="test-workflow",
            workflow_config=workflow_config,
            drone_event_manager=mock_drone_manager,
            alarm_manager=mock_alarm_manager
        )
        
        # Should parse workflow correctly
        assert len(executor.nodes) == 3
        assert len(executor.input_nodes) == 1
    
    async def test_altitude_filter(self):
        """Test altitude filtering in workflow"""
        workflow_config = {
            "nodes": [
                {
                    "id": "filter1",
                    "type": "droneFilter",
                    "data": {
                        "altitude_min": 50,
                        "altitude_max": 150
                    }
                }
            ],
            "edges": []
        }
        
        executor = DroneWorkflowExecutor(
            workflow_id="test-filter",
            workflow_config=workflow_config,
            drone_event_manager=Mock(),
            alarm_manager=None
        )
        
        filter_node = executor.nodes["filter1"]
        
        # Detection within range
        detection1 = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10
        )
        
        result = await executor._process_filter_node(filter_node, detection1)
        assert result is True
        
        # Detection below range
        detection2 = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=30,
            speed=10
        )
        
        result = await executor._process_filter_node(filter_node, detection2)
        assert result is False
    
    async def test_speed_filter(self):
        """Test speed filtering in workflow"""
        workflow_config = {
            "nodes": [
                {
                    "id": "filter1",
                    "type": "droneFilter",
                    "data": {
                        "speed_min": 5,
                        "speed_max": 25
                    }
                }
            ],
            "edges": []
        }
        
        executor = DroneWorkflowExecutor(
            workflow_id="test-speed",
            workflow_config=workflow_config,
            drone_event_manager=Mock(),
            alarm_manager=None
        )
        
        filter_node = executor.nodes["filter1"]
        
        # Within range
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=15
        )
        
        result = await executor._process_filter_node(filter_node, detection)
        assert result is True
        
        # Too fast
        detection_fast = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=50
        )
        
        result = await executor._process_filter_node(filter_node, detection_fast)
        assert result is False
    
    async def test_alarm_action(self):
        """Test alarm creation action"""
        mock_alarm_manager = AsyncMock()
        
        workflow_config = {
            "nodes": [
                {
                    "id": "action1",
                    "type": "droneAction",
                    "data": {
                        "action_type": "alarm",
                        "alarm_severity": "critical",
                        "alarm_title": "Drone {remote_id} detected"
                    }
                }
            ],
            "edges": []
        }
        
        executor = DroneWorkflowExecutor(
            workflow_id="test-alarm",
            workflow_config=workflow_config,
            drone_event_manager=Mock(),
            alarm_manager=mock_alarm_manager
        )
        
        action_node = executor.nodes["action1"]
        
        detection = DroneDetection(
            remote_id="DRONE123",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10
        )
        
        await executor._process_action_node(action_node, detection)
        
        # Verify alarm was created
        assert mock_alarm_manager.create_alarm.called
        call_args = mock_alarm_manager.create_alarm.call_args[0][0]
        assert call_args['severity'] == 'critical'
        assert 'DRONE123' in call_args['title']
    
    async def test_multiple_concurrent_drones(self):
        """Test handling multiple drones simultaneously"""
        workflow_config = {
            "nodes": [
                {
                    "id": "input1",
                    "type": "droneInput",
                    "data": {"receiver_id": "receiver-01"}
                }
            ],
            "edges": []
        }
        
        mock_drone_manager = Mock()
        executor = DroneWorkflowExecutor(
            workflow_id="test-concurrent",
            workflow_config=workflow_config,
            drone_event_manager=mock_drone_manager,
            alarm_manager=None
        )
        
        # Simulate multiple detections
        detections = [
            {
                "type": "drone_detection",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "remote_id": f"DRONE{i}",
                    "position": {"latitude": 37.422, "longitude": -122.084, "altitude": 100},
                    "velocity": {"speed": 10, "heading": 45, "vertical_speed": 0},
                    "operator": {},
                    "receiver_id": "receiver-01",
                    "geofence_violations": []
                }
            }
            for i in range(10)
        ]
        
        # Process all detections
        for det in detections:
            await executor._on_drone_detection(det)
        
        # Should track all 10 drones
        assert len(executor.drone_tracks) == 10
    
    async def test_geofence_violation_workflow(self):
        """Test workflow with geofence violation"""
        workflow_config = {
            "nodes": [
                {
                    "id": "filter1",
                    "type": "droneFilter",
                    "data": {
                        "geofence_ids": ["restricted_zone"],
                        "filter_mode": "pass_violations"
                    }
                }
            ],
            "edges": []
        }
        
        executor = DroneWorkflowExecutor(
            workflow_id="test-geofence",
            workflow_config=workflow_config,
            drone_event_manager=Mock(),
            alarm_manager=None
        )
        
        filter_node = executor.nodes["filter1"]
        
        # Detection with violation
        detection_violation = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10,
            geofence_violations=["restricted_zone"]
        )
        
        result = await executor._process_filter_node(filter_node, detection_violation)
        # Should pass in "pass_violations" mode
        assert result is True
        
        # Detection without violation
        detection_clean = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10,
            geofence_violations=[]
        )
        
        result = await executor._process_filter_node(filter_node, detection_clean)
        # Should not pass in "pass_violations" mode
        assert result is False

