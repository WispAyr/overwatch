"""
Fire and Smoke Detection Model Plugin
Early warning system for fire and smoke detection
"""
import asyncio
import logging
from typing import List, Optional
import numpy as np
import cv2

from ultralytics import YOLO
from .base import BaseModel


logger = logging.getLogger('overwatch.models.fire')


class FireDetectionModel(BaseModel):
    """Detect fire and smoke for early warning"""
    
    async def initialize(self):
        """Initialize fire detection model"""
        # Use custom trained model or generic YOLO with color/motion analysis
        model_path = self.config.get('model_path', 'yolov8n.pt')
        
        logger.info(f"Loading Fire Detection model: {model_path}")
        
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(model_path)
        )
        
        # Color analysis for fire (red/orange/yellow hues)
        self.use_color_analysis = self.config.get('use_color_analysis', True)
        
        logger.info("Fire Detection model loaded successfully")
        
    async def detect(self, frame: np.ndarray):
        """
        Detect fire and smoke with high confidence threshold
        
        Returns detections with severity assessment
        """
        if self.model is None:
            logger.error("Model not initialized")
            return []
        
        detections = []
        
        # Try ML detection first
        ml_detections = await self._ml_detection(frame)
        detections.extend(ml_detections)
        
        # Add color-based detection if enabled
        if self.use_color_analysis:
            color_detections = await self._color_based_detection(frame)
            detections.extend(color_detections)
        
        return detections
    
    async def _ml_detection(self, frame: np.ndarray) -> List[dict]:
        """ML-based fire/smoke detection"""
        # Run inference with high confidence
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.model(
                frame,
                conf=self.config.get('confidence', 0.7),
                verbose=False
            )
        )
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy().tolist()
                
                # Get class name
                class_name = result.names.get(class_id, f'class_{class_id}')
                
                # Check if it's fire/smoke related
                if any(keyword in class_name.lower() for keyword in ['fire', 'smoke', 'flame']):
                    # Assess severity based on size and confidence
                    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    frame_area = frame.shape[0] * frame.shape[1]
                    coverage = bbox_area / frame_area
                    
                    if coverage > 0.3 or confidence > 0.9:
                        severity = 'critical'
                    elif coverage > 0.15 or confidence > 0.8:
                        severity = 'high'
                    else:
                        severity = 'medium'
                    
                    detection = {
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': bbox,
                        'severity': severity,
                        'coverage': float(coverage),
                        'detection_type': 'fire_ml',
                        'requires_immediate_action': True
                    }
                    
                    detections.append(detection)
                    
                    logger.warning(
                        f"FIRE/SMOKE DETECTED: {class_name} "
                        f"(confidence: {confidence:.2f}, severity: {severity})"
                    )
        
        return detections
    
    async def _color_based_detection(self, frame: np.ndarray) -> List[dict]:
        """Color-based fire detection (red/orange/yellow regions)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._process_color_detection,
            frame
        )
    
    def _process_color_detection(self, frame: np.ndarray) -> List[dict]:
        """Process color-based fire detection (blocking)"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Define fire color ranges (red, orange, yellow)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            lower_yellow = np.array([20, 100, 100])
            upper_yellow = np.array([40, 255, 255])
            
            # Create masks
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask3 = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            # Combine masks
            fire_mask = mask1 | mask2 | mask3
            
            # Apply morphological operations to reduce noise
            kernel = np.ones((5, 5), np.uint8)
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            min_area = self.config.get('min_fire_area', 500)  # Minimum pixel area
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if area > min_area:
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    bbox = [float(x), float(y), float(x + w), float(y + h)]
                    
                    # Calculate confidence based on color intensity and area
                    roi = fire_mask[y:y+h, x:x+w]
                    fill_ratio = np.sum(roi > 0) / (w * h) if w * h > 0 else 0
                    
                    confidence = min(0.9, fill_ratio * 1.2)
                    
                    # Only return high confidence detections
                    if confidence > 0.6:
                        detection = {
                            'class_id': 999,  # Custom ID
                            'class_name': 'fire_color_based',
                            'confidence': confidence,
                            'bbox': bbox,
                            'area': float(area),
                            'detection_type': 'fire_color',
                            'severity': 'high' if area > 5000 else 'medium'
                        }
                        
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Color-based fire detection error: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None


