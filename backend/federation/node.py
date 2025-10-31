"""
Federated Node
Represents a remote Overwatch server in the federation
"""
import logging
from typing import Optional, Dict
from datetime import datetime
import aiohttp


logger = logging.getLogger('overwatch.federation.node')


class FederatedNode:
    """Represents a federated Overwatch node"""
    
    def __init__(
        self,
        node_id: str,
        node_type: str,
        url: str,
        metadata: Optional[Dict] = None
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.url = url
        self.metadata = metadata or {}
        self.last_heartbeat: Optional[datetime] = None
        
    def update_info(self, info: dict):
        """Update node information"""
        self.url = info.get('url', self.url)
        self.metadata = info.get('metadata', self.metadata)
        self.last_heartbeat = datetime.utcnow()
        
    async def send_event(self, event: dict) -> bool:
        """Send an event to this node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.url}/api/federation/events",
                    json=event
                ) as response:
                    return response.status in [200, 201]
        except Exception as e:
            logger.error(f"Failed to send event to {self.node_id}: {e}")
            return False
            
    async def get_status(self) -> dict:
        """Get status from this node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/api/system/status",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Failed to get status from {self.node_id}: {e}")
            
        return {'status': 'offline'}
        
    async def sync_cameras(self) -> list:
        """Get camera list from this node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/api/cameras"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('cameras', [])
        except Exception as e:
            logger.error(f"Failed to sync cameras from {self.node_id}: {e}")
            
        return []

