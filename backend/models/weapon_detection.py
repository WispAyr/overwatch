"""
Weapon Detection Model Plugin
Detect guns, knives, and weapons for critical security alerts
"""
import asyncio
import logging
from typing import List, Optional
import numpy as np

from ultralytics import YOLO
from .base import BaseModel


logger = logging.getLogger('overwatch.models.weapon')


class WeaponDetectionModel(BaseModel):
    """Detect guns, knives, and weapons"""
    
    # Weapon class mappings (customize based on your model)
    WEAPON_CLASSES = {
        0: 'handgun',
        1: 'rifle',
        2: 'knife',
        3: 'weapon'
    }
    
    # Threat levels
    THREAT_LEVELS = {
        'handgun': 'critical',
        'rifle': 'critical',
        'knife': 'high',
        'weapon': 'high'
    }
    
    async def initialize(self):
        """Initialize weapon detection model"""
        # Can use custom trained model or pre-trained from Roboflow/HuggingFace
        model_path = self.config.get('model_path', 'yolov8n.pt')  # Use custom weapon model if available
        
        logger.info(f"Loading Weapon Detection model: {model_path}")
        
        # Load custom class names if provided
        custom_classes = self.config.get('class_names')
        if custom_classes:
            self.WEAPON_CLASSES = {i: name for i, name in enumerate(custom_classes)}
        
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(model_path)
        )
        
        logger.info("Weapon Detection model loaded successfully")
        
    async def detect(self, frame: np.ndarray):
        """
        Detect weapons with high confidence threshold
        
        Returns detections with threat level assessment
        """
        if self.model is None:
            logger.error("Model not initialized")
            return []
            
        # Use high confidence threshold for weapons (reduce false positives)
        high_conf = self.config.get('confidence', 0.85)
        
        # Run inference
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.model(
                frame,
                conf=high_conf,
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
                
                # Get weapon type
                if class_id in result.names:
                    weapon_type = result.names[class_id]
                elif class_id in self.WEAPON_CLASSES:
                    weapon_type = self.WEAPON_CLASSES[class_id]
                else:
                    weapon_type = 'unknown_weapon'
                
                # Determine threat level
                threat_level = self.THREAT_LEVELS.get(weapon_type, 'high')
                
                # Only return detections above high confidence threshold
                if confidence >= high_conf:
                    detection = {
                        'class_id': class_id,
                        'class_name': weapon_type,
                        'confidence': confidence,
                        'bbox': bbox,
                        'threat_level': threat_level,
                        'alert_priority': 'critical',
                        'detection_type': 'weapon',
                        'requires_immediate_action': True
                    }
                    
                    detections.append(detection)
                    
                    # Log critical detection
                    logger.warning(
                        f"WEAPON DETECTED: {weapon_type} "
                        f"(confidence: {confidence:.2f}, threat: {threat_level})"
                    )
        
        return detections
    
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None


