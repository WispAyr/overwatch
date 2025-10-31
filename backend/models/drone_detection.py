"""
Drone Remote ID Detection Data Model
Defines schema for drone telemetry received from Meshtastic devices
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class FlightStatus(str, Enum):
    """FAA Remote ID flight status codes"""
    UNDECLARED = "undeclared"
    GROUND = "ground"
    AIRBORNE = "airborne"
    EMERGENCY = "emergency"


class AltitudeType(str, Enum):
    """Altitude measurement type"""
    BAROMETRIC = "barometric"
    GEODETIC = "geodetic"


@dataclass
class OperatorLocation:
    """Drone operator position (FAA requirement)"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    timestamp: Optional[datetime] = None

    def validate(self) -> bool:
        """Validate operator coordinates"""
        return (-90 <= self.latitude <= 90 and 
                -180 <= self.longitude <= 180)


@dataclass
class DroneDetection:
    """
    Complete drone Remote ID detection data
    Based on FAA Remote ID requirements and ESP32 Meshtastic format
    """
    # Identification
    remote_id: str  # FAA Remote ID (UAS ID)
    mac_address: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Position data
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0  # meters
    altitude_type: AltitudeType = AltitudeType.BAROMETRIC
    
    # Velocity vectors
    speed: float = 0.0  # m/s
    heading: float = 0.0  # degrees
    vertical_speed: float = 0.0  # m/s
    
    # Operator information
    operator_location: Optional[OperatorLocation] = None
    operator_id: Optional[str] = None
    
    # Signal/Detection metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    rssi: Optional[int] = None  # Signal strength in dBm
    receiver_id: Optional[str] = None  # Meshtastic device that detected
    
    # Flight status
    flight_status: FlightStatus = FlightStatus.UNDECLARED
    height_above_ground: Optional[float] = None  # meters
    
    # Track metadata (populated by drone manager)
    track_id: Optional[str] = None
    geofence_violations: list[str] = field(default_factory=list)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate detection data against FAA requirements and physical bounds
        Returns (is_valid, error_message)
        """
        # Coordinate validation
        if not (-90 <= self.latitude <= 90):
            return False, f"Invalid latitude: {self.latitude}"
        if not (-180 <= self.longitude <= 180):
            return False, f"Invalid longitude: {self.longitude}"
        
        # Altitude validation (reasonable flight range)
        if not (-100 <= self.altitude <= 10000):
            return False, f"Invalid altitude: {self.altitude}m"
        
        # Speed validation (max ~300 m/s for typical drones)
        if self.speed < 0 or self.speed > 300:
            return False, f"Invalid speed: {self.speed} m/s"
        
        # Heading validation
        if not (0 <= self.heading <= 360):
            return False, f"Invalid heading: {self.heading}"
        
        # Required FAA Remote ID field
        if not self.remote_id:
            return False, "Missing required Remote ID"
        
        # Operator location validation if present
        if self.operator_location and not self.operator_location.validate():
            return False, "Invalid operator location coordinates"
        
        return True, None
    
    def to_event_dict(self) -> Dict[str, Any]:
        """
        Convert to canonical event schema for storage/WebSocket
        Compatible with backend/events/storage.py format
        """
        return {
            "type": "drone_detection",
            "timestamp": self.timestamp.isoformat(),
            "data": {
                # Identification
                "remote_id": self.remote_id,
                "mac_address": self.mac_address,
                "serial_number": self.serial_number,
                
                # Position
                "position": {
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "altitude": self.altitude,
                    "altitude_type": self.altitude_type.value
                },
                
                # Velocity
                "velocity": {
                    "speed": self.speed,
                    "heading": self.heading,
                    "vertical_speed": self.vertical_speed
                },
                
                # Operator
                "operator": {
                    "location": {
                        "latitude": self.operator_location.latitude,
                        "longitude": self.operator_location.longitude,
                        "altitude": self.operator_location.altitude
                    } if self.operator_location else None,
                    "operator_id": self.operator_id
                },
                
                # Metadata
                "flight_status": self.flight_status.value,
                "height_above_ground": self.height_above_ground,
                "rssi": self.rssi,
                "receiver_id": self.receiver_id,
                
                # Track correlation
                "track_id": self.track_id,
                "geofence_violations": self.geofence_violations
            }
        }
    
    @classmethod
    def from_meshtastic_message(cls, msg: Dict[str, Any], receiver_id: str) -> 'DroneDetection':
        """
        Parse Meshtastic protobuf message into DroneDetection
        Handles various Remote ID message formats
        """
        # Extract Remote ID data from Meshtastic packet
        payload = msg.get('decoded', {})
        drone_data = payload.get('droneId', {})
        
        # Create detection object
        detection = cls(
            remote_id=drone_data.get('id_or_mac', 'UNKNOWN'),
            mac_address=drone_data.get('mac'),
            serial_number=drone_data.get('serial'),
            latitude=drone_data.get('lat', 0.0),
            longitude=drone_data.get('lon', 0.0),
            altitude=drone_data.get('altitude', 0.0),
            speed=drone_data.get('speed', 0.0),
            heading=drone_data.get('heading', 0.0),
            vertical_speed=drone_data.get('vert_speed', 0.0),
            rssi=msg.get('rxRssi'),
            receiver_id=receiver_id,
            timestamp=datetime.fromtimestamp(msg.get('rxTime', datetime.utcnow().timestamp()))
        )
        
        # Parse operator location if present
        if 'operator_lat' in drone_data and 'operator_lon' in drone_data:
            detection.operator_location = OperatorLocation(
                latitude=drone_data['operator_lat'],
                longitude=drone_data['operator_lon'],
                altitude=drone_data.get('operator_alt')
            )
        
        # Parse flight status
        status_code = drone_data.get('status', 0)
        status_map = {0: FlightStatus.UNDECLARED, 1: FlightStatus.GROUND, 
                     2: FlightStatus.AIRBORNE, 3: FlightStatus.EMERGENCY}
        detection.flight_status = status_map.get(status_code, FlightStatus.UNDECLARED)
        
        return detection
    
    def calculate_operator_distance(self) -> Optional[float]:
        """
        Calculate distance between drone and operator in meters
        Returns None if operator location unavailable
        """
        if not self.operator_location:
            return None
        
        from math import radians, sin, cos, sqrt, atan2
        
        # Haversine formula
        R = 6371000  # Earth radius in meters
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(self.operator_location.latitude), radians(self.operator_location.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

