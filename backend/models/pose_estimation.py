"""
YOLOv8-Pose Model Plugin
Pose estimation for fall detection, activity recognition, behavior analysis
"""
import asyncio
import logging
from typing import List, Optional
import numpy as np

from ultralytics import YOLO
from .base import BaseModel


logger = logging.getLogger('overwatch.models.pose')


class PoseEstimationModel(BaseModel):
    """YOLOv8-Pose for human pose estimation"""
    
    # Keypoint indices (COCO format)
    KEYPOINTS = {
        'nose': 0, 'left_eye': 1, 'right_eye': 2, 'left_ear': 3, 'right_ear': 4,
        'left_shoulder': 5, 'right_shoulder': 6, 'left_elbow': 7, 'right_elbow': 8,
        'left_wrist': 9, 'right_wrist': 10, 'left_hip': 11, 'right_hip': 12,
        'left_knee': 13, 'right_knee': 14, 'left_ankle': 15, 'right_ankle': 16
    }
    
    async def initialize(self):
        """Initialize YOLOv8-Pose model"""
        model_variant = self.config.get('variant', 'n')  # n, s, m, l, x
        model_path = self.config.get('model_path', f'yolov8{model_variant}-pose.pt')
        
        logger.info(f"Loading YOLOv8-Pose model: {model_path}")
        
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(model_path)
        )
        
        logger.info("YOLOv8-Pose model loaded successfully")
        
    async def detect(self, frame: np.ndarray):
        """
        Detect people and their pose keypoints
        
        Returns detections with pose data and fall detection analysis
        """
        if self.model is None:
            logger.error("Model not initialized")
            return []
            
        # Run inference
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.model(
                frame,
                conf=self.config.get('confidence', 0.5),
                verbose=False
            )
        )
        
        detections = []
        
        for result in results:
            if result.keypoints is None:
                continue
                
            boxes = result.boxes
            keypoints = result.keypoints
            
            for i, (box, kpts) in enumerate(zip(boxes, keypoints)):
                # Extract box data
                bbox = box.xyxy[0].cpu().numpy().tolist()
                confidence = float(box.conf[0])
                
                # Extract keypoints (x, y, confidence)
                kpts_data = kpts.data[0].cpu().numpy()  # Shape: (17, 3)
                
                # Convert keypoints to dict
                pose_keypoints = {}
                for name, idx in self.KEYPOINTS.items():
                    x, y, conf = kpts_data[idx]
                    pose_keypoints[name] = {
                        'x': float(x),
                        'y': float(y),
                        'confidence': float(conf)
                    }
                
                # Analyze pose for fall detection
                fall_detected, fall_confidence = self._detect_fall(pose_keypoints, bbox)
                
                # Analyze activity
                activity = self._analyze_activity(pose_keypoints)
                
                detection = {
                    'class_id': 0,
                    'class_name': 'person',
                    'confidence': confidence,
                    'bbox': bbox,
                    'keypoints': pose_keypoints,
                    'fall_detected': fall_detected,
                    'fall_confidence': fall_confidence,
                    'activity': activity,
                    'pose_type': 'human_pose'
                }
                
                detections.append(detection)
        
        return detections
    
    def _detect_fall(self, keypoints: dict, bbox: list) -> tuple[bool, float]:
        """
        Detect if person has fallen based on pose keypoints
        
        Returns (fall_detected, confidence)
        """
        try:
            # Get hip and shoulder keypoints
            left_hip = keypoints.get('left_hip', {})
            right_hip = keypoints.get('right_hip', {})
            left_shoulder = keypoints.get('left_shoulder', {})
            right_shoulder = keypoints.get('right_shoulder', {})
            
            # Check if keypoints are visible
            if (left_hip.get('confidence', 0) < 0.3 or 
                right_hip.get('confidence', 0) < 0.3 or
                left_shoulder.get('confidence', 0) < 0.3 or
                right_shoulder.get('confidence', 0) < 0.3):
                return False, 0.0
            
            # Calculate center points
            hip_y = (left_hip['y'] + right_hip['y']) / 2
            shoulder_y = (left_shoulder['y'] + right_shoulder['y']) / 2
            
            # Calculate bounding box dimensions
            bbox_height = bbox[3] - bbox[1]
            bbox_width = bbox[2] - bbox[0]
            
            # Aspect ratio check (fallen person is wider than tall)
            aspect_ratio = bbox_width / bbox_height if bbox_height > 0 else 0
            
            # Torso angle check (shoulders below hips = fallen)
            torso_vertical = abs(shoulder_y - hip_y)
            
            fall_confidence = 0.0
            
            # Wide aspect ratio indicates horizontal person
            if aspect_ratio > 1.3:
                fall_confidence += 0.5
            
            # Small vertical distance between shoulders and hips
            if torso_vertical < bbox_height * 0.3:
                fall_confidence += 0.3
            
            # Check if person is close to ground (bottom of bbox near bottom of frame)
            # This would require frame dimensions, so we skip for now
            
            fall_detected = fall_confidence > 0.6
            
            return fall_detected, float(fall_confidence)
            
        except Exception as e:
            logger.debug(f"Fall detection error: {e}")
            return False, 0.0
    
    def _analyze_activity(self, keypoints: dict) -> str:
        """
        Analyze activity based on pose
        
        Returns activity string: standing, sitting, lying, crouching
        """
        try:
            # Get key points
            nose = keypoints.get('nose', {})
            left_hip = keypoints.get('left_hip', {})
            right_hip = keypoints.get('right_hip', {})
            left_knee = keypoints.get('left_knee', {})
            right_knee = keypoints.get('right_knee', {})
            left_ankle = keypoints.get('left_ankle', {})
            right_ankle = keypoints.get('right_ankle', {})
            
            # Check visibility
            if nose.get('confidence', 0) < 0.3:
                return 'unknown'
            
            # Calculate vertical positions
            hip_y = (left_hip.get('y', 0) + right_hip.get('y', 0)) / 2
            knee_y = (left_knee.get('y', 0) + right_knee.get('y', 0)) / 2
            ankle_y = (left_ankle.get('y', 0) + right_ankle.get('y', 0)) / 2
            
            # Simple heuristics
            if ankle_y - hip_y < 50:  # Legs not extended
                if knee_y - hip_y < 30:
                    return 'lying'
                else:
                    return 'sitting'
            else:
                if knee_y - hip_y > 100:
                    return 'standing'
                else:
                    return 'crouching'
                    
        except Exception as e:
            logger.debug(f"Activity analysis error: {e}")
            return 'unknown'
    
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None


