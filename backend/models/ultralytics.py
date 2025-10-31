"""
Ultralytics YOLO Model Plugin
"""
import asyncio
import logging
from typing import List
from pathlib import Path

import numpy as np
import torch
from ultralytics import YOLO

from core.config import settings
from .base import BaseModel, Detection


logger = logging.getLogger('overwatch.models.ultralytics')


class UltralyticsModel(BaseModel):
    """Ultralytics YOLO model plugin"""
    
    # COCO class names
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    def __init__(self, model_id: str, config: dict):
        super().__init__(model_id, config)
        self.device = settings.DEVICE
        
    async def initialize(self):
        """Initialize YOLO model"""
        logger.info(f"Loading {self.model_id}...")
        
        # Determine model variant
        variant = self.model_id.split('-')[-1]  # e.g., 'yolov8n'
        model_file = f"{variant}.pt"
        
        # Model path
        model_path = Path(settings.MODEL_CACHE_DIR) / model_file
        
        # Load model in executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            self._load_model,
            str(model_path)
        )
        
        logger.info(f"Loaded {self.model_id} on {self.device}")
        
    def _load_model(self, model_path: str) -> YOLO:
        """Load YOLO model (blocking operation)"""
        model = YOLO(model_path)
        
        # Move to device
        if self.device == 'cuda' and torch.cuda.is_available():
            model.to('cuda')
        else:
            model.to('cpu')
            
        return model
        
    async def detect(self, frame: np.ndarray) -> List[dict]:
        """Run YOLO detection"""
        if self.model is None:
            logger.error("Model not initialized")
            return []
            
        # Run inference in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._run_inference,
            frame
        )
        
        return results
        
    def _run_inference(self, frame: np.ndarray) -> List[dict]:
        """Run inference (blocking operation)"""
        # Run YOLO
        results = self.model(frame, verbose=False)
        
        detections = []
        
        # Parse results
        for result in results:
            boxes = result.boxes
            
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy().tolist()
                
                # Get class name
                class_name = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else f"class_{class_id}"
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox  # [x1, y1, x2, y2]
                }
                
                detections.append(detection)
                
        return detections
        
    async def cleanup(self):
        """Cleanup model"""
        if self.model:
            del self.model
            self.model = None
            
            # Clear CUDA cache if using GPU
            if self.device == 'cuda' and torch.cuda.is_available():
                torch.cuda.empty_cache()

