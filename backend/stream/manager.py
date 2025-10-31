"""
Stream Manager
Handles RTSP stream ingestion and management
"""
import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path

import yaml

from core.config import settings
from .rtsp import RTSPStream
from workflows.engine import WorkflowEngine


logger = logging.getLogger('overwatch.stream')


class StreamManager:
    """Manages multiple RTSP camera streams"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine
        self.streams: Dict[str, RTSPStream] = {}
        self.cameras: Dict[str, dict] = {}
        self._running = False
        
    async def load_cameras(self):
        """Load camera configuration from database"""
        from core.database import SessionLocal, Camera
        
        db = SessionLocal()
        try:
            # Load all cameras from database
            db_cameras = db.query(Camera).all()
            
            if not db_cameras:
                logger.warning("No cameras found in database")
                return
                
            logger.info(f"Loading {len(db_cameras)} cameras from database...")
            
            for db_cam in db_cameras:
                # Get RTSP URL from streams or legacy rtsp_url
                rtsp_url = db_cam.rtsp_url
                if db_cam.streams:
                    active_quality = db_cam.active_stream or 'medium'
                    if active_quality in db_cam.streams:
                        rtsp_url = db_cam.streams[active_quality].get('url')
                
                camera = {
                    'id': db_cam.id,
                    'name': db_cam.name,
                    'type': db_cam.type,
                    'rtsp_url': rtsp_url,
                    'streams': db_cam.streams or {},
                    'active_stream': db_cam.active_stream or 'medium',
                    'enabled': bool(db_cam.enabled),
                    'workflows': db_cam.workflows or [],
                    'settings': db_cam.settings or {}
                }
                
                self.cameras[db_cam.id] = camera
                
                if camera.get('enabled', True):
                    await self.start_stream(db_cam.id)
                    
            logger.info(f"Loaded {len(self.cameras)} cameras")
            
        finally:
            db.close()
        
    async def start_stream(self, camera_id: str) -> bool:
        """Start a camera stream"""
        if camera_id in self.streams:
            logger.warning(f"Stream {camera_id} already running")
            return False
            
        if camera_id not in self.cameras:
            logger.error(f"Camera {camera_id} not found")
            return False
            
        camera = self.cameras[camera_id]
        
        try:
            stream = RTSPStream(
                camera_id=camera_id,
                rtsp_url=camera['rtsp_url'],
                workflow_engine=self.workflow_engine,
                workflows=camera.get('workflows', [])
            )
            
            self.streams[camera_id] = stream
            await stream.start()
            
            logger.info(f"Started stream: {camera_id} ({camera['name']})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start stream {camera_id}: {e}", exc_info=True)
            return False
            
    async def stop_stream(self, camera_id: str) -> bool:
        """Stop a camera stream"""
        if camera_id not in self.streams:
            logger.warning(f"Stream {camera_id} not running")
            return False
            
        try:
            stream = self.streams[camera_id]
            await stream.stop()
            del self.streams[camera_id]
            
            logger.info(f"Stopped stream: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop stream {camera_id}: {e}", exc_info=True)
            return False
            
    async def stop_all(self):
        """Stop all camera streams"""
        logger.info("Stopping all streams...")
        
        tasks = []
        for camera_id in list(self.streams.keys()):
            tasks.append(self.stop_stream(camera_id))
            
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All streams stopped")
        
    def get_stream_status(self, camera_id: str) -> Optional[dict]:
        """Get status of a camera stream"""
        if camera_id not in self.streams:
            return None
            
        stream = self.streams[camera_id]
        return stream.get_status()
        
    def get_all_status(self) -> List[dict]:
        """Get status of all streams"""
        return [
            {
                'camera_id': camera_id,
                'camera_name': self.cameras[camera_id]['name'],
                'status': self.get_stream_status(camera_id)
            }
            for camera_id in self.cameras
        ]
        
    async def add_camera(self, camera_config: dict) -> bool:
        """Add a new camera"""
        camera_id = camera_config['id']
        
        if camera_id in self.cameras:
            logger.error(f"Camera {camera_id} already exists")
            return False
            
        self.cameras[camera_id] = camera_config
        
        if camera_config.get('enabled', True):
            await self.start_stream(camera_id)
            
        return True
        
    async def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera"""
        if camera_id not in self.cameras:
            logger.error(f"Camera {camera_id} not found")
            return False
            
        if camera_id in self.streams:
            await self.stop_stream(camera_id)
            
        del self.cameras[camera_id]
        return True

