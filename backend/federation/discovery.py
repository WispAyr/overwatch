"""
Network Discovery Service
Discovers other Overwatch devices on the local network using mDNS/Zeroconf
"""
import asyncio
import logging
import socket
from typing import Dict, Set, Callable, Optional
from datetime import datetime
import json

from zeroconf import ServiceInfo, Zeroconf
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser, AsyncServiceInfo

from core.config import settings


logger = logging.getLogger('overwatch.discovery')


class DiscoveryService:
    """Discovers and announces Overwatch devices on local network"""
    
    SERVICE_TYPE = "_overwatch._tcp.local."
    
    def __init__(self, device_id: str, device_type: str, port: int = 8000):
        self.device_id = device_id
        self.device_type = device_type
        self.port = port
        self.discovered_devices: Dict[str, Dict] = {}
        self.aiozc: Optional[AsyncZeroconf] = None
        self.browser: Optional[AsyncServiceBrowser] = None
        self.service_info: Optional[ServiceInfo] = None
        self._callbacks: Set[Callable] = set()
        self._running = False
    
    async def start(self):
        """Start discovery service"""
        if self._running:
            logger.warning("Discovery service already running")
            return
        
        logger.info(f"Starting discovery service for {self.device_id}")
        
        try:
            self.aiozc = AsyncZeroconf()
            
            # Register our service
            await self._register_service()
            
            # Start browsing for other devices
            self.browser = AsyncServiceBrowser(
                self.aiozc.zeroconf,
                self.SERVICE_TYPE,
                handlers=[self._on_service_state_change]
            )
            
            self._running = True
            logger.info("Discovery service started")
            
        except Exception as e:
            logger.error(f"Failed to start discovery service: {e}")
            if self.aiozc:
                await self.aiozc.async_close()
    
    async def stop(self):
        """Stop discovery service"""
        if not self._running:
            return
        
        logger.info("Stopping discovery service")
        
        try:
            # Unregister our service
            if self.aiozc and self.service_info:
                await self.aiozc.async_unregister_service(self.service_info)
            
            # Close browser
            if self.browser:
                await self.browser.async_cancel()
            
            # Close zeroconf
            if self.aiozc:
                await self.aiozc.async_close()
            
            self._running = False
            logger.info("Discovery service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping discovery service: {e}")
    
    async def _register_service(self):
        """Register this device as a service"""
        hostname = socket.gethostname()
        local_ip = self._get_local_ip()
        
        # Service properties
        properties = {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'node_type': settings.NODE_TYPE,
            'version': '1.0.0',
            'api_port': str(self.port),
            'hostname': hostname
        }
        
        # Create service info
        self.service_info = ServiceInfo(
            type_=self.SERVICE_TYPE,
            name=f"{self.device_id}.{self.SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties=properties,
            server=f"{hostname}.local."
        )
        
        # Register
        await self.aiozc.async_register_service(self.service_info)
        logger.info(f"Registered service: {self.device_id} at {local_ip}:{self.port}")
    
    def _on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change
    ):
        """Handle service state changes"""
        asyncio.create_task(self._handle_service_change(zeroconf, service_type, name, state_change))
    
    async def _handle_service_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change
    ):
        """Handle service state changes asynchronously"""
        from zeroconf import ServiceStateChange
        
        if state_change == ServiceStateChange.Added:
            await self._on_service_added(zeroconf, service_type, name)
        elif state_change == ServiceStateChange.Removed:
            await self._on_service_removed(name)
        elif state_change == ServiceStateChange.Updated:
            await self._on_service_updated(zeroconf, service_type, name)
    
    async def _on_service_added(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Handle new service discovered"""
        try:
            # Get service info
            info = AsyncServiceInfo(service_type, name)
            await info.async_request(zeroconf, 3000)
            
            if not info:
                return
            
            # Extract device info
            device_id = info.properties.get(b'device_id', b'').decode('utf-8')
            
            # Don't add ourselves
            if device_id == self.device_id:
                return
            
            # Get IP address
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            ip_address = addresses[0] if addresses else None
            
            if not ip_address:
                return
            
            device_info = {
                'device_id': device_id,
                'device_type': info.properties.get(b'device_type', b'').decode('utf-8'),
                'node_type': info.properties.get(b'node_type', b'').decode('utf-8'),
                'hostname': info.properties.get(b'hostname', b'').decode('utf-8'),
                'ip_address': ip_address,
                'port': info.port,
                'url': f"http://{ip_address}:{info.port}",
                'discovered_at': datetime.utcnow().isoformat(),
                'last_seen': datetime.utcnow().isoformat()
            }
            
            self.discovered_devices[device_id] = device_info
            logger.info(f"Discovered device: {device_id} at {ip_address}:{info.port}")
            
            # Notify callbacks
            await self._notify_callbacks('added', device_info)
            
        except Exception as e:
            logger.error(f"Error handling service added: {e}")
    
    async def _on_service_removed(self, name: str):
        """Handle service removed"""
        # Extract device_id from name
        device_id = name.split('.')[0]
        
        if device_id in self.discovered_devices:
            device_info = self.discovered_devices.pop(device_id)
            logger.info(f"Device removed: {device_id}")
            
            # Notify callbacks
            await self._notify_callbacks('removed', device_info)
    
    async def _on_service_updated(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Handle service updated"""
        # Just treat it as a new discovery
        await self._on_service_added(zeroconf, service_type, name)
    
    async def _notify_callbacks(self, event_type: str, device_info: Dict):
        """Notify registered callbacks of device changes"""
        for callback in self._callbacks:
            try:
                await callback(event_type, device_info)
            except Exception as e:
                logger.error(f"Error in discovery callback: {e}")
    
    def add_callback(self, callback: Callable):
        """Add a callback for device discovery events"""
        self._callbacks.add(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback"""
        self._callbacks.discard(callback)
    
    def get_discovered_devices(self) -> Dict[str, Dict]:
        """Get all discovered devices"""
        return self.discovered_devices.copy()
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

