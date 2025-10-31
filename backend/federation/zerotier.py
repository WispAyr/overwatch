"""
ZeroTier Integration
Manages ZeroTier network for secure federated communication
"""
import asyncio
import logging
import json
from typing import Optional, List, Dict
from pathlib import Path

import aiohttp

from core.config import settings


logger = logging.getLogger('overwatch.federation.zerotier')


class ZeroTierManager:
    """Manages ZeroTier network for federation"""
    
    def __init__(self):
        self.api_token = settings.ZEROTIER_API_TOKEN
        self.network_id = settings.ZEROTIER_NETWORK_ID
        self.api_url = "https://api.zerotier.com/api/v1"
        self.local_port = 9993
        self.node_id: Optional[str] = None
        self.network_info: Optional[Dict] = None
        
    async def initialize(self):
        """Initialize ZeroTier integration"""
        logger.info("Initializing ZeroTier integration...")
        
        # Get local ZeroTier node info
        await self._get_node_info()
        
        if settings.NODE_TYPE == 'central':
            # Central server manages the network
            await self._ensure_network_exists()
            await self._configure_network()
        else:
            # Edge nodes join the network
            await self._join_network()
            
        logger.info(f"ZeroTier initialized (Node: {self.node_id}, Network: {self.network_id})")
        
    async def _get_node_info(self):
        """Get local ZeroTier node information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.local_port}/status",
                    headers={"X-ZT1-Auth": await self._get_local_token()}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.node_id = data.get('address')
                        logger.info(f"Local ZeroTier node: {self.node_id}")
        except Exception as e:
            logger.error(f"Failed to get ZeroTier node info: {e}")
            logger.warning("Is ZeroTier running? Install: https://www.zerotier.com/download/")
            
    async def _get_local_token(self) -> str:
        """Get local ZeroTier auth token"""
        # Token is stored in authtoken.secret file
        token_paths = [
            Path("/var/lib/zerotier-one/authtoken.secret"),  # Linux
            Path.home() / "Library/Application Support/ZeroTier/One/authtoken.secret",  # macOS
            Path("C:/ProgramData/ZeroTier/One/authtoken.secret"),  # Windows
        ]
        
        for path in token_paths:
            if path.exists():
                return path.read_text().strip()
                
        return ""
        
    async def _ensure_network_exists(self):
        """Ensure ZeroTier network exists (central server only)"""
        if not self.api_token:
            logger.warning("ZeroTier API token not configured")
            return
            
        if self.network_id:
            # Verify existing network
            network = await self._get_network(self.network_id)
            if network:
                self.network_info = network
                logger.info(f"Using existing ZeroTier network: {self.network_id}")
                return
                
        # Create new network
        logger.info("Creating new ZeroTier network...")
        await self._create_network()
        
    async def _create_network(self):
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
                        
                        # Save to config for edge nodes to use
                        await self._save_network_config()
        except Exception as e:
            logger.error(f"Failed to create ZeroTier network: {e}")
            
    async def _configure_network(self):
        """Configure ZeroTier network settings"""
        if not self.network_id or not self.api_token:
            return
            
        config = {
            "name": f"Overwatch Federation - {settings.NODE_ID}",
            "private": True,
            "v4AssignMode": {
                "zt": True
            },
            "routes": [
                {
                    "target": "10.147.0.0/16",
                    "via": None
                }
            ],
            "ipAssignmentPools": [
                {
                    "ipRangeStart": "10.147.0.1",
                    "ipRangeEnd": "10.147.255.254"
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
        except Exception as e:
            logger.error(f"Failed to configure network: {e}")
            
    async def _join_network(self):
        """Join ZeroTier network (edge nodes)"""
        if not self.network_id:
            logger.warning("No ZeroTier network ID configured")
            return
            
        try:
            local_token = await self._get_local_token()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{self.local_port}/network/{self.network_id}",
                    headers={"X-ZT1-Auth": local_token}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Joined ZeroTier network: {self.network_id}")
                        
                        # Wait for network to be ready
                        await asyncio.sleep(2)
                        await self._get_network_status()
        except Exception as e:
            logger.error(f"Failed to join network: {e}")
            
    async def _get_network_status(self):
        """Get local network status"""
        try:
            local_token = await self._get_local_token()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.local_port}/network/{self.network_id}",
                    headers={"X-ZT1-Auth": local_token}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"ZeroTier status: {data.get('status')}")
                        logger.info(f"Assigned IP: {data.get('assignedAddresses')}")
        except Exception as e:
            logger.error(f"Failed to get network status: {e}")
            
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
            
        return None
        
    async def authorize_member(self, node_id: str, member_name: str = "") -> bool:
        """Authorize a member to join the network (central server only)"""
        if not self.network_id or not self.api_token:
            return False
            
        try:
            config = {
                "authorized": True,
                "name": member_name or node_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/network/{self.network_id}/member/{node_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=config
                ) as response:
                    if response.status == 200:
                        logger.info(f"Authorized member: {node_id}")
                        return True
        except Exception as e:
            logger.error(f"Failed to authorize member: {e}")
            
        return False
        
    async def deauthorize_member(self, node_id: str) -> bool:
        """Deauthorize a member from the network"""
        if not self.network_id or not self.api_token:
            return False
            
        try:
            config = {"authorized": False}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/network/{self.network_id}/member/{node_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=config
                ) as response:
                    if response.status == 200:
                        logger.info(f"Deauthorized member: {node_id}")
                        return True
        except Exception as e:
            logger.error(f"Failed to deauthorize member: {e}")
            
        return False
        
    async def list_members(self) -> List[Dict]:
        """List all network members (central server only)"""
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
        except Exception as e:
            logger.error(f"Failed to list members: {e}")
            
        return []
        
    async def get_member_ip(self, node_id: str) -> Optional[str]:
        """Get ZeroTier IP address for a member"""
        if not self.network_id or not self.api_token:
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/network/{self.network_id}/member/{node_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assignments = data.get('ipAssignments', [])
                        if assignments:
                            return assignments[0]
        except Exception as e:
            logger.error(f"Failed to get member IP: {e}")
            
        return None
        
    async def _save_network_config(self):
        """Save network config for sharing with edge nodes"""
        config_file = Path(settings.CONFIG_DIR) / "zerotier_network.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            "network_id": self.network_id,
            "created_by": settings.NODE_ID,
            "name": f"Overwatch Federation"
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Saved ZeroTier network config: {config_file}")
        
    async def cleanup(self):
        """Cleanup ZeroTier resources"""
        # Optionally leave network on shutdown
        pass

