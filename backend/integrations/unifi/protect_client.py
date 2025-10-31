"""
UniFi Protect API Client
Dedicated client for UniFi Protect (camera system)
"""
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger('overwatch.integrations.unifi.protect')


class UniFiProtectClient:
    """UniFi Protect API client for camera management"""
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        verify_ssl: bool = False
    ):
        """
        Initialize UniFi Protect client
        
        Args:
            host: Protect NVR hostname/IP
            username: Admin username
            password: Admin password  
            port: Protect port (default 443)
            verify_ssl: Verify SSL certificates
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.verify_ssl = verify_ssl
        
        self.base_url = f"https://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self._authenticated = False
        self._api_token: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.login()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.logout()
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)
            
    async def login(self):
        """Authenticate with UniFi Protect"""
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._api_token = resp.headers.get('X-CSRF-Token') or resp.headers.get('Authorization')
                    self._authenticated = True
                    logger.info(f"Successfully authenticated to UniFi Protect at {self.host}")
                    return True
                else:
                    error = await resp.text()
                    logger.error(f"UniFi Protect authentication failed: {resp.status} - {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"UniFi Protect login error: {e}")
            return False
            
    async def logout(self):
        """Logout from UniFi Protect"""
        if not self._authenticated:
            return
            
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            self._authenticated = False
            self._api_token = None
            logger.info("Logged out from UniFi Protect")
        except Exception as e:
            logger.error(f"UniFi Protect logout error: {e}")
            
    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request to UniFi Protect
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            params: Query parameters
            
        Returns:
            Response data or None on error
        """
        if not self._authenticated:
            await self.login()
            
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        if self._api_token:
            headers['X-CSRF-Token'] = self._api_token
            
        try:
            async with self.session.request(
                method, 
                url, 
                json=data,
                params=params,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    # Some endpoints return empty responses
                    if resp.content_length == 0:
                        return {}
                    result = await resp.json()
                    return result
                else:
                    error = await resp.text()
                    logger.error(f"UniFi Protect API error: {resp.status} - {error}")
                    return None
                    
        except Exception as e:
            logger.error(f"UniFi Protect API request error: {e}")
            return None
            
    # Bootstrap - Main data endpoint
    
    async def get_bootstrap(self) -> Optional[Dict]:
        """
        Get bootstrap data (all system info)
        This is the main endpoint that returns everything
        """
        return await self._api_request('GET', '/proxy/protect/api/bootstrap')
        
    # Camera Management
    
    async def get_cameras(self) -> List[Dict]:
        """Get all cameras"""
        bootstrap = await self.get_bootstrap()
        if bootstrap and 'cameras' in bootstrap:
            return bootstrap['cameras']
        return []
        
    async def get_camera(self, camera_id: str) -> Optional[Dict]:
        """Get specific camera by ID"""
        cameras = await self.get_cameras()
        for camera in cameras:
            if camera.get('id') == camera_id:
                return camera
        return None
        
    async def get_camera_by_name(self, name: str) -> Optional[Dict]:
        """Get camera by name"""
        cameras = await self.get_cameras()
        for camera in cameras:
            if camera.get('name', '').lower() == name.lower():
                return camera
        return None
        
    async def update_camera(self, camera_id: str, settings: Dict) -> Optional[Dict]:
        """Update camera settings"""
        return await self._api_request(
            'PATCH',
            f'/proxy/protect/api/cameras/{camera_id}',
            data=settings
        )
        
    # Camera Streams
    
    def get_rtsp_url(
        self,
        camera: Dict,
        channel: int = 0,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> str:
        """
        Get RTSP URL for camera stream
        
        Args:
            camera: Camera object from get_cameras()
            channel: Channel index (0=high, 1=medium, 2=low)
            username: Optional RTSP username (uses admin if not provided)
            password: Optional RTSP password (uses admin if not provided)
            
        Returns:
            RTSP URL string
        """
        if not camera:
            return ""
            
        # Use provided credentials or fall back to controller creds
        rtsp_user = username or self.username
        rtsp_pass = password or self.password
        
        camera_id = camera.get('id', '')
        camera_host = camera.get('host', self.host)
        
        # Channel mapping: 0=high, 1=medium, 2=low
        return f"rtsp://{rtsp_user}:{rtsp_pass}@{camera_host}:7447/{camera_id}_{channel}"
        
    def get_snapshot_url(self, camera: Dict, width: int = 640) -> str:
        """
        Get snapshot URL for camera
        
        Args:
            camera: Camera object
            width: Snapshot width
            
        Returns:
            Snapshot URL
        """
        camera_id = camera.get('id', '')
        return f"{self.base_url}/proxy/protect/api/cameras/{camera_id}/snapshot?w={width}"
        
    # Events
    
    async def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        event_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get motion/detection events
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            limit: Max events to return
            event_types: Filter by event types (motion, ring, smartDetectZone, etc)
            
        Returns:
            List of events
        """
        params = {
            'limit': limit
        }
        
        if start_time:
            params['start'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['end'] = int(end_time.timestamp() * 1000)
        if event_types:
            params['types'] = ','.join(event_types)
            
        result = await self._api_request('GET', '/proxy/protect/api/events', params=params)
        if result and isinstance(result, list):
            return result
        return []
        
    async def get_motion_events(
        self,
        camera_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent motion events"""
        events = await self.get_events(limit=limit, event_types=['motion'])
        
        if camera_id:
            events = [e for e in events if e.get('camera') == camera_id]
            
        return events
        
    async def get_smart_detections(
        self,
        camera_id: Optional[str] = None,
        limit: int = 100,
        detection_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get smart detection events
        
        Args:
            camera_id: Filter by camera
            limit: Max events
            detection_type: person, vehicle, animal, etc
            
        Returns:
            List of smart detection events
        """
        events = await self.get_events(limit=limit, event_types=['smartDetectZone'])
        
        if camera_id:
            events = [e for e in events if e.get('camera') == camera_id]
            
        if detection_type:
            events = [
                e for e in events 
                if detection_type in e.get('smartDetectTypes', [])
            ]
            
        return events
        
    # NVR Information
    
    async def get_nvr_info(self) -> Optional[Dict]:
        """Get NVR system information"""
        bootstrap = await self.get_bootstrap()
        if bootstrap and 'nvr' in bootstrap:
            return bootstrap['nvr']
        return None
        
    async def get_storage_info(self) -> Optional[Dict]:
        """Get storage information"""
        nvr = await get_nvr_info()
        if nvr:
            return {
                'total_bytes': nvr.get('storage', {}).get('total_bytes'),
                'used_bytes': nvr.get('storage', {}).get('used_bytes'),
                'available_bytes': nvr.get('storage', {}).get('available_bytes'),
                'recording_retention': nvr.get('recordingRetentionDurationMs')
            }
        return None
        
    # Test connection
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to UniFi Protect
        
        Returns:
            Dict with success status and details
        """
        try:
            success = await self.login()
            if not success:
                return {
                    "success": False,
                    "error": "Authentication failed"
                }
                
            cameras = await self.get_cameras()
            nvr = await self.get_nvr_info()
            
            await self.logout()
            
            return {
                "success": True,
                "camera_count": len(cameras),
                "nvr_name": nvr.get('name') if nvr else 'Unknown',
                "nvr_version": nvr.get('version') if nvr else 'Unknown',
                "cameras": [
                    {
                        'id': c.get('id'),
                        'name': c.get('name'),
                        'model': c.get('type'),
                        'state': c.get('state'),
                        'is_recording': c.get('isRecording', False)
                    }
                    for c in cameras
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

