"""
ZeroTier Network Provider
Implements overlay networking using ZeroTier
"""
import asyncio
import logging
import json
from typing import Optional, List, Dict
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

from core.config import settings
from .base import NetworkProvider


logger = logging.getLogger('overwatch.federation.zerotier')


class ZeroTierProvider(NetworkProvider):
    """ZeroTier overlay network provider"""
    
    def __init__(self):
        self.api_token = settings.ZEROTIER_API_TOKEN
        self.network_id = settings.ZEROTIER_NETWORK_ID
        self.api_url = "https://api.zerotier.com/api/v1"
        self.local_port = settings.ZEROTIER_LOCAL_API_PORT
        self.node_id: Optional[str] = None
        self.network_info: Optional[Dict] = None
        self.assigned_addresses: List[str] = []
        self.local_api_available = False
        self.last_error: Optional[str] = None
        self._local_token: Optional[str] = None
        
    async def initialize(self) -> bool:
        """Initialize ZeroTier provider"""
        logger.info("Initializing ZeroTier provider...")
        
        try:
            # Test local API availability
            self.local_api_available = await self._test_local_api()
            
            if self.local_api_available:
                # Get local ZeroTier node info
                await self._get_node_info()
            else:
                logger.warning("ZeroTier local API unavailable - management-only mode")
                # Can still manage networks via Central API if we have a token
                if not self.api_token:
                    logger.error("No API token and no local API - ZeroTier unusable")
                    self.last_error = "local_api_unavailable_no_token"
                    return False
                else:
                    logger.info("Central API available for management operations")
            
            if settings.NODE_TYPE == 'central':
                # Central server manages the network
                if not await self.ensure_network():
                    return False
                # Central node should join its own network (Comment 1)
                if self.local_api_available:
                    await self.join_network()
            else:
                # Edge nodes join the network
                if self.local_api_available:
                    await self.join_network()
                else:
                    logger.error("Edge nodes require local ZeroTier API")
                    self.last_error = "edge_requires_local_api"
                    return False
            
            logger.info(f"ZeroTier initialized (Node: {self.node_id}, Network: {self.network_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ZeroTier: {e}")
            self.last_error = str(e)
            return False
    
    async def _test_local_api(self) -> bool:
        """Test if local ZeroTier API is available"""
        try:
            # Try to get local token
            self._local_token = await self._get_local_token()
            if not self._local_token:
                logger.warning("Could not read ZeroTier authtoken.secret - permission denied or not installed")
                return False
            
            # Test local API connection
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.local_port}/status",
                    headers={"X-ZT1-Auth": self._local_token},
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        logger.info("ZeroTier local API available")
                        return True
                    else:
                        logger.warning(f"ZeroTier local API returned {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"ZeroTier local API test failed: {e}")
            return False
    
    async def _get_node_info(self):
        """Get local ZeroTier node information"""
        if not self.local_api_available or not self._local_token:
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.local_port}/status",
                    headers={"X-ZT1-Auth": self._local_token}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.node_id = data.get('address')
                        logger.info(f"Local ZeroTier node: {self.node_id}")
        except Exception as e:
            logger.error(f"Failed to get ZeroTier node info: {e}")
            self.last_error = str(e)
    
    async def _get_local_token(self) -> str:
        """Get local ZeroTier auth token"""
        # Token is stored in authtoken.secret file
        token_paths = [
            Path("/var/lib/zerotier-one/authtoken.secret"),  # Linux
            Path.home() / "Library/Application Support/ZeroTier/One/authtoken.secret",  # macOS
            Path("C:/ProgramData/ZeroTier/One/authtoken.secret"),  # Windows
        ]
        
        for path in token_paths:
            try:
                if path.exists():
                    return path.read_text().strip()
            except PermissionError:
                logger.warning(f"Permission denied reading {path}")
                continue
            except Exception as e:
                logger.debug(f"Could not read {path}: {e}")
                continue
        
        return ""
    
    async def ensure_network(self) -> bool:
        """Ensure ZeroTier network exists (central server only)"""
        if not self.api_token:
            logger.warning("ZeroTier API token not configured")
            self.last_error = "no_api_token"
            return False
        
        if self.network_id:
            # Verify existing network
            network = await self._get_network(self.network_id)
            if network:
                self.network_info = network
                logger.info(f"Using existing ZeroTier network: {self.network_id}")
                # Configure network settings
                await self._configure_network()
                return True
            else:
                logger.warning(f"Network {self.network_id} not found, creating new one")
        
        # Create new network
        logger.info("Creating new ZeroTier network...")
        return await self._create_network()
    
    async def _create_network(self) -> bool:
        """Create a new ZeroTier network"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/network",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json={}
                ) as response:
                    if response.status in [200, 201]:
                        network = await response.json()
                        self.network_id = network['id']
                        self.network_info = network
                        logger.info(f"Created ZeroTier network: {self.network_id}")
                        
                        # Configure network
                        await self._configure_network()
                        
                        # Save to config for edge nodes to use
                        await self._save_network_config()
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create network: {response.status} - {error_text}")
                        self.last_error = f"create_failed_{response.status}"
                        return False
        except Exception as e:
            logger.error(f"Failed to create ZeroTier network: {e}")
            self.last_error = str(e)
            return False
    
    async def _configure_network(self):
        """Configure ZeroTier network settings"""
        if not self.network_id or not self.api_token:
            return
        
        # Use configurable settings from config.py (Comment 7)
        config = {
            "name": f"{settings.ZEROTIER_NETWORK_NAME} - {settings.NODE_ID}",
            "private": True,
            "v4AssignMode": {
                "zt": True
            },
            "routes": [
                {
                    "target": settings.ZEROTIER_ROUTE_TARGET,
                    "via": None
                }
            ],
            "ipAssignmentPools": [
                {
                    "ipRangeStart": settings.ZEROTIER_IP_RANGE_START,
                    "ipRangeEnd": settings.ZEROTIER_IP_RANGE_END
                }
            ],
            "rules": [
                {
                    "type": "ACTION_ACCEPT"
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/network/{self.network_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=config
                ) as response:
                    if response.status == 200:
                        logger.info("ZeroTier network configured")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to configure network: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Failed to configure network: {e}")
            self.last_error = str(e)
    
    async def join_network(self) -> bool:
        """Join ZeroTier network"""
        if not self.network_id:
            logger.warning("No ZeroTier network ID configured")
            self.last_error = "no_network_id"
            return False
        
        if not self.local_api_available or not self._local_token:
            logger.error("Cannot join network - local API not available")
            self.last_error = "local_api_unavailable"
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{self.local_port}/network/{self.network_id}",
                    headers={"X-ZT1-Auth": self._local_token}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Joined ZeroTier network: {self.network_id}")
                        
                        # Wait for network assignment (Comment 1)
                        await asyncio.sleep(2)
                        await self._get_network_status()
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to join network: {response.status} - {error_text}")
                        self.last_error = f"join_failed_{response.status}"
                        return False
        except Exception as e:
            logger.error(f"Failed to join network: {e}")
            self.last_error = str(e)
            return False
    
    async def _get_network_status(self):
        """Get local network status and log assigned IP (Comment 1)"""
        if not self.local_api_available or not self._local_token:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.local_port}/network/{self.network_id}",
                    headers={"X-ZT1-Auth": self._local_token}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status')
                        self.assigned_addresses = data.get('assignedAddresses', [])
                        logger.info(f"ZeroTier status: {status}")
                        logger.info(f"Assigned IPs: {', '.join(self.assigned_addresses)}")
        except Exception as e:
            logger.error(f"Failed to get network status: {e}")
            self.last_error = str(e)
    
    async def _get_network(self, network_id: str) -> Optional[Dict]:
        """Get network information from ZeroTier API"""
        if not self.api_token:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/network/{network_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            self.last_error = str(e)
        
        return None
    
    async def authorize_member(self, member_id: str, member_name: str = "") -> bool:
        """Authorize a member to join the network"""
        if not self.network_id or not self.api_token:
            return False
        
        try:
            config = {
                "authorized": True,
                "name": member_name or member_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/network/{self.network_id}/member/{member_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=config
                ) as response:
                    if response.status == 200:
                        logger.info(f"Authorized member: {member_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to authorize member: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Failed to authorize member: {e}")
            self.last_error = str(e)
            return False
    
    async def list_members(self) -> List[Dict]:
        """List all network members"""
        if not self.network_id or not self.api_token:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/network/{self.network_id}/member",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to list members: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Failed to list members: {e}")
            self.last_error = str(e)
            return []
    
    async def get_member_ip(self, member_id: str) -> Optional[str]:
        """Get ZeroTier IP address for a member"""
        if not self.network_id or not self.api_token:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/network/{self.network_id}/member/{member_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assignments = data.get('ipAssignments', [])
                        if assignments:
                            return assignments[0]
        except Exception as e:
            logger.error(f"Failed to get member IP: {e}")
            self.last_error = str(e)
        
        return None
    
    async def status(self) -> Dict:
        """Get current provider status (Comment 8)"""
        # Get peer count from local API
        peer_count = 0
        if self.local_api_available and self._local_token:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://localhost:{self.local_port}/peer",
                        headers={"X-ZT1-Auth": self._local_token}
                    ) as response:
                        if response.status == 200:
                            peers = await response.json()
                            peer_count = len([p for p in peers if p.get('role') == 'LEAF'])
            except:
                pass
        
        # Get member count from Central API
        member_count = 0
        if self.api_token and settings.NODE_TYPE == 'central':
            members = await self.list_members()
            member_count = len(members)
        
        # Refresh local network status
        if self.local_api_available:
            await self._get_network_status()
        
        return {
            "enabled": True,
            "provider": "zerotier",
            "online": self.local_api_available,
            "node_id": self.node_id,
            "network_id": self.network_id,
            "assigned_addresses": self.assigned_addresses,
            "peer_count": peer_count,
            "member_count": member_count,
            "local_api_available": self.local_api_available,
            "last_error": self.last_error
        }
    
    def prefer_overlay_url(self, original_url: str) -> str:
        """Convert URL to use ZeroTier IP if available (Comment 3)"""
        if not self.assigned_addresses:
            return original_url
        
        try:
            parsed = urlparse(original_url)
            # Use first assigned IPv4 address
            overlay_ip = None
            for addr in self.assigned_addresses:
                if '.' in addr and '/' in addr:
                    overlay_ip = addr.split('/')[0]
                    break
                elif '.' in addr:
                    overlay_ip = addr
                    break
            
            if overlay_ip:
                # Replace host with ZeroTier IP
                overlay_url = f"{parsed.scheme}://{overlay_ip}:{parsed.port or 8000}{parsed.path}"
                logger.debug(f"Prefer overlay URL: {overlay_url}")
                return overlay_url
        except Exception as e:
            logger.warning(f"Failed to convert to overlay URL: {e}")
        
        return original_url
    
    async def _save_network_config(self):
        """Save network config for sharing with edge nodes"""
        config_file = Path(settings.CONFIG_DIR) / "zerotier_network.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            "network_id": self.network_id,
            "created_by": settings.NODE_ID,
            "name": settings.ZEROTIER_NETWORK_NAME
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved ZeroTier network config: {config_file}")
    
    async def cleanup(self):
        """Cleanup ZeroTier resources"""
        # Optionally leave network on shutdown
        pass


