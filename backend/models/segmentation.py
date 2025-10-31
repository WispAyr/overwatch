"""
YOLOv8-Seg Model Plugin
Instance segmentation for precise object masks
"""
import asyncio
import logging
from typing import List, Optional
import numpy as np
import cv2

from ultralytics import YOLO
from .base import BaseModel


logger = logging.getLogger('overwatch.models.segmentation')


class SegmentationModel(BaseModel):
    """YOLOv8-Seg for instance segmentation"""
    
    async def initialize(self):
        """Initialize YOLOv8-Seg model"""
        model_variant = self.config.get('variant', 'n')  # n, s, m, l, x
        model_path = self.config.get('model_path', f'yolov8{model_variant}-seg.pt')
        
        logger.info(f"Loading YOLOv8-Seg model: {model_path}")
        
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(model_path)
        )
        
        logger.info("YOLOv8-Seg model loaded successfully")
        
    async def detect(self, frame: np.ndarray):
        """
        Detect objects with pixel-level segmentation masks
        
        Returns detections with segmentation masks
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
            if result.masks is None:
                continue
                
            boxes = result.boxes
            masks = result.masks
            
            for box, mask in zip(boxes, masks):
                # Extract box data
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy().tolist()
                
                # Get class name
                class_name = result.names[class_id] if class_id in result.names else f'class_{class_id}'
                
                # Extract mask data
                mask_data = mask.data[0].cpu().numpy()  # Binary mask
                
                # Calculate mask area and perimeter
                mask_area = int(np.sum(mask_data))
                contours, _ = cv2.findContours(
                    mask_data.astype(np.uint8),
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                perimeter = int(cv2.arcLength(contours[0], True)) if contours else 0
                
                # Get mask polygon (simplified)
                polygon = []
                if contours:
                    # Simplify contour
                    epsilon = 0.01 * cv2.arcLength(contours[0], True)
                    approx = cv2.approxPolyDP(contours[0], epsilon, True)
                    polygon = approx.reshape(-1, 2).tolist()
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox,
                    'mask': mask_data.tolist(),  # Full binary mask
                    'mask_area': mask_area,
                    'mask_perimeter': perimeter,
                    'polygon': polygon,  # Simplified polygon points
                    'detection_type': 'segmentation'
                }
                
                detections.append(detection)
        
        return detections
    
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None


