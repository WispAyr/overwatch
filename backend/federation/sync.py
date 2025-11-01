"""
Federation Synchronization Service
Handles bidirectional sync of workflows, cameras, and configurations
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import json

import aiohttp


logger = logging.getLogger('overwatch.federation.sync')


class SyncService:
    """Manages synchronization between federated nodes"""
    
    def __init__(self, federation_manager):
        self.federation_manager = federation_manager
        self._sync_lock = asyncio.Lock()
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Track sync state
        self._last_sync: Dict[str, datetime] = {}
        self._sync_hashes: Dict[str, str] = {}
    
    async def start(self, interval: int = 60):
        """Start periodic sync"""
        if self._running:
            return
        
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop(interval))
        logger.info(f"Sync service started (interval: {interval}s)")
    
    async def stop(self):
        """Stop sync service"""
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Sync service stopped")
    
    async def _sync_loop(self, interval: int):
        """Periodic sync loop"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self.sync_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
    
    async def sync_all(self):
        """Sync all resources with federated nodes"""
        async with self._sync_lock:
            logger.debug("Starting federation sync...")
            
            if self.federation_manager.node_type == 'edge':
                # Edge nodes sync FROM central
                await self._sync_from_central()
            else:
                # Central node syncs WITH edge nodes
                await self._sync_with_edges()
            
            logger.debug("Federation sync completed")
    
    async def _sync_from_central(self):
        """Sync resources from central server (edge node)"""
        if not self.federation_manager.central_url:
            return
        
        central_url = self.federation_manager._get_central_url()
        
        try:
            # Sync workflows
            workflows = await self._fetch_resource(central_url, '/api/workflows')
            if workflows:
                await self._apply_workflows(workflows)
            
            # Sync cameras (metadata only, not credentials)
            cameras = await self._fetch_resource(central_url, '/api/cameras')
            if cameras:
                await self._apply_cameras(cameras)
            
            # Sync hierarchy
            hierarchy = await self._fetch_resource(central_url, '/api/hierarchy/tree')
            if hierarchy:
                await self._apply_hierarchy(hierarchy)
            
            self._last_sync['central'] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error syncing from central: {e}")
    
    async def _sync_with_edges(self):
        """Sync resources with edge nodes (central node)"""
        for node_id, node in self.federation_manager.nodes.items():
            try:
                # Get edge node's resources
                workflows = await self._fetch_resource(node.url, '/api/workflows')
                
                # Merge with central (edge nodes can contribute workflows)
                if workflows:
                    await self._merge_workflows(workflows, node_id)
                
                self._last_sync[node_id] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error syncing with edge node {node_id}: {e}")
    
    async def _fetch_resource(self, base_url: str, endpoint: str) -> Optional[Any]:
        """Fetch a resource from a node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}{endpoint}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error fetching {endpoint} from {base_url}: {e}")
        
        return None
    
    async def _apply_workflows(self, workflows: List[Dict]):
        """Apply workflows from central server"""
        # This would integrate with your workflow engine
        # For now, just log
        logger.info(f"Received {len(workflows)} workflows from central")
        
        # TODO: Integrate with workflow engine to apply workflows
        # workflow_engine = self.federation_manager._app.state.workflow_engine
        # for workflow in workflows:
        #     await workflow_engine.load_workflow(workflow)
    
    async def _apply_cameras(self, cameras: List[Dict]):
        """Apply camera configurations from central server"""
        logger.info(f"Received {len(cameras)} cameras from central")
        
        # TODO: Integrate with camera manager
        # camera_manager = self.federation_manager._app.state.camera_manager
        # for camera in cameras:
        #     await camera_manager.add_camera(camera)
    
    async def _apply_hierarchy(self, hierarchy: Dict):
        """Apply hierarchy from central server"""
        logger.info("Received hierarchy from central")
        
        # TODO: Integrate with hierarchy manager
    
    async def _merge_workflows(self, workflows: List[Dict], source_node: str):
        """Merge workflows from edge node"""
        logger.info(f"Merging {len(workflows)} workflows from {source_node}")
        
        # TODO: Implement intelligent merge strategy
        # - Check for conflicts
        # - Preserve local modifications
        # - Propagate to other nodes
    
    async def push_workflow(self, workflow: Dict, target_nodes: Optional[List[str]] = None):
        """Push a workflow to target nodes"""
        if self.federation_manager.node_type == 'edge':
            # Edge nodes push to central
            if self.federation_manager.central_url:
                await self._push_resource(
                    self.federation_manager._get_central_url(),
                    '/api/workflows',
                    workflow
                )
        else:
            # Central pushes to specified edge nodes or all
            nodes = target_nodes or list(self.federation_manager.nodes.keys())
            
            for node_id in nodes:
                if node_id in self.federation_manager.nodes:
                    node = self.federation_manager.nodes[node_id]
                    await self._push_resource(
                        node.url,
                        '/api/workflows',
                        workflow
                    )
    
    async def _push_resource(self, base_url: str, endpoint: str, data: Dict):
        """Push a resource to a node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}{endpoint}",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status not in [200, 201]:
                        logger.warning(f"Failed to push to {base_url}{endpoint}: {response.status}")
        except Exception as e:
            logger.error(f"Error pushing to {base_url}{endpoint}: {e}")
    
    def _calculate_hash(self, data: Any) -> str:
        """Calculate hash of data for change detection"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status"""
        return {
            'running': self._running,
            'last_sync': {
                node_id: timestamp.isoformat()
                for node_id, timestamp in self._last_sync.items()
            },
            'node_count': len(self._last_sync)
        }

