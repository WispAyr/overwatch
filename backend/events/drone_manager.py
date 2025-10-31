"""
Drone Event Manager
Specialized event manager for drone detection with track correlation and geofence checking
"""
import asyncio
import logging
import yaml
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from shapely.geometry import Point, Polygon

from models.drone_detection import DroneDetection
from events.storage import EventStorage

logger = logging.getLogger(__name__)


@dataclass
class Geofence:
    """Airspace restriction zone definition"""
    id: str
    name: str
    polygon: Polygon
    altitude_min: float  # meters
    altitude_max: float  # meters
    restriction_type: str  # no-fly, restricted, warning, monitoring
    enforcement_level: str  # log_only, warning, critical_alarm
    active_hours: Optional[List[tuple[int, int]]] = None  # [(start_hour, end_hour)]
    temporary_start: Optional[datetime] = None
    temporary_end: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Check if geofence is currently active based on time restrictions"""
        now = datetime.utcnow()
        
        # Check temporary restrictions
        if self.temporary_start and now < self.temporary_start:
            return False
        if self.temporary_end and now > self.temporary_end:
            return False
        
        # Check active hours
        if self.active_hours:
            current_hour = now.hour
            return any(start <= current_hour < end for start, end in self.active_hours)
        
        return True
    
    def contains_point(self, lat: float, lon: float, altitude: float) -> bool:
        """Check if position violates geofence"""
        if not self.is_active():
            return False
        
        # Check altitude bounds
        if not (self.altitude_min <= altitude <= self.altitude_max):
            return False
        
        # Check polygon boundary
        point = Point(lon, lat)
        return self.polygon.contains(point)


@dataclass
class DroneTrack:
    """Historical track for a single drone"""
    remote_id: str
    first_seen: datetime
    last_seen: datetime
    positions: List[DroneDetection] = field(default_factory=list)
    geofence_violations: Set[str] = field(default_factory=set)
    total_detections: int = 0
    
    def add_detection(self, detection: DroneDetection):
        """Add new detection to track"""
        self.positions.append(detection)
        self.last_seen = detection.timestamp
        self.total_detections += 1
        
        # Keep only recent positions (last 1000 or 1 hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.positions = [p for p in self.positions if p.timestamp > cutoff_time][-1000:]
    
    def get_flight_path(self) -> List[Dict]:
        """Get simplified flight path for visualization"""
        return [
            {
                "lat": p.latitude,
                "lon": p.longitude,
                "alt": p.altitude,
                "timestamp": p.timestamp.isoformat(),
                "speed": p.speed
            }
            for p in self.positions
        ]


class DroneEventManager:
    """
    Manages drone detection events with track correlation and geofence checking
    Extends base event manager functionality for drone-specific processing
    """
    
    def __init__(self, config_path: str = "config/geofences.yaml", event_storage: Optional[EventStorage] = None):
        self.config_path = Path(config_path)
        self.geofences: Dict[str, Geofence] = {}
        self.active_tracks: Dict[str, DroneTrack] = {}  # remote_id -> track
        self.event_callbacks: List = []
        self.event_storage = event_storage
        
        # Track management settings
        self.track_timeout = timedelta(minutes=10)  # Remove inactive tracks
        self.cleanup_interval = 60  # seconds
        
    async def initialize(self):
        """Load geofence configurations and initialize storage"""
        logger.info(f"Initializing drone event manager from {self.config_path}")
        
        # Initialize event storage if not provided
        if self.event_storage is None:
            self.event_storage = EventStorage()
            await self.event_storage.initialize()
        
        if not self.config_path.exists():
            logger.warning(f"Geofence config {self.config_path} not found")
            return
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load geofences
        for gf_config in config.get('geofences', []):
            geofence = self._parse_geofence(gf_config)
            self.geofences[geofence.id] = geofence
            logger.info(f"Loaded geofence: {geofence.name} ({geofence.restriction_type})")
        
        logger.info(f"Loaded {len(self.geofences)} geofences")
    
    def _parse_geofence(self, config: Dict) -> Geofence:
        """Parse geofence configuration into Geofence object"""
        # Convert coordinate list to Shapely polygon
        coords = config['polygon']
        polygon = Polygon([(lon, lat) for lat, lon in coords])
        
        # Parse active hours if present
        active_hours = None
        if 'active_hours' in config:
            active_hours = [
                (int(h.split('-')[0]), int(h.split('-')[1]))
                for h in config['active_hours']
            ]
        
        # Parse temporary restrictions
        temp_start = None
        temp_end = None
        if 'temporary_start' in config:
            # Handle ISO format with 'Z' suffix
            ts = config['temporary_start'].replace('Z', '+00:00')
            temp_start = datetime.fromisoformat(ts)
        if 'temporary_end' in config:
            # Handle ISO format with 'Z' suffix
            ts = config['temporary_end'].replace('Z', '+00:00')
            temp_end = datetime.fromisoformat(ts)
        
        return Geofence(
            id=config['id'],
            name=config['name'],
            polygon=polygon,
            altitude_min=config.get('altitude_min', 0),
            altitude_max=config.get('altitude_max', 10000),
            restriction_type=config.get('restriction_type', 'monitoring'),
            enforcement_level=config.get('enforcement_level', 'log_only'),
            active_hours=active_hours,
            temporary_start=temp_start,
            temporary_end=temp_end
        )
    
    async def process_detection(self, detection: DroneDetection) -> DroneDetection:
        """
        Process drone detection: correlate tracks, check geofences, enrich data
        Returns enriched detection ready for WebSocket broadcast
        """
        # Track correlation
        track = self._correlate_track(detection)
        detection.track_id = track.remote_id
        
        # Geofence violation detection
        violations = self._check_geofences(detection)
        detection.geofence_violations = list(violations)
        
        # Update track with violations
        track.geofence_violations.update(violations)
        
        # Publish enriched detection
        await self._publish_event(detection)
        
        return detection
    
    def _correlate_track(self, detection: DroneDetection) -> DroneTrack:
        """
        Associate detection with existing track or create new one
        Uses Remote ID for correlation
        """
        remote_id = detection.remote_id
        
        if remote_id in self.active_tracks:
            track = self.active_tracks[remote_id]
        else:
            # Create new track
            track = DroneTrack(
                remote_id=remote_id,
                first_seen=detection.timestamp,
                last_seen=detection.timestamp
            )
            self.active_tracks[remote_id] = track
            logger.info(f"New drone track: {remote_id}")
        
        track.add_detection(detection)
        return track
    
    def _check_geofences(self, detection: DroneDetection) -> Set[str]:
        """
        Check if drone position violates any geofences
        Returns set of violated geofence IDs
        """
        violations = set()
        
        for gf_id, geofence in self.geofences.items():
            if geofence.contains_point(
                detection.latitude,
                detection.longitude,
                detection.altitude
            ):
                violations.add(gf_id)
                logger.warning(
                    f"Geofence violation: {detection.remote_id} in {geofence.name} "
                    f"({geofence.enforcement_level})"
                )
        
        return violations
    
    async def _publish_event(self, detection: DroneDetection):
        """Publish enriched detection to event callbacks (WebSocket, storage)"""
        event_data = detection.to_event_dict()
        
        # Store to persistent storage
        if self.event_storage:
            try:
                storage_event = {
                    'id': str(uuid.uuid4()),
                    'tenant': event_data.get('tenant'),
                    'site': event_data.get('site'),
                    'source': {
                        'type': 'drone_detection',
                        'subtype': 'remote_id',
                        'device_id': detection.receiver_id,
                        'vendor': 'meshtastic',
                        'model': 'esp32'
                    },
                    'observed': detection.timestamp.isoformat(),
                    'ingested': datetime.utcnow().isoformat(),
                    'location': {
                        'lat': detection.latitude,
                        'lon': detection.longitude,
                        'floor': None,
                        'area_id': None
                    },
                    'attributes': {
                        'remote_id': detection.remote_id,
                        'altitude': detection.altitude,
                        'speed': detection.speed,
                        'heading': detection.heading,
                        'vertical_speed': detection.vertical_speed,
                        'rssi': detection.rssi,
                        'geofence_violations': detection.geofence_violations,
                        'operator_id': detection.operator_id,
                        'operator_location': {
                            'latitude': detection.operator_location.latitude,
                            'longitude': detection.operator_location.longitude,
                            'altitude': detection.operator_location.altitude
                        } if detection.operator_location else None
                    },
                    'severity': 'critical' if detection.geofence_violations else 'info',
                    'tags': ['drone', 'aerial'] + (['violation'] if detection.geofence_violations else [])
                }
                
                await self.event_storage.store_event(storage_event)
            except Exception as e:
                logger.error(f"Error storing drone event: {e}", exc_info=True)
        
        # Publish to callbacks (WebSocket, etc.)
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    callback(event_data)
            except Exception as e:
                logger.error(f"Error in drone event callback: {e}", exc_info=True)
    
    def register_callback(self, callback):
        """Register callback for enriched drone events"""
        self.event_callbacks.append(callback)
    
    async def cleanup_inactive_tracks(self):
        """Remove tracks that haven't been updated recently"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            
            cutoff = datetime.utcnow() - self.track_timeout
            inactive = [
                remote_id for remote_id, track in self.active_tracks.items()
                if track.last_seen < cutoff
            ]
            
            for remote_id in inactive:
                del self.active_tracks[remote_id]
                logger.info(f"Removed inactive track: {remote_id}")
    
    def get_active_drones(self) -> List[Dict]:
        """Get all currently tracked drones for API"""
        return [
            {
                "remote_id": track.remote_id,
                "first_seen": track.first_seen.isoformat(),
                "last_seen": track.last_seen.isoformat(),
                "total_detections": track.total_detections,
                "geofence_violations": list(track.geofence_violations),
                "current_position": self._normalize_position(track.positions[-1]) if track.positions else None,
                "flight_path_length": len(track.positions)
            }
            for track in self.active_tracks.values()
        ]
    
    def _normalize_position(self, detection) -> Dict:
        """Normalize detection to lightweight position object"""
        return {
            "latitude": detection.latitude,
            "longitude": detection.longitude,
            "altitude": detection.altitude,
            "speed": detection.speed,
            "heading": detection.heading,
            "timestamp": detection.timestamp.isoformat(),
            "rssi": detection.rssi
        }
    
    async def get_drone_history(self, remote_id: str) -> Optional[Dict]:
        """Get flight history for specific drone (from memory or storage)"""
        track = self.active_tracks.get(remote_id)
        
        # If in active memory, return current track
        if track:
            return {
                "remote_id": track.remote_id,
                "first_seen": track.first_seen.isoformat(),
                "last_seen": track.last_seen.isoformat(),
                "total_detections": track.total_detections,
                "geofence_violations": list(track.geofence_violations),
                "flight_path": track.get_flight_path()
            }
        
        # Otherwise, try to retrieve from persistent storage
        if self.event_storage:
            try:
                # Query events from storage for this drone
                events = await self.event_storage.query_events(
                    source_type='drone_detection',
                    limit=1000
                )
                
                # Filter events for this specific drone
                drone_events = [
                    e for e in events 
                    if e.get('attributes', {}).get('remote_id') == remote_id
                ]
                
                if not drone_events:
                    return None
                
                # Build flight path from stored events
                flight_path = [
                    {
                        'lat': e.get('location', {}).get('lat'),
                        'lon': e.get('location', {}).get('lon'),
                        'alt': e.get('attributes', {}).get('altitude'),
                        'timestamp': e.get('observed'),
                        'speed': e.get('attributes', {}).get('speed')
                    }
                    for e in sorted(drone_events, key=lambda x: x.get('observed', ''))
                ]
                
                # Collect geofence violations
                violations = set()
                for e in drone_events:
                    violations.update(e.get('attributes', {}).get('geofence_violations', []))
                
                return {
                    "remote_id": remote_id,
                    "first_seen": drone_events[0].get('observed') if drone_events else None,
                    "last_seen": drone_events[-1].get('observed') if drone_events else None,
                    "total_detections": len(drone_events),
                    "geofence_violations": list(violations),
                    "flight_path": flight_path,
                    "from_storage": True
                }
            except Exception as e:
                logger.error(f"Error retrieving drone history from storage: {e}", exc_info=True)
        
        return None
    
    def get_geofences(self) -> List[Dict]:
        """Get all geofence definitions for API"""
        return [
            {
                "id": gf.id,
                "name": gf.name,
                "polygon": [[coord[1], coord[0]] for coord in gf.polygon.exterior.coords],
                "altitude_min": gf.altitude_min,
                "altitude_max": gf.altitude_max,
                "restriction_type": gf.restriction_type,
                "enforcement_level": gf.enforcement_level,
                "is_active": gf.is_active()
            }
            for gf in self.geofences.values()
        ]
    
    def add_geofence(self, config: Dict) -> Geofence:
        """Add new geofence (for POST API endpoint)"""
        geofence = self._parse_geofence(config)
        self.geofences[geofence.id] = geofence
        logger.info(f"Added geofence: {geofence.name}")
        return geofence

