"""
License Plate Recognition Model Plugin
Automatic License Plate Recognition (ALPR) using YOLOv8 + EasyOCR
"""
import asyncio
import logging
from typing import List, Optional
import numpy as np
import re

from .base import BaseModel


logger = logging.getLogger('overwatch.models.alpr')


class LicensePlateModel(BaseModel):
    """Automatic License Plate Recognition (ALPR)"""
    
    async def initialize(self):
        """Initialize plate detector and OCR reader"""
        logger.info("Loading License Plate Recognition model...")
        
        try:
            # Import dependencies
            import easyocr
            from ultralytics import YOLO
            
            self.YOLO = YOLO
            self.easyocr = easyocr
            
            # Load plate detector (can use generic YOLOv8 or custom trained)
            detector_path = self.config.get('detector_path', 'yolov8n.pt')
            
            loop = asyncio.get_event_loop()
            self.detector = await loop.run_in_executor(
                None,
                lambda: YOLO(detector_path)
            )
            
            # Load OCR reader
            languages = self.config.get('languages', ['en'])
            use_gpu = self.config.get('use_gpu', True)
            
            self.reader = await loop.run_in_executor(
                None,
                lambda: easyocr.Reader(languages, gpu=use_gpu)
            )
            
            logger.info("License Plate Recognition initialized successfully")
            
        except ImportError as e:
            logger.error(f"Missing dependency: {e}. Install with: pip install easyocr")
            raise
        
    async def detect(self, frame: np.ndarray):
        """
        Detect license plates and read text
        
        Returns detections with plate numbers
        """
        if not hasattr(self, 'detector') or not hasattr(self, 'reader'):
            logger.error("Model not initialized")
            return []
        
        # Run detection in executor
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            None,
            self._process_plates,
            frame
        )
        
        return detections
    
    def _process_plates(self, frame: np.ndarray) -> List[dict]:
        """Process license plates (blocking operation)"""
        try:
            # Detect vehicles/objects that might have plates
            # Filter for cars, trucks, buses
            vehicle_classes = self.config.get('vehicle_classes', [2, 5, 7])  # car, bus, truck in COCO
            
            results = self.detector(
                frame,
                conf=self.config.get('confidence', 0.5),
                classes=vehicle_classes,
                verbose=False
            )
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for box in boxes:
                    # Get vehicle bounding box
                    vehicle_bbox = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, vehicle_bbox)
                    
                    # Expand box slightly to catch plates
                    h, w = frame.shape[:2]
                    expand = 0.1  # 10% expansion
                    x1 = max(0, int(x1 - (x2-x1)*expand))
                    y1 = max(0, int(y1 - (y2-y1)*expand))
                    x2 = min(w, int(x2 + (x2-x1)*expand))
                    y2 = min(h, int(y2 + (y2-y1)*expand))
                    
                    # Crop vehicle region
                    vehicle_img = frame[y1:y2, x1:x2]
                    
                    # Read text with OCR
                    ocr_results = self.reader.readtext(
                        vehicle_img,
                        detail=1,
                        paragraph=False
                    )
                    
                    # Process OCR results
                    for detection_data in ocr_results:
                        bbox_points, text, confidence = detection_data
                        
                        # Filter for plate-like text patterns
                        if self._is_plate_like(text):
                            # Convert relative bbox to absolute
                            abs_bbox = self._convert_bbox(bbox_points, x1, y1)
                            
                            # Clean plate text
                            plate_number = self._clean_plate_text(text)
                            
                            detection = {
                                'class_id': 0,
                                'class_name': 'license_plate',
                                'confidence': float(confidence),
                                'bbox': abs_bbox,
                                'plate_number': plate_number,
                                'raw_text': text,
                                'vehicle_bbox': vehicle_bbox.tolist(),
                                'detection_type': 'license_plate'
                            }
                            
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"License plate detection error: {e}")
            return []
    
    def _is_plate_like(self, text: str) -> bool:
        """Check if text looks like a license plate"""
        # Remove spaces and special chars
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Must have both letters and numbers
        has_letter = bool(re.search(r'[A-Z]', clean))
        has_number = bool(re.search(r'[0-9]', clean))
        
        # Reasonable length for a plate
        min_length = self.config.get('min_plate_length', 4)
        max_length = self.config.get('max_plate_length', 10)
        
        return has_letter and has_number and min_length <= len(clean) <= max_length
    
    def _clean_plate_text(self, text: str) -> str:
        """Clean and normalize plate text"""
        # Remove spaces and special characters
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Common OCR corrections
        replacements = {
            'O': '0',  # O -> 0 in numbers
            'I': '1',  # I -> 1 in numbers
            'S': '5',  # S -> 5 sometimes
        }
        
        # Apply selective replacements based on context
        # This is basic - can be improved with ML
        
        return clean
    
    def _convert_bbox(self, points, offset_x, offset_y) -> List[float]:
        """Convert OCR bbox points to absolute coordinates"""
        # Get bounding rectangle from points
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        return [
            float(min(x_coords) + offset_x),
            float(min(y_coords) + offset_y),
            float(max(x_coords) + offset_x),
            float(max(y_coords) + offset_y)
        ]
    
    async def cleanup(self):
        """Cleanup model resources"""
        if hasattr(self, 'detector'):
            del self.detector
        if hasattr(self, 'reader'):
            del self.reader


