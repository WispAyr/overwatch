"""
Drone Workflow Executor
Executes drone detection workflows with filtering and actions
"""
import asyncio
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
from dataclasses import dataclass

from models.drone_detection import DroneDetection
from workflows.drone_schema import validate_drone_node_config
from workflows.event_bus import get_event_bus, EventType, WorkflowEvent

logger = logging.getLogger(__name__)


@dataclass
class DroneWorkflowNode:
    """Drone workflow node definition"""
    id: str
    type: str
    config: Dict
    connections: List[str]  # Node IDs this node connects to


class DroneWorkflowExecutor:
    """
    Executes drone detection workflows
    Routes drone data through workflow graph: input → filters → actions
    """
    
    def __init__(self, workflow_id: str, workflow_config: Dict, 
                 drone_event_manager, alarm_manager=None):
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.drone_event_manager = drone_event_manager
        self.alarm_manager = alarm_manager
        
        # Parse workflow graph
        self.nodes: Dict[str, DroneWorkflowNode] = {}
        self.input_nodes: Set[str] = set()
        self.running = False
        
        # Track state
        self.drone_tracks: Dict[str, List[DroneDetection]] = {}
        self.execution_count = 0
        
        # Event bus for debug/monitoring
        self.event_bus = get_event_bus()
        
        # Per-node metrics
        self.node_metrics: Dict[str, Dict] = {}
        
        self._parse_workflow()
    
    def _parse_workflow(self):
        """Parse workflow configuration into node graph"""
        nodes = self.workflow_config.get('nodes', [])
        edges = self.workflow_config.get('edges', [])
        
        # Build node map
        for node_config in nodes:
            node_id = node_config['id']
            node_type = node_config.get('type')
            
            # Validate node configuration
            config = node_config.get('data', {})
            is_valid, error = validate_drone_node_config(node_type, config)
            if not is_valid:
                logger.error(f"Invalid node config {node_id}: {error}")
                continue
            
            self.nodes[node_id] = DroneWorkflowNode(
                id=node_id,
                type=node_type,
                config=config,
                connections=[]
            )
            
            # Track input nodes
            if node_type == 'droneInput':
                self.input_nodes.add(node_id)
        
        # Build connections
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            
            if source in self.nodes:
                self.nodes[source].connections.append(target)
        
        logger.info(f"Parsed drone workflow {self.workflow_id}: "
                   f"{len(self.nodes)} nodes, {len(self.input_nodes)} inputs")
    
    async def start(self):
        """Start workflow execution"""
        self.running = True
        logger.info(f"Starting drone workflow executor: {self.workflow_id}")
        
        # Emit workflow start event
        await self.event_bus.emit(WorkflowEvent(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id=self.workflow_id,
            node_id=None,
            timestamp=datetime.utcnow(),
            data={'node_count': len(self.nodes)}
        ))
        
        # Subscribe to drone detection events
        self.drone_event_manager.register_callback(self._on_drone_detection)
    
    async def stop(self):
        """Stop workflow execution"""
        self.running = False
        logger.info(f"Stopped drone workflow executor: {self.workflow_id}")
        
        # Emit workflow stop event
        await self.event_bus.emit(WorkflowEvent(
            event_type=EventType.WORKFLOW_STOPPED,
            workflow_id=self.workflow_id,
            node_id=None,
            timestamp=datetime.utcnow(),
            data={'execution_count': self.execution_count}
        ))
    
    async def _on_drone_detection(self, detection_event: Dict):
        """
        Handle incoming drone detection event
        Route through workflow graph
        """
        if not self.running:
            return
        
        try:
            # Convert event to DroneDetection model
            detection = self._event_to_detection(detection_event)
            
            # Track detection history
            remote_id = detection.remote_id
            if remote_id not in self.drone_tracks:
                self.drone_tracks[remote_id] = []
            self.drone_tracks[remote_id].append(detection)
            
            # Limit track history
            if len(self.drone_tracks[remote_id]) > 100:
                self.drone_tracks[remote_id] = self.drone_tracks[remote_id][-100:]
            
            # Execute workflow starting from input nodes
            for input_node_id in self.input_nodes:
                await self._execute_from_node(input_node_id, detection)
            
            self.execution_count += 1
        
        except Exception as e:
            logger.error(f"Error processing detection in workflow {self.workflow_id}: {e}", 
                        exc_info=True)
    
    async def _execute_from_node(self, node_id: str, detection: DroneDetection):
        """
        Execute workflow starting from a specific node
        Recursively processes connected nodes
        """
        if node_id not in self.nodes:
            return
        
        node = self.nodes[node_id]
        
        # Emit node started event
        await self.event_bus.emit(WorkflowEvent(
            event_type=EventType.NODE_STARTED,
            workflow_id=self.workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data={'node_type': node.type}
        ))
        
        # Process node based on type
        result = await self._process_node(node, detection)
        
        # Emit node completed event
        await self.event_bus.emit(WorkflowEvent(
            event_type=EventType.NODE_COMPLETED,
            workflow_id=self.workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data={
                'node_type': node.type,
                'result': result,
                'passed': result is not False
            }
        ))
        
        # If node returns False, stop propagation (filtered out)
        if result is False:
            return
        
        # Propagate to connected nodes
        for next_node_id in node.connections:
            await self._execute_from_node(next_node_id, detection)
    
    async def _process_node(self, node: DroneWorkflowNode, detection: DroneDetection) -> bool:
        """
        Process a single node
        Returns True to continue propagation, False to stop
        """
        try:
            if node.type == 'droneInput':
                result = await self._process_input_node(node, detection)
                
            elif node.type == 'droneFilter':
                result = await self._process_filter_node(node, detection)
                
            elif node.type == 'droneAction':
                result = await self._process_action_node(node, detection)
                
            elif node.type == 'droneAnalytics':
                result = await self._process_analytics_node(node, detection)
                
            elif node.type == 'droneMap':
                # Map nodes are visualization only, always pass through
                result = True
                # Emit map data for visualization
                await self.event_bus.emit(WorkflowEvent(
                    event_type=EventType.STATUS_UPDATE,
                    workflow_id=self.workflow_id,
                    node_id=node.id,
                    timestamp=datetime.utcnow(),
                    data={
                        'drone_id': detection.remote_id,
                        'position': {
                            'lat': detection.latitude,
                            'lon': detection.longitude,
                            'alt': detection.altitude
                        },
                        'violations': detection.geofence_violations
                    }
                ))
            
            else:
                logger.warning(f"Unknown drone node type: {node.type}")
                result = True
            
            # Emit detection data to debug nodes
            await self.event_bus.emit(WorkflowEvent(
                event_type=EventType.DETECTIONS_EMITTED,
                workflow_id=self.workflow_id,
                node_id=node.id,
                timestamp=datetime.utcnow(),
                data={
                    'drone_id': detection.remote_id,
                    'node_type': node.type,
                    'passed_filter': result,
                    'detections': [{
                        'remote_id': detection.remote_id,
                        'altitude': detection.altitude,
                        'speed': detection.speed,
                        'latitude': detection.latitude,
                        'longitude': detection.longitude,
                        'violations': detection.geofence_violations,
                        'rssi': detection.rssi
                    }]
                }
            ))
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing node {node.id}: {e}", exc_info=True)
            
            # Emit error event
            await self.event_bus.emit_error(
                workflow_id=self.workflow_id,
                node_id=node.id,
                error=e,
                meta={'node_type': node.type, 'drone_id': detection.remote_id}
            )
            
            return True
    
    async def _process_input_node(self, node: DroneWorkflowNode, 
                                  detection: DroneDetection) -> bool:
        """Process drone input node - filter by receiver"""
        config = node.config
        
        # Filter by receiver if specified (empty/None means all receivers)
        receiver_id = config.get('receiver_id')
        if receiver_id and receiver_id != '' and detection.receiver_id != receiver_id:
            return False
        
        # Filter by RSSI if specified
        min_rssi = config.get('min_rssi')
        if min_rssi and detection.rssi and detection.rssi < min_rssi:
            return False
        
        return True
    
    async def _process_filter_node(self, node: DroneWorkflowNode, 
                                   detection: DroneDetection) -> bool:
        """Process filter node - apply criteria"""
        config = node.config
        
        # Altitude filter
        alt_min = config.get('altitude_min', 0)
        alt_max = config.get('altitude_max', 10000)
        if not (alt_min <= detection.altitude <= alt_max):
            return False
        
        # Speed filter
        speed_min = config.get('speed_min', 0)
        speed_max = config.get('speed_max', 300)
        if not (speed_min <= detection.speed <= speed_max):
            return False
        
        # Geofence filter
        geofence_ids = config.get('geofence_ids', [])
        if geofence_ids:
            # Check if detection violates any of the specified geofences
            has_violation = any(
                gf_id in detection.geofence_violations 
                for gf_id in geofence_ids
            )
            
            filter_mode = config.get('filter_mode', 'pass_matching')
            if filter_mode == 'pass_violations' and not has_violation:
                return False
        
        # Operator distance filter
        max_distance = config.get('operator_distance_max')
        if max_distance:
            distance = detection.calculate_operator_distance()
            if distance is None or distance > max_distance:
                return False
        
        # RSSI filter
        rssi_min = config.get('rssi_min')
        if rssi_min and (not detection.rssi or detection.rssi < rssi_min):
            return False
        
        return True
    
    async def _process_action_node(self, node: DroneWorkflowNode, 
                                   detection: DroneDetection) -> bool:
        """Process action node - trigger responses"""
        config = node.config
        action_type = config.get('action_type')
        
        if action_type == 'alarm':
            await self._create_alarm(config, detection)
        
        elif action_type == 'log_flight':
            await self._log_flight(config, detection)
        
        elif action_type == 'notify_authorities':
            await self._notify_authorities(config, detection)
        
        elif action_type == 'camera_slew':
            await self._slew_camera(config, detection)
        
        elif action_type == 'geofence_alert':
            await self._geofence_alert(config, detection)
        
        # Always pass through
        return True
    
    async def _process_analytics_node(self, node: DroneWorkflowNode, 
                                      detection: DroneDetection) -> bool:
        """Process analytics node - accumulate statistics"""
        # Analytics nodes accumulate data over time
        # Actual analysis would be done periodically or on-demand
        # For now, just pass through
        return True
    
    async def _create_alarm(self, config: Dict, detection: DroneDetection):
        """Create alarm for drone detection"""
        if not self.alarm_manager:
            logger.warning("Alarm manager not available")
            return
        
        severity = config.get('alarm_severity', 'high')
        title = config.get('alarm_title', 'Drone Detection Alert')
        
        # Format title with detection data
        title_formatted = title.format(
            remote_id=detection.remote_id,
            altitude=detection.altitude,
            speed=detection.speed
        )
        
        alarm_data = {
            "title": title_formatted,
            "severity": severity,
            "type": "drone_detection",
            "metadata": {
                "remote_id": detection.remote_id,
                "latitude": detection.latitude,
                "longitude": detection.longitude,
                "altitude": detection.altitude,
                "speed": detection.speed,
                "geofence_violations": detection.geofence_violations,
                "workflow_id": self.workflow_id
            },
            "timestamp": detection.timestamp.isoformat()
        }
        
        await self.alarm_manager.create_alarm(alarm_data)
        logger.info(f"Created {severity} alarm for drone {detection.remote_id}")
        
        # Emit action triggered event
        await self.event_bus.emit(WorkflowEvent(
            event_type=EventType.ACTION_TRIGGERED,
            workflow_id=self.workflow_id,
            node_id=None,
            timestamp=datetime.utcnow(),
            data={
                'action_type': 'alarm',
                'severity': severity,
                'drone_id': detection.remote_id
            }
        ))
    
    async def _log_flight(self, config: Dict, detection: DroneDetection):
        """Log flight data to database"""
        # This would integrate with event storage
        logger.info(f"Logged flight data for {detection.remote_id}")
    
    async def _notify_authorities(self, config: Dict, detection: DroneDetection):
        """Send notification to authorities"""
        authority_contact = config.get('authority_contact', {})
        
        message = f"Drone Detection Alert\n"
        message += f"Remote ID: {detection.remote_id}\n"
        message += f"Location: {detection.latitude}, {detection.longitude}\n"
        message += f"Altitude: {detection.altitude}m\n"
        message += f"Speed: {detection.speed} m/s\n"
        message += f"Violations: {', '.join(detection.geofence_violations)}\n"
        
        logger.info(f"Authority notification: {authority_contact.get('agency', 'Unknown')}")
        # Would integrate with notification system
    
    async def _slew_camera(self, config: Dict, detection: DroneDetection):
        """Command PTZ camera to track drone"""
        camera_id = config.get('camera_id')
        if not camera_id:
            return
        
        logger.info(f"Slewing camera {camera_id} to drone at "
                   f"{detection.latitude}, {detection.longitude}")
        # Would integrate with PTZ camera control system
    
    async def _geofence_alert(self, config: Dict, detection: DroneDetection):
        """Trigger geofence-specific alert"""
        enforcement_level = config.get('enforcement_level', 'warning')
        
        if detection.geofence_violations:
            logger.warning(f"Geofence alert ({enforcement_level}): "
                          f"Drone {detection.remote_id} violated "
                          f"{', '.join(detection.geofence_violations)}")
    
    def _event_to_detection(self, event: Dict) -> DroneDetection:
        """Convert event dict to DroneDetection model"""
        data = event.get('data', {})
        
        # Extract operator location if present
        from models.drone_detection import OperatorLocation
        operator_loc = None
        if data.get('operator', {}).get('location'):
            op_data = data['operator']['location']
            operator_loc = OperatorLocation(
                latitude=op_data['latitude'],
                longitude=op_data['longitude'],
                altitude=op_data.get('altitude')
            )
        
        # Create detection
        detection = DroneDetection(
            remote_id=data.get('remote_id', 'UNKNOWN'),
            mac_address=data.get('mac_address'),
            serial_number=data.get('serial_number'),
            latitude=data.get('position', {}).get('latitude', 0),
            longitude=data.get('position', {}).get('longitude', 0),
            altitude=data.get('position', {}).get('altitude', 0),
            speed=data.get('velocity', {}).get('speed', 0),
            heading=data.get('velocity', {}).get('heading', 0),
            vertical_speed=data.get('velocity', {}).get('vertical_speed', 0),
            operator_location=operator_loc,
            operator_id=data.get('operator', {}).get('operator_id'),
            rssi=data.get('rssi'),
            receiver_id=data.get('receiver_id'),
            timestamp=datetime.fromisoformat(event.get('timestamp', datetime.utcnow().isoformat())),
            track_id=data.get('track_id'),
            geofence_violations=data.get('geofence_violations', [])
        )
        
        return detection
    
    def get_stats(self) -> Dict:
        """Get executor statistics"""
        return {
            "workflow_id": self.workflow_id,
            "running": self.running,
            "execution_count": self.execution_count,
            "tracked_drones": len(self.drone_tracks),
            "node_count": len(self.nodes),
            "input_nodes": len(self.input_nodes)
        }

