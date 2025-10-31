"""
Workflow
Individual workflow implementation
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import uuid

import numpy as np

from models import get_model
from .snapshot import SnapshotHandler


logger = logging.getLogger('overwatch.workflows.workflow')


class Workflow:
    """Individual workflow"""
    
    def __init__(self, workflow_id: str, config: dict, event_manager):
        self.workflow_id = workflow_id
        self.config = config
        self.event_manager = event_manager
        
        self.name = config.get('name', workflow_id)
        self.description = config.get('description', '')
        self.model_id = config.get('model')
        self.model = None
        
        # Detection config
        self.classes = config.get('detection', {}).get('classes', [])
        self.confidence = config.get('detection', {}).get('confidence', 0.7)
        
        # Processing config
        self.processing = config.get('processing', {})
        self.target_fps = self.processing.get('fps', 10)
        self.skip_similar = self.processing.get('skip_similar', False)
        
        # Actions
        self.actions = config.get('actions', [])
        
        # State
        self.last_process_time: Dict[str, float] = {}
        self.frame_count = 0
        self.detection_count = 0
        
        # Snapshot handler
        self.snapshot_handler = SnapshotHandler()
        
    async def initialize(self):
        """Initialize the workflow"""
        logger.info(f"Initializing workflow: {self.workflow_id}")
        
        # Load model
        if self.model_id:
            self.model = await get_model(self.model_id, self.config)
            
    async def process_frame(
        self,
        camera_id: str,
        frame: np.ndarray,
        timestamp: datetime
    ):
        """Process a frame"""
        # Check FPS throttling
        if not self._should_process(camera_id):
            return
            
        self.frame_count += 1
        
        # Run detection
        detections = await self._run_detection(frame)
        
        if not detections:
            return
            
        self.detection_count += len(detections)
        
        # Execute actions
        await self._execute_actions(
            camera_id=camera_id,
            detections=detections,
            frame=frame,
            timestamp=timestamp
        )
        
    async def _run_detection(self, frame: np.ndarray) -> List[dict]:
        """Run model detection on frame"""
        if not self.model:
            return []
            
        try:
            results = await self.model.detect(frame)
            
            # Filter by confidence and classes
            filtered = []
            for detection in results:
                if detection['confidence'] < self.confidence:
                    continue
                    
                if self.classes and detection['class_id'] not in self.classes:
                    continue
                    
                filtered.append(detection)
                
            return filtered
            
        except Exception as e:
            logger.error(f"Detection error in {self.workflow_id}: {e}", exc_info=True)
            return []
            
    async def _execute_actions(
        self,
        camera_id: str,
        detections: List[dict],
        frame: np.ndarray,
        timestamp: datetime,
        audio_result: dict = None
    ):
        """Execute workflow actions"""
        for action in self.actions:
            action_type = action.get('type')
            
            try:
                if action_type == 'event':
                    await self._action_event(
                        camera_id, detections, timestamp, action, frame, audio_result
                    )
                elif action_type == 'alert':
                    await self._action_alert(
                        camera_id, detections, timestamp, action, audio_result
                    )
                elif action_type == 'webhook':
                    await self._action_webhook(
                        camera_id, detections, timestamp, action, audio_result
                    )
                elif action_type == 'record':
                    await self._action_record(
                        camera_id, frame, timestamp, action
                    )
                elif action_type == 'snapshot':
                    # Skip snapshot for audio-only events
                    if frame is not None:
                        await self._action_snapshot(
                            camera_id, frame, detections, timestamp, action
                        )
                    
            except Exception as e:
                logger.error(f"Action error ({action_type}): {e}", exc_info=True)
                
    async def _action_event(
        self,
        camera_id: str,
        detections: List[dict],
        timestamp: datetime,
        action: dict,
        frame: np.ndarray = None,
        audio_result: dict = None
    ):
        """Create event action"""
        event_id = str(uuid.uuid4())
        snapshot_path = None
        
        # Save snapshot if frame provided
        if frame is not None:
            snapshot_path = self.snapshot_handler.save_snapshot(
                frame=frame,
                event_id=event_id,
                detections=detections,
                draw_boxes=True
            )
        
        event = {
            'id': event_id,
            'camera_id': camera_id,
            'workflow_id': self.workflow_id,
            'timestamp': timestamp,
            'severity': action.get('severity', 'info'),
            'detections': detections,
            'snapshot_path': snapshot_path
        }
        
        # Include audio data if present
        if audio_result:
            event['audio_data'] = audio_result
        
        await self.event_manager.create_event(event)
        
    async def _action_alert(
        self,
        camera_id: str,
        detections: List[dict],
        timestamp: datetime,
        action: dict,
        audio_result: dict = None
    ):
        """Create alert action"""
        # Create high-priority event with audio context
        await self._action_event(camera_id, detections, timestamp, action, audio_result=audio_result)
        
        # TODO: Send notifications to configured channels
        # Include audio transcript or detected sounds in alert message
        
    async def _action_webhook(
        self,
        camera_id: str,
        detections: List[dict],
        timestamp: datetime,
        action: dict,
        audio_result: dict = None
    ):
        """Webhook action with retries and exponential backoff"""
        import httpx
        import asyncio
        
        url = action.get('url')
        if not url:
            logger.warning("Webhook action missing URL")
            return
            
        payload = {
            'workflow_id': self.workflow_id,
            'camera_id': camera_id,
            'timestamp': timestamp.isoformat(),
            'detections': detections,
            'action': action.get('data', {})
        }
        
        # Include audio results in webhook payload
        if audio_result:
            payload['audio_data'] = audio_result
        
        max_retries = action.get('retries', 3)
        timeout = action.get('timeout', 10)
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    
                    logger.info(f"Webhook sent to {url}: {response.status_code}")
                    
                    # Store response metadata
                    response_metadata = {
                        'url': url,
                        'status': response.status_code,
                        'body': response.text[:500],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    return response_metadata
                    
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Webhook failed after {max_retries} attempts")
                    
        return None
        
    async def _action_record(
        self,
        camera_id: str,
        frame: np.ndarray,
        timestamp: datetime,
        action: dict
    ):
        """Record video clip using stream buffer"""
        import cv2
        from pathlib import Path
        from core.config import settings
        
        duration = action.get('duration', 30)  # seconds
        pre_buffer = action.get('pre_buffer', 5)  # seconds before event
        
        # Generate recording path
        recording_id = str(uuid.uuid4())
        recording_path = Path(settings.RECORDING_DIR) / f"{recording_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.mp4"
        recording_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Recording {duration}s clip from {camera_id} to {recording_path}")
        
        # Note: This is a basic implementation
        # In production, this should pull from StreamManager's ring buffer
        # and encode the buffered frames + future frames for the duration
        
        try:
            # For now, just save a single frame as a placeholder
            # TODO: Integrate with StreamManager to get buffered frames
            height, width = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(recording_path), fourcc, 10.0, (width, height))
            
            # Write the current frame (placeholder)
            out.write(frame)
            out.release()
            
            logger.info(f"Recording saved to {recording_path}")
            
            return str(recording_path)
            
        except Exception as e:
            logger.error(f"Failed to record clip: {e}")
            return None
    
    async def _action_snapshot(
        self,
        camera_id: str,
        frame: np.ndarray,
        detections: List[dict],
        timestamp: datetime,
        action: dict
    ):
        """Save snapshot using SnapshotHandler"""
        event_id = str(uuid.uuid4())
        
        try:
            # Extract config from action
            draw_boxes = action.get('draw_boxes', True)
            draw_zones = action.get('draw_zones', False)
            img_format = action.get('format', 'jpg')
            quality = action.get('quality', 90)
            
            # Save snapshot with SnapshotHandler
            snapshot_path = self.snapshot_handler.save_snapshot(
                frame=frame,
                event_id=event_id,
                detections=detections if draw_boxes else None,
                draw_boxes=draw_boxes,
                format=img_format,
                quality=quality
            )
            
            logger.info(f"Snapshot saved: {snapshot_path}")
            
            return {
                'snapshot_path': snapshot_path,
                'event_id': event_id,
                'timestamp': timestamp.isoformat(),
                'camera_id': camera_id,
                'detection_count': len(detections)
            }
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return None
        
    def _should_process(self, camera_id: str) -> bool:
        """Check if frame should be processed based on FPS throttling"""
        current_time = time.time()
        last_time = self.last_process_time.get(camera_id, 0)
        
        interval = 1.0 / self.target_fps
        
        if current_time - last_time >= interval:
            self.last_process_time[camera_id] = current_time
            return True
            
        return False
        
    def get_info(self) -> dict:
        """Get workflow information"""
        return {
            'name': self.name,
            'description': self.description,
            'model': self.model_id,
            'enabled': True,
            'frames_processed': self.frame_count,
            'total_detections': self.detection_count
        }
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.model:
            await self.model.cleanup()

