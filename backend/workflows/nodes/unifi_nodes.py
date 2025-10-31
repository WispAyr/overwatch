"""
UniFi Workflow Nodes
Nodes for integrating UniFi data into workflows
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger('overwatch.workflows.nodes.unifi')


class UniFiCameraDiscoveryNode:
    """
    Discovers and lists UniFi Protect cameras
    Outputs camera list that can be used by other nodes
    """
    
    def __init__(self, node_id: str, config: Dict):
        self.node_id = node_id
        self.config = config
        self.credential_id = config.get('credentialId')
        self.filter_state = config.get('filterState')  # 'connected', 'disconnected', 'all'
        self.filter_recording = config.get('filterRecording')  # True, False, None
        
    async def execute(self, input_data: Dict, unifi_manager) -> Dict:
        """
        Execute camera discovery
        
        Args:
            input_data: Input from previous node
            unifi_manager: UniFiCredentialManager instance
            
        Returns:
            Output data with camera list
        """
        if not self.credential_id:
            return {
                "success": False,
                "error": "No credential ID configured"
            }
            
        # Get Protect client
        protect_client = unifi_manager.get_protect_client(self.credential_id)
        if not protect_client:
            return {
                "success": False,
                "error": "Failed to create Protect client"
            }
            
        try:
            async with protect_client:
                cameras = await protect_client.get_cameras()
                
                # Apply filters
                filtered = cameras
                
                if self.filter_state == 'connected':
                    filtered = [c for c in filtered if c.get('isConnected')]
                elif self.filter_state == 'disconnected':
                    filtered = [c for c in filtered if not c.get('isConnected')]
                    
                if self.filter_recording is not None:
                    filtered = [c for c in filtered if c.get('isRecording') == self.filter_recording]
                
                # Build output
                output_cameras = []
                for camera in filtered:
                    output_cameras.append({
                        'id': camera.get('id'),
                        'name': camera.get('name'),
                        'model': camera.get('type'),
                        'mac': camera.get('mac'),
                        'host': camera.get('host'),
                        'state': camera.get('state'),
                        'isConnected': camera.get('isConnected', False),
                        'isRecording': camera.get('isRecording', False),
                        'rtsp_urls': {
                            'high': protect_client.get_rtsp_url(camera, 0),
                            'medium': protect_client.get_rtsp_url(camera, 1),
                            'low': protect_client.get_rtsp_url(camera, 2)
                        }
                    })
                
                return {
                    "success": True,
                    "cameras": output_cameras,
                    "count": len(output_cameras),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"UniFi camera discovery error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class UniFiProtectEventNode:
    """
    Listens for UniFi Protect events (motion, smart detections)
    Triggers downstream nodes when events occur
    """
    
    def __init__(self, node_id: str, config: Dict):
        self.node_id = node_id
        self.config = config
        self.credential_id = config.get('credentialId')
        self.event_types = config.get('eventTypes', ['motion'])  # motion, smart, ring
        self.camera_filter = config.get('cameraFilter', [])  # List of camera IDs or names
        self.detection_types = config.get('detectionTypes', [])  # person, vehicle, animal
        self.poll_interval = config.get('pollInterval', 10)  # seconds
        self.last_check = None
        
    async def execute(self, input_data: Dict, unifi_manager) -> Dict:
        """
        Check for new events
        
        Args:
            input_data: Input from previous node
            unifi_manager: UniFiCredentialManager instance
            
        Returns:
            Events that occurred since last check
        """
        if not self.credential_id:
            return {
                "success": False,
                "error": "No credential ID configured"
            }
            
        protect_client = unifi_manager.get_protect_client(self.credential_id)
        if not protect_client:
            return {
                "success": False,
                "error": "Failed to create Protect client"
            }
            
        try:
            async with protect_client:
                events = []
                
                # Get events based on type
                if 'motion' in self.event_types:
                    motion_events = await protect_client.get_motion_events(limit=50)
                    events.extend(motion_events)
                    
                if 'smart' in self.event_types:
                    smart_events = await protect_client.get_smart_detections(limit=50)
                    events.extend(smart_events)
                
                # Filter by camera if specified
                if self.camera_filter:
                    events = [
                        e for e in events
                        if e.get('camera') in self.camera_filter or
                        any(e.get('cameraName', '').lower() == name.lower() 
                            for name in self.camera_filter)
                    ]
                
                # Filter by detection type for smart events
                if self.detection_types:
                    events = [
                        e for e in events
                        if any(dt in e.get('smartDetectTypes', []) 
                               for dt in self.detection_types)
                    ]
                
                # Filter by time if we have a last check time
                if self.last_check:
                    events = [
                        e for e in events
                        if e.get('start', 0) > self.last_check
                    ]
                
                self.last_check = datetime.utcnow().timestamp() * 1000
                
                return {
                    "success": True,
                    "events": events,
                    "count": len(events),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"UniFi event check error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class UniFiDeviceStatusNode:
    """
    Monitors UniFi device status (APs, switches, etc)
    """
    
    def __init__(self, node_id: str, config: Dict):
        self.node_id = node_id
        self.config = config
        self.credential_id = config.get('credentialId')
        self.device_types = config.get('deviceTypes', [])  # uap, usw, ugw, etc
        self.check_offline = config.get('checkOffline', False)
        
    async def execute(self, input_data: Dict, unifi_manager) -> Dict:
        """
        Get device status
        
        Args:
            input_data: Input from previous node
            unifi_manager: UniFiCredentialManager instance
            
        Returns:
            Device status information
        """
        if not self.credential_id:
            return {
                "success": False,
                "error": "No credential ID configured"
            }
            
        client = unifi_manager.get_client(self.credential_id)
        if not client:
            return {
                "success": False,
                "error": "Failed to create UniFi client"
            }
            
        try:
            async with client:
                devices = await client.get_devices()
                
                # Filter by device type
                if self.device_types:
                    devices = [d for d in devices if d.get('type') in self.device_types]
                
                # Build output
                device_list = []
                offline_devices = []
                
                for device in devices:
                    device_info = {
                        'mac': device.get('mac'),
                        'name': device.get('name'),
                        'model': device.get('model'),
                        'type': device.get('type'),
                        'state': device.get('state'),
                        'ip': device.get('ip'),
                        'uptime': device.get('uptime'),
                        'version': device.get('version')
                    }
                    
                    device_list.append(device_info)
                    
                    if device.get('state') == 0:  # Offline
                        offline_devices.append(device_info)
                
                result = {
                    "success": True,
                    "devices": device_list,
                    "total_count": len(device_list),
                    "offline_count": len(offline_devices),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if self.check_offline and offline_devices:
                    result["offline_devices"] = offline_devices
                    result["alert"] = f"{len(offline_devices)} devices offline"
                
                return result
                
        except Exception as e:
            logger.error(f"UniFi device status error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class UniFiClientDetectionNode:
    """
    Detects network clients (devices connected to WiFi/network)
    Useful for presence detection, device tracking
    """
    
    def __init__(self, node_id: str, config: Dict):
        self.node_id = node_id
        self.config = config
        self.credential_id = config.get('credentialId')
        self.mac_filter = config.get('macFilter', [])  # Specific MACs to watch
        self.hostname_filter = config.get('hostnameFilter', [])  # Hostnames to watch
        self.active_only = config.get('activeOnly', True)
        
    async def execute(self, input_data: Dict, unifi_manager) -> Dict:
        """
        Get network clients
        
        Args:
            input_data: Input from previous node
            unifi_manager: UniFiCredentialManager instance
            
        Returns:
            Client information
        """
        if not self.credential_id:
            return {
                "success": False,
                "error": "No credential ID configured"
            }
            
        client = unifi_manager.get_client(self.credential_id)
        if not client:
            return {
                "success": False,
                "error": "Failed to create UniFi client"
            }
            
        try:
            async with client:
                clients = await client.get_clients(active_only=self.active_only)
                
                # Apply filters
                if self.mac_filter:
                    clients = [c for c in clients if c.get('mac') in self.mac_filter]
                    
                if self.hostname_filter:
                    clients = [
                        c for c in clients 
                        if any(h.lower() in c.get('hostname', '').lower() 
                               for h in self.hostname_filter)
                    ]
                
                # Build output
                client_list = []
                for cl in clients:
                    client_list.append({
                        'mac': cl.get('mac'),
                        'hostname': cl.get('hostname'),
                        'name': cl.get('name'),
                        'ip': cl.get('ip'),
                        'essid': cl.get('essid'),  # WiFi network name
                        'signal': cl.get('signal'),
                        'uptime': cl.get('uptime'),
                        'last_seen': cl.get('last_seen')
                    })
                
                return {
                    "success": True,
                    "clients": client_list,
                    "count": len(client_list),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"UniFi client detection error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class UniFiAddCameraNode:
    """
    Automatically adds discovered UniFi cameras to Overwatch
    """
    
    def __init__(self, node_id: str, config: Dict):
        self.node_id = node_id
        self.config = config
        self.sublocation_id = config.get('sublocationId')  # Where to add cameras
        self.stream_quality = config.get('streamQuality', 'medium')  # high, medium, low
        self.auto_enable = config.get('autoEnable', True)
        
    async def execute(self, input_data: Dict, db_session) -> Dict:
        """
        Add cameras to Overwatch from discovery data
        
        Args:
            input_data: Must contain 'cameras' from discovery node
            db_session: Database session
            
        Returns:
            Result of camera addition
        """
        from core.database import Camera
        
        cameras = input_data.get('cameras', [])
        if not cameras:
            return {
                "success": False,
                "error": "No cameras in input data"
            }
            
        if not self.sublocation_id:
            return {
                "success": False,
                "error": "No sublocation ID configured"
            }
            
        added = []
        skipped = []
        
        for camera in cameras:
            camera_id = f"unifi_{camera.get('mac', camera.get('id'))}"
            
            # Check if camera already exists
            existing = db_session.query(Camera).filter(Camera.id == camera_id).first()
            if existing:
                skipped.append(camera.get('name'))
                continue
            
            # Get RTSP URL for selected quality
            rtsp_url = camera.get('rtsp_urls', {}).get(self.stream_quality)
            if not rtsp_url:
                continue
            
            # Create camera entry
            new_camera = Camera(
                id=camera_id,
                sublocation_id=self.sublocation_id,
                name=camera.get('name', f"UniFi Camera {camera.get('id')}"),
                type='unifi',
                sensor_type='camera',
                rtsp_url=rtsp_url,
                streams=camera.get('rtsp_urls'),
                active_stream=self.stream_quality,
                enabled=1 if self.auto_enable else 0,
                workflows=[],
                settings={
                    'unifi_id': camera.get('id'),
                    'unifi_mac': camera.get('mac'),
                    'unifi_model': camera.get('model')
                }
            )
            
            db_session.add(new_camera)
            added.append(camera.get('name'))
        
        if added:
            db_session.commit()
        
        return {
            "success": True,
            "added": added,
            "added_count": len(added),
            "skipped": skipped,
            "skipped_count": len(skipped),
            "timestamp": datetime.utcnow().isoformat()
        }

