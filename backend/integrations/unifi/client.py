"""
UniFi Controller API Client
Supports both local controllers and UniFi Cloud
"""
import logging
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import urllib3

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger('overwatch.integrations.unifi')


class UniFiClient:
    """UniFi Controller API client"""
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        site: str = "default",
        verify_ssl: bool = False
    ):
        """
        Initialize UniFi client
        
        Args:
            host: Controller hostname/IP
            username: Admin username
            password: Admin password
            port: Controller port (default 443)
            site: UniFi site name (default "default")
            verify_ssl: Verify SSL certificates
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.site = site
        self.verify_ssl = verify_ssl
        
        self.base_url = f"https://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self._authenticated = False
        
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
        """Authenticate with UniFi controller"""
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/api/login"
            payload = {
                "username": self.username,
                "password": self.password,
                "remember": True
            }
            
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    self._authenticated = True
                    logger.info(f"Successfully authenticated to UniFi controller at {self.host}")
                    return True
                else:
                    error = await resp.text()
                    logger.error(f"UniFi authentication failed: {resp.status} - {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"UniFi login error: {e}")
            return False
            
    async def logout(self):
        """Logout from UniFi controller"""
        if not self._authenticated:
            return
            
        try:
            url = f"{self.base_url}/api/logout"
            async with self.session.post(url) as resp:
                self._authenticated = False
                logger.info("Logged out from UniFi controller")
        except Exception as e:
            logger.error(f"UniFi logout error: {e}")
        finally:
            if self.session and not self.session.closed:
                await self.session.close()
                
    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request to UniFi controller
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/api/s/default/stat/device')
            data: Request payload
            
        Returns:
            Response data or None on error
        """
        if not self._authenticated:
            await self.login()
            
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    error = await resp.text()
                    logger.error(f"UniFi API error: {resp.status} - {error}")
                    return None
                    
        except Exception as e:
            logger.error(f"UniFi API request error: {e}")
            return None
            
    # Site Management
    
    async def get_sites(self) -> List[Dict]:
        """Get list of UniFi sites"""
        result = await self._api_request('GET', '/api/self/sites')
        if result and 'data' in result:
            return result['data']
        return []
        
    async def get_site_info(self) -> Optional[Dict]:
        """Get current site information"""
        result = await self._api_request('GET', f'/api/s/{self.site}/self')
        if result and 'data' in result:
            return result['data'][0] if result['data'] else None
        return None
        
    # Device Management
    
    async def get_devices(self) -> List[Dict]:
        """Get all devices on the site"""
        result = await self._api_request('GET', f'/api/s/{self.site}/stat/device')
        if result and 'data' in result:
            return result['data']
        return []
        
    async def get_device(self, device_mac: str) -> Optional[Dict]:
        """Get specific device by MAC address"""
        devices = await self.get_devices()
        for device in devices:
            if device.get('mac') == device_mac:
                return device
        return None
        
    # Client Management
    
    async def get_clients(self, active_only: bool = True) -> List[Dict]:
        """Get network clients"""
        endpoint = f'/api/s/{self.site}/stat/sta' if active_only else f'/api/s/{self.site}/rest/user'
        result = await self._api_request('GET', endpoint)
        if result and 'data' in result:
            return result['data']
        return []
        
    async def get_client(self, client_mac: str) -> Optional[Dict]:
        """Get specific client by MAC address"""
        result = await self._api_request('GET', f'/api/s/{self.site}/stat/user/{client_mac}')
        if result and 'data' in result:
            return result['data'][0] if result['data'] else None
        return None
        
    # Camera/Protect Integration
    
    async def get_cameras(self) -> List[Dict]:
        """
        Get UniFi Protect cameras
        Note: This works with integrated Protect, for standalone use UniFiProtectClient
        """
        devices = await self.get_devices()
        cameras = [d for d in devices if d.get('type') in ['uvc', 'uap'] and 'camera' in d.get('name', '').lower()]
        return cameras
        
    # Network Information
    
    async def get_network_stats(self) -> Optional[Dict]:
        """Get network statistics"""
        result = await self._api_request('GET', f'/api/s/{self.site}/stat/health')
        if result and 'data' in result:
            return result['data']
        return None
        
    async def get_port_forwards(self) -> List[Dict]:
        """Get port forwarding rules"""
        result = await self._api_request('GET', f'/api/s/{self.site}/rest/portforward')
        if result and 'data' in result:
            return result['data']
        return []
        
    # Alerts and Events
    
    async def get_alerts(self, limit: int = 100) -> List[Dict]:
        """Get recent alerts"""
        result = await self._api_request('GET', f'/api/s/{self.site}/stat/alarm?_limit={limit}')
        if result and 'data' in result:
            return result['data']
        return []
        
    async def get_events(self, limit: int = 100) -> List[Dict]:
        """Get recent events"""
        result = await self._api_request('GET', f'/api/s/{self.site}/stat/event?_limit={limit}')
        if result and 'data' in result:
            return result['data']
        return []
        
    # Test connection
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to UniFi controller
        
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
                
            site_info = await self.get_site_info()
            devices = await self.get_devices()
            
            await self.logout()
            
            return {
                "success": True,
                "site_name": site_info.get('desc') if site_info else 'Unknown',
                "device_count": len(devices),
                "controller_version": site_info.get('version') if site_info else 'Unknown'
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

