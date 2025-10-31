"""
Federation Manager
Manages connections to other Overwatch servers
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp

from core.config import settings
from .node import FederatedNode
from .providers.base import NetworkProvider, NoOpProvider
from .providers.zerotier import ZeroTierProvider


logger = logging.getLogger('overwatch.federation')


class FederationManager:
    """Manages federated server connections"""
    
    def __init__(self):
        self.nodes: Dict[str, FederatedNode] = {}
        self.local_node_id = settings.NODE_ID
        self.node_type = settings.NODE_TYPE  # 'central' or 'edge'
        self.central_url = settings.CENTRAL_SERVER_URL
        self.central_mesh_url: Optional[str] = None  # ZeroTier mesh URL
        self.use_mesh = False  # Whether to prefer mesh over public URL
        self._heartbeat_task = None
        self._health_check_task = None
        self.overlay_provider: NetworkProvider = None
        
    async def initialize(self):
        """Initialize federation"""
        logger.info(f"Initializing federation (Node: {self.local_node_id}, Type: {self.node_type})")
        
        # Initialize overlay network provider (Comment 5)
        if settings.ENABLE_ZEROTIER:
            if settings.OVERLAY_PROVIDER == "zerotier":
                self.overlay_provider = ZeroTierProvider()
            else:
                logger.warning(f"Unknown overlay provider: {settings.OVERLAY_PROVIDER}")
                self.overlay_provider = NoOpProvider()
        else:
            self.overlay_provider = NoOpProvider()
        
        # Initialize the provider
        if self.overlay_provider:
            provider_ok = await self.overlay_provider.initialize()
            if not provider_ok:
                logger.warning("Overlay provider initialization failed, continuing without overlay")
        
        if self.node_type == 'edge' and self.central_url:
            # Edge node: Discover central's mesh IP and register (Comment 3)
            await self._discover_central_mesh_ip()
            
            # Register with central server
            await self._register_with_central()
            
            # Start heartbeat and health check loops
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())
        else:
            # Central node: Wait for edge nodes to register
            logger.info("Central server ready to accept edge node connections")
    
    async def _discover_central_mesh_ip(self):
        """
        Discover central server's ZeroTier IP (Comment 3)
        Call central's /api/zerotier/status over public URL to get its mesh IP
        """
        if not self.overlay_provider or not settings.ENABLE_ZEROTIER:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.central_url}/api/zerotier/status",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('enabled') and data.get('assigned_addresses'):
                            # Extract first IPv4 address
                            for addr in data['assigned_addresses']:
                                if '.' in addr:
                                    ip = addr.split('/')[0] if '/' in addr else addr
                                    # Construct mesh URL
                                    self.central_mesh_url = f"http://{ip}:8000"
                                    logger.info(f"Discovered central mesh IP: {self.central_mesh_url}")
                                    # Test connectivity before switching
                                    if await self._test_url(self.central_mesh_url):
                                        self.use_mesh = True
                                        logger.info("Using mesh URL for federation traffic")
                                    else:
                                        logger.warning("Mesh URL not reachable, using public URL")
                                    break
        except Exception as e:
            logger.warning(f"Could not discover central mesh IP: {e}")
    
    async def _test_url(self, url: str) -> bool:
        """Test if a URL is reachable"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}/health",
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    def _get_central_url(self) -> str:
        """Get the appropriate central URL (mesh or public) (Comment 3)"""
        if self.use_mesh and self.central_mesh_url:
            return self.central_mesh_url
        return self.central_url
    
    async def _health_check_loop(self):
        """
        Periodically check mesh and public connectivity (Comment 12)
        Prefer mesh when healthy, fall back to public when not
        """
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if not self.central_mesh_url:
                    continue
                
                # Test both URLs
                mesh_ok = await self._test_url(self.central_mesh_url)
                public_ok = await self._test_url(self.central_url)
                
                # Decide which to use
                old_use_mesh = self.use_mesh
                if mesh_ok:
                    self.use_mesh = True
                elif public_ok:
                    self.use_mesh = False
                else:
                    logger.error("Both mesh and public URLs unreachable")
                
                # Log transition
                if old_use_mesh != self.use_mesh:
                    if self.use_mesh:
                        logger.info("Switched to mesh URL (ZeroTier)")
                    else:
                        logger.warning("Fell back to public URL (mesh unreachable)")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def register_node(self, node_info: dict) -> bool:
        """Register a federated node (called by edge nodes)"""
        node_id = node_info['node_id']
        
        if node_id in self.nodes:
            logger.warning(f"Node {node_id} already registered, updating...")
            self.nodes[node_id].update_info(node_info)
            return True
        
        node = FederatedNode(
            node_id=node_id,
            node_type=node_info['node_type'],
            url=node_info['url'],
            metadata=node_info.get('metadata', {})
        )
        
        self.nodes[node_id] = node
        logger.info(f"Registered federated node: {node_id} ({node_info['node_type']})")
        
        # Auto-authorize in overlay network if enabled (Comment 2)
        if self.overlay_provider and 'zerotier_address' in node_info.get('metadata', {}):
            zt_address = node_info['metadata']['zerotier_address']
            logger.info(f"Auto-authorizing ZeroTier member: {zt_address}")
            await self.overlay_provider.authorize_member(zt_address, node_id)
        
        return True
    
    async def unregister_node(self, node_id: str) -> bool:
        """Unregister a federated node"""
        if node_id not in self.nodes:
            return False
        
        del self.nodes[node_id]
        logger.info(f"Unregistered node: {node_id}")
        return True
    
    async def forward_event(self, event: dict, target_nodes: Optional[List[str]] = None):
        """Forward an event to federated nodes"""
        if self.node_type == 'edge':
            # Edge nodes forward to central
            if self.central_url:
                await self._send_to_central('/api/federation/events', event)
        else:
            # Central server forwards to specified edge nodes or all
            nodes = target_nodes or list(self.nodes.keys())
            
            tasks = []
            for node_id in nodes:
                if node_id in self.nodes:
                    tasks.append(
                        self.nodes[node_id].send_event(event)
                    )
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def sync_hierarchy(self) -> dict:
        """Sync hierarchy from central server (edge nodes)"""
        if self.node_type != 'edge' or not self.central_url:
            return {}
        
        try:
            url = self._get_central_url()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}/api/hierarchy/tree"
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Failed to sync hierarchy: {e}")
        
        return {}
    
    async def get_cluster_status(self) -> dict:
        """Get status of all nodes in federation"""
        status = {
            'local_node': {
                'id': self.local_node_id,
                'type': self.node_type,
                'status': 'online'
            },
            'federated_nodes': [],
            'overlay': None
        }
        
        # Add overlay status if enabled
        if self.overlay_provider:
            status['overlay'] = await self.overlay_provider.status()
        
        # Add mesh connectivity status
        if self.node_type == 'edge' and self.central_mesh_url:
            status['mesh_connectivity'] = {
                'mesh_url': self.central_mesh_url,
                'public_url': self.central_url,
                'using_mesh': self.use_mesh
            }
        
        for node_id, node in self.nodes.items():
            node_status = await node.get_status()
            status['federated_nodes'].append({
                'id': node_id,
                'type': node.node_type,
                'url': node.url,
                'status': node_status.get('status', 'unknown'),
                'last_seen': node.last_heartbeat.isoformat() if node.last_heartbeat else None
            })
        
        return status
    
    async def _register_with_central(self):
        """Register this edge node with central server"""
        metadata = {
            'version': '1.0.0',
            'capabilities': ['stream_processing', 'ai_inference']
        }
        
        # Add ZeroTier address if available (Comment 2, 6)
        if self.overlay_provider and settings.ENABLE_ZEROTIER:
            provider_status = await self.overlay_provider.status()
            if provider_status.get('online') and provider_status.get('node_id'):
                metadata['zerotier_address'] = provider_status['node_id']
                logger.info(f"Including ZeroTier address in registration: {metadata['zerotier_address']}")
        
        registration_data = {
            'node_id': self.local_node_id,
            'node_type': self.node_type,
            'url': settings.NODE_URL,
            'metadata': metadata
        }
        
        try:
            await self._send_to_central('/api/federation/register', registration_data)
            logger.info(f"Registered with central server: {self._get_central_url()}")
        except Exception as e:
            logger.error(f"Failed to register with central server: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to central server"""
        while True:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                heartbeat_data = {
                    'node_id': self.local_node_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'online'
                }
                
                await self._send_to_central('/api/federation/heartbeat', heartbeat_data)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def _send_to_central(self, endpoint: str, data: dict):
        """Send data to central server"""
        if not self.central_url:
            return
        
        url = f"{self._get_central_url()}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status not in [200, 201]:
                    logger.warning(f"Central server returned {response.status}")
    
    async def cleanup(self):
        """Cleanup federation"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup overlay provider
        if self.overlay_provider:
            await self.overlay_provider.cleanup()
        
        # Unregister from central if edge node
        if self.node_type == 'edge' and self.central_url:
            try:
                await self._send_to_central(
                    '/api/federation/unregister',
                    {'node_id': self.local_node_id}
                )
            except:
                pass
