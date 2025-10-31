"""
Meshtastic Interface Manager
Handles serial communication with ESP32 drone detection hardware
"""
import asyncio
import logging
import serial
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MeshtasticDevice:
    """Meshtastic receiver configuration"""
    id: str
    name: str
    port: str  # /dev/ttyUSB0 or COM3
    baud_rate: int = 115200
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coverage_radius: Optional[float] = None  # meters
    min_rssi: int = -120  # dBm threshold
    enabled: bool = True
    
    # Connection state
    connected: bool = False
    last_detection: Optional[datetime] = None
    detection_count: int = 0


class MeshtasticManager:
    """
    Manages multiple Meshtastic devices for distributed drone detection
    Handles serial communication, message parsing, and event publishing
    """
    
    def __init__(self, config_path: str = "config/meshtastic.yaml"):
        self.config_path = Path(config_path)
        self.devices: Dict[str, MeshtasticDevice] = {}
        self.connections: Dict[str, serial.Serial] = {}
        self.running = False
        self.event_callbacks: List[Callable] = []
        
        # Duplicate detection
        self.recent_detections: Dict[str, datetime] = {}
        self.duplicate_window = 2.0  # seconds
        
    async def initialize(self):
        """Load configuration and establish connections"""
        logger.info(f"Initializing Meshtastic manager from {self.config_path}")
        
        if not self.config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load device configurations
        for device_config in config.get('devices', []):
            device = MeshtasticDevice(**device_config)
            self.devices[device.id] = device
            logger.info(f"Configured Meshtastic device: {device.name} on {device.port}")
        
        # Set duplicate detection window if configured
        self.duplicate_window = config.get('duplicate_window', 2.0)
        
    async def start(self):
        """Start all device connections and listening tasks"""
        self.running = True
        
        tasks = []
        for device_id, device in self.devices.items():
            if device.enabled:
                task = asyncio.create_task(self._connect_and_listen(device))
                tasks.append(task)
        
        logger.info(f"Started {len(tasks)} Meshtastic receiver tasks")
        
        # Run all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Gracefully shutdown all connections"""
        self.running = False
        
        for device_id, conn in self.connections.items():
            try:
                conn.close()
                logger.info(f"Closed connection to {device_id}")
            except Exception as e:
                logger.error(f"Error closing {device_id}: {e}")
        
        self.connections.clear()
    
    async def _connect_and_listen(self, device: MeshtasticDevice):
        """
        Establish serial or TCP connection and continuously read messages
        Handles reconnection on failure
        """
        # Check if TCP connection
        if device.port.startswith('tcp://'):
            await self._connect_and_listen_tcp(device)
            return
        
        # Serial connection
        while self.running:
            try:
                # Attempt connection
                logger.info(f"Connecting to {device.name} on {device.port}")
                conn = serial.Serial(
                    port=device.port,
                    baudrate=device.baud_rate,
                    timeout=1.0
                )
                
                self.connections[device.id] = conn
                device.connected = True
                logger.info(f"Connected to {device.name}")
                
                # Read messages continuously
                while self.running and conn.is_open:
                    try:
                        if conn.in_waiting > 0:
                            # Read message (assumes line-delimited JSON or protobuf)
                            await self._read_message(device, conn)
                        else:
                            await asyncio.sleep(0.01)  # Prevent busy waiting
                    
                    except Exception as e:
                        logger.error(f"Error reading from {device.name}: {e}")
                        break
                
            except serial.SerialException as e:
                logger.error(f"Serial connection error for {device.name}: {e}")
                device.connected = False
                
                # Wait before reconnecting
                if self.running:
                    logger.info(f"Reconnecting to {device.name} in 5 seconds...")
                    await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Unexpected error for {device.name}: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _connect_and_listen_tcp(self, device: MeshtasticDevice):
        """
        Establish TCP connection and continuously read messages
        Handles reconnection on failure
        """
        # Parse TCP URL: tcp://host:port
        tcp_url = device.port.replace('tcp://', '')
        host, port_str = tcp_url.split(':')
        port = int(port_str)
        
        while self.running:
            try:
                # Attempt TCP connection
                logger.info(f"Connecting to {device.name} at {host}:{port}")
                reader, writer = await asyncio.open_connection(host, port)
                
                device.connected = True
                logger.info(f"Connected to {device.name} via TCP")
                
                # Read messages continuously
                while self.running:
                    try:
                        await self._read_message_tcp(device, reader)
                    except Exception as e:
                        logger.error(f"Error reading from {device.name}: {e}")
                        break
                
                # Close writer
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                logger.error(f"TCP connection error for {device.name}: {e}")
                device.connected = False
                
                # Wait before reconnecting
                if self.running:
                    logger.info(f"Reconnecting to {device.name} in 5 seconds...")
                    await asyncio.sleep(5)
    
    async def _read_message(self, device: MeshtasticDevice, conn: serial.Serial):
        """
        Read and parse a single Meshtastic message from serial connection
        Supports both JSON and protobuf formats
        """
        try:
            # Try reading line-delimited data first
            line = conn.readline().decode('utf-8', errors='ignore').strip()
            
            if not line:
                return
            
            await self._process_message_line(device, line)
        
        except Exception as e:
            logger.error(f"Error parsing message from {device.name}: {e}", exc_info=True)
    
    async def _read_message_tcp(self, device: MeshtasticDevice, reader: asyncio.StreamReader):
        """
        Read and parse a single Meshtastic message from TCP connection
        Supports both JSON and protobuf formats
        """
        try:
            # Read line-delimited data
            line_bytes = await reader.readline()
            
            if not line_bytes:
                return
            
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            
            if not line:
                return
            
            await self._process_message_line(device, line)
        
        except Exception as e:
            logger.error(f"Error parsing TCP message from {device.name}: {e}", exc_info=True)
    
    async def _process_message_line(self, device: MeshtasticDevice, line: str):
        """
        Process a message line (common logic for serial and TCP)
        """
        # Attempt JSON parsing (some Meshtastic firmwares output JSON)
        import json
        try:
            msg_data = json.loads(line)
        except json.JSONDecodeError:
            # If not JSON, might be protobuf - handle separately
            logger.debug(f"Non-JSON message from {device.name}, skipping")
            return
        
        # Check if message contains drone Remote ID data
        if not self._is_drone_message(msg_data):
            return
        
        # Check RSSI threshold
        rssi = msg_data.get('rxRssi', -999)
        if rssi < device.min_rssi:
            logger.debug(f"Weak signal ({rssi} dBm) from {device.name}, filtering")
            return
        
        # Duplicate detection
        remote_id = msg_data.get('decoded', {}).get('droneId', {}).get('id_or_mac')
        if remote_id and self._is_duplicate(remote_id):
            logger.debug(f"Duplicate detection of {remote_id}, filtering")
            return
        
        # Parse into DroneDetection model
        from models.drone_detection import DroneDetection
        detection = DroneDetection.from_meshtastic_message(msg_data, device.id)
        
        # Validate
        is_valid, error = detection.validate()
        if not is_valid:
            logger.warning(f"Invalid detection from {device.name}: {error}")
            return
        
        # Update device stats
        device.last_detection = datetime.utcnow()
        device.detection_count += 1
        
        # Publish to event system
        await self._publish_detection(detection)
        
        logger.info(f"Drone detected: {detection.remote_id} by {device.name}")
    
    def _is_drone_message(self, msg: Dict) -> bool:
        """Check if message contains drone Remote ID data"""
        decoded = msg.get('decoded', {})
        return 'droneId' in decoded or 'drone_id' in decoded
    
    def _is_duplicate(self, remote_id: str) -> bool:
        """
        Check if detection is duplicate within time window
        Multiple receivers may detect same drone simultaneously
        """
        now = datetime.utcnow()
        
        if remote_id in self.recent_detections:
            time_diff = (now - self.recent_detections[remote_id]).total_seconds()
            if time_diff < self.duplicate_window:
                return True
        
        # Update recent detections
        self.recent_detections[remote_id] = now
        
        # Cleanup old entries (keep last 1000)
        if len(self.recent_detections) > 1000:
            sorted_items = sorted(self.recent_detections.items(), key=lambda x: x[1])
            self.recent_detections = dict(sorted_items[-1000:])
        
        return False
    
    async def _publish_detection(self, detection):
        """
        Publish detection to registered event callbacks
        Used by drone_manager to inject into event system
        """
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(detection)
                else:
                    callback(detection)
            except Exception as e:
                logger.error(f"Error in event callback: {e}", exc_info=True)
    
    def register_callback(self, callback: Callable):
        """Register callback for drone detection events"""
        self.event_callbacks.append(callback)
        logger.info(f"Registered drone detection callback: {callback.__name__}")
    
    def get_device_status(self) -> List[Dict]:
        """Get status of all configured devices for API"""
        return [
            {
                "id": device.id,
                "name": device.name,
                "port": device.port,
                "connected": device.connected,
                "enabled": device.enabled,
                "location": {
                    "latitude": device.latitude,
                    "longitude": device.longitude,
                    "coverage_radius": device.coverage_radius
                } if device.latitude else None,
                "stats": {
                    "detection_count": device.detection_count,
                    "last_detection": device.last_detection.isoformat() if device.last_detection else None
                }
            }
            for device in self.devices.values()
        ]
    
    def get_device(self, device_id: str) -> Optional[MeshtasticDevice]:
        """Get device by ID"""
        return self.devices.get(device_id)

