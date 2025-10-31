"""
Object Tracking Model Plugin
Multi-object tracking using ByteTrack/BoT-SORT for persistent object IDs
"""
import asyncio
import logging
from typing import List, Optional, Dict
import numpy as np

from ultralytics import YOLO
from .base import BaseModel


logger = logging.getLogger('overwatch.models.tracking')


class ObjectTrackingModel(BaseModel):
    """
    YOLOv8 with built-in tracking (ByteTrack/BoT-SORT)
    
    Provides persistent object IDs across frames for tracking movement
    """
    
    def __init__(self, model_id: str, config: dict):
        super().__init__(model_id, config)
        self.track_history = {}  # Store track paths
        
    async def initialize(self):
        """Initialize YOLOv8 model with tracking"""
        model_variant = self.config.get('variant', 'n')  # n, s, m, l, x
        model_path = self.config.get('model_path', f'yolov8{model_variant}.pt')
        
        logger.info(f"Loading YOLOv8 tracking model: {model_path}")
        
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(model_path)
        )
        
        logger.info("YOLOv8 tracking model loaded successfully")
        
    async def detect(self, frame: np.ndarray):
        """
        Track objects across frames with persistent IDs
        
        Returns detections with track_id for persistence
        """
        if self.model is None:
            logger.error("Model not initialized")
            return []
            
        # Get tracker type from config (bytetrack or botsort)
        tracker = self.config.get('tracker', 'bytetrack.yaml')
        persist = self.config.get('persist', True)
        
        # Run tracking
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.model.track(
                frame,
                conf=self.config.get('confidence', 0.5),
                tracker=tracker,
                persist=persist,
                verbose=False
            )
        )
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                # Extract box data
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy().tolist()
                
                # Get class name
                class_name = result.names[class_id] if class_id in result.names else f'class_{class_id}'
                
                # Get track ID (unique across frames)
                track_id = int(box.id[0]) if box.id is not None else None
                
                # Calculate center point
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                
                # Update track history
                if track_id is not None:
                    if track_id not in self.track_history:
                        self.track_history[track_id] = {
                            'path': [],
                            'first_seen': 0,
                            'last_seen': 0,
                            'class_name': class_name
                        }
                    
                    # Add current position to path
                    self.track_history[track_id]['path'].append([center_x, center_y])
                    self.track_history[track_id]['last_seen'] += 1
                    
                    # Keep only last 30 points
                    if len(self.track_history[track_id]['path']) > 30:
                        self.track_history[track_id]['path'].pop(0)
                    
                    # Calculate velocity
                    velocity = self._calculate_velocity(track_id)
                    
                    # Calculate dwell time (frames object has been tracked)
                    dwell_time = (self.track_history[track_id]['last_seen'] - 
                                 self.track_history[track_id]['first_seen'])
                else:
                    velocity = 0.0
                    dwell_time = 0
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox,
                    'track_id': track_id,
                    'center': [center_x, center_y],
                    'velocity': velocity,
                    'dwell_time': dwell_time,
                    'track_path': self.track_history.get(track_id, {}).get('path', []),
                    'detection_type': 'tracked'
                }
                
                detections.append(detection)
        
        # Clean up old tracks (not seen in last 30 frames)
        self._cleanup_old_tracks()
        
        return detections
    
    def _calculate_velocity(self, track_id: int) -> float:
        """Calculate velocity from recent track points"""
        if track_id not in self.track_history:
            return 0.0
            
        path = self.track_history[track_id]['path']
        if len(path) < 2:
            return 0.0
        
        # Calculate distance between last two points
        p1 = np.array(path[-2])
        p2 = np.array(path[-1])
        distance = np.linalg.norm(p2 - p1)
        
        return float(distance)
    
    def _cleanup_old_tracks(self):
        """Remove tracks that haven't been seen recently"""
        max_age = self.config.get('max_track_age', 30)
        
        current_tracks = set()
        for track_id, data in self.track_history.items():
            age = data['last_seen'] - data['first_seen']
            if age < max_age:
                current_tracks.add(track_id)
        
        # Remove old tracks
        old_tracks = set(self.track_history.keys()) - current_tracks
        for track_id in old_tracks:
            del self.track_history[track_id]
    
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None
        self.track_history.clear()


