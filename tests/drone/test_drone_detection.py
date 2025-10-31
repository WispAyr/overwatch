"""
Unit Tests for Drone Detection
Tests drone data model validation, geofence violation detection, and track correlation
"""
import pytest
from datetime import datetime
from shapely.geometry import Polygon

from backend.models.drone_detection import DroneDetection, OperatorLocation, FlightStatus
from backend.events.drone_manager import DroneEventManager, Geofence


class TestDroneDetection:
    """Tests for DroneDetection model"""
    
    def test_valid_detection(self):
        """Test creating a valid drone detection"""
        detection = DroneDetection(
            remote_id="FA18C52D9C9C1B6E",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10.5,
            heading=45,
            timestamp=datetime.utcnow()
        )
        
        is_valid, error = detection.validate()
        assert is_valid is True
        assert error is None
    
    def test_invalid_latitude(self):
        """Test invalid latitude values"""
        detection = DroneDetection(
            remote_id="TEST",
            latitude=100,  # Invalid: > 90
            longitude=-122.084,
            altitude=100,
            speed=10
        )
        
        is_valid, error = detection.validate()
        assert is_valid is False
        assert "latitude" in error.lower()
    
    def test_invalid_longitude(self):
        """Test invalid longitude values"""
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=200,  # Invalid: > 180
            altitude=100,
            speed=10
        )
        
        is_valid, error = detection.validate()
        assert is_valid is False
        assert "longitude" in error.lower()
    
    def test_invalid_altitude(self):
        """Test invalid altitude values"""
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=15000,  # Invalid: > 10000m
            speed=10
        )
        
        is_valid, error = detection.validate()
        assert is_valid is False
        assert "altitude" in error.lower()
    
    def test_invalid_speed(self):
        """Test invalid speed values"""
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=-5  # Invalid: negative speed
        )
        
        is_valid, error = detection.validate()
        assert is_valid is False
        assert "speed" in error.lower()
    
    def test_missing_remote_id(self):
        """Test detection without Remote ID"""
        detection = DroneDetection(
            remote_id="",  # Invalid: empty
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10
        )
        
        is_valid, error = detection.validate()
        assert is_valid is False
        assert "remote id" in error.lower()
    
    def test_operator_location(self):
        """Test detection with operator location"""
        op_loc = OperatorLocation(
            latitude=37.420,
            longitude=-122.083,
            altitude=10
        )
        
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10,
            operator_location=op_loc
        )
        
        is_valid, error = detection.validate()
        assert is_valid is True
        
        # Test operator location validation
        assert op_loc.validate() is True
    
    def test_invalid_operator_location(self):
        """Test detection with invalid operator location"""
        op_loc = OperatorLocation(
            latitude=100,  # Invalid
            longitude=-122.083,
            altitude=10
        )
        
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10,
            operator_location=op_loc
        )
        
        is_valid, error = detection.validate()
        assert is_valid is False
        assert "operator" in error.lower()
    
    def test_operator_distance_calculation(self):
        """Test distance calculation between drone and operator"""
        op_loc = OperatorLocation(
            latitude=37.420,
            longitude=-122.083
        )
        
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10,
            operator_location=op_loc
        )
        
        distance = detection.calculate_operator_distance()
        assert distance is not None
        assert distance > 0
        # Rough distance should be a few hundred meters
        assert 100 < distance < 500
    
    def test_operator_distance_no_operator(self):
        """Test distance calculation without operator"""
        detection = DroneDetection(
            remote_id="TEST",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10
        )
        
        distance = detection.calculate_operator_distance()
        assert distance is None
    
    def test_to_event_dict(self):
        """Test conversion to event dictionary"""
        detection = DroneDetection(
            remote_id="TEST123",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10.5,
            heading=45,
            vertical_speed=2.0,
            rssi=-75,
            receiver_id="receiver-01"
        )
        
        event = detection.to_event_dict()
        
        assert event['type'] == 'drone_detection'
        assert event['data']['remote_id'] == 'TEST123'
        assert event['data']['position']['latitude'] == 37.422
        assert event['data']['position']['altitude'] == 100
        assert event['data']['velocity']['speed'] == 10.5
        assert event['data']['rssi'] == -75


class TestGeofenceViolation:
    """Tests for geofence violation detection"""
    
    def test_point_in_simple_rectangle(self):
        """Test point-in-polygon for simple rectangle"""
        # Create simple rectangular geofence
        polygon = Polygon([
            (-122.085, 37.420),
            (-122.085, 37.425),
            (-122.080, 37.425),
            (-122.080, 37.420),
            (-122.085, 37.420)
        ])
        
        geofence = Geofence(
            id="test_zone",
            name="Test Zone",
            polygon=polygon,
            altitude_min=0,
            altitude_max=500,
            restriction_type="no-fly",
            enforcement_level="critical_alarm"
        )
        
        # Point inside geofence
        assert geofence.contains_point(37.422, -122.083, 100) is True
        
        # Point outside geofence
        assert geofence.contains_point(37.430, -122.090, 100) is False
    
    def test_altitude_restriction(self):
        """Test altitude-based filtering"""
        polygon = Polygon([
            (-122.085, 37.420),
            (-122.085, 37.425),
            (-122.080, 37.425),
            (-122.080, 37.420)
        ])
        
        geofence = Geofence(
            id="test_zone",
            name="Test Zone",
            polygon=polygon,
            altitude_min=0,
            altitude_max=120,  # FAA hobby limit
            restriction_type="restricted",
            enforcement_level="warning"
        )
        
        # Within polygon and altitude range
        assert geofence.contains_point(37.422, -122.083, 100) is True
        
        # Within polygon but above altitude limit
        assert geofence.contains_point(37.422, -122.083, 200) is False
    
    def test_complex_polygon(self):
        """Test complex polygon boundary"""
        # L-shaped polygon
        polygon = Polygon([
            (-122.085, 37.420),
            (-122.085, 37.425),
            (-122.082, 37.425),
            (-122.082, 37.422),
            (-122.080, 37.422),
            (-122.080, 37.420),
            (-122.085, 37.420)
        ])
        
        geofence = Geofence(
            id="complex_zone",
            name="Complex Zone",
            polygon=polygon,
            altitude_min=0,
            altitude_max=1000,
            restriction_type="no-fly",
            enforcement_level="critical_alarm"
        )
        
        # Point in long part of L
        assert geofence.contains_point(37.423, -122.083, 100) is True
        
        # Point in short part of L
        assert geofence.contains_point(37.421, -122.081, 100) is True
        
        # Point in cutout area
        assert geofence.contains_point(37.421, -122.083, 100) is False


@pytest.mark.asyncio
class TestDroneEventManager:
    """Tests for drone event manager"""
    
    async def test_track_correlation(self):
        """Test correlating multiple detections into tracks"""
        manager = DroneEventManager()
        
        # Create two detections of same drone
        detection1 = DroneDetection(
            remote_id="DRONE123",
            latitude=37.422,
            longitude=-122.084,
            altitude=100,
            speed=10
        )
        
        detection2 = DroneDetection(
            remote_id="DRONE123",
            latitude=37.423,
            longitude=-122.083,
            altitude=105,
            speed=11
        )
        
        # Process detections
        track1 = manager._correlate_track(detection1)
        track2 = manager._correlate_track(detection2)
        
        # Should be same track
        assert track1.remote_id == track2.remote_id
        assert track1.total_detections == 2
        assert len(track1.positions) == 2
    
    async def test_multiple_drones(self):
        """Test tracking multiple drones simultaneously"""
        manager = DroneEventManager()
        
        drone1 = DroneDetection(remote_id="DRONE1", latitude=37.422, longitude=-122.084, altitude=100, speed=10)
        drone2 = DroneDetection(remote_id="DRONE2", latitude=37.420, longitude=-122.082, altitude=80, speed=8)
        
        manager._correlate_track(drone1)
        manager._correlate_track(drone2)
        
        assert len(manager.active_tracks) == 2
        assert "DRONE1" in manager.active_tracks
        assert "DRONE2" in manager.active_tracks

