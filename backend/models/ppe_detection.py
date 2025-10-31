"""
PPE Detection Model Plugin
Personal Protective Equipment detection for safety compliance
Detects hard hats, safety vests, masks, gloves, goggles
"""
import asyncio
import logging
from typing import List, Optional, Dict, Set
import numpy as np

from ultralytics import YOLO
from .base import BaseModel


logger = logging.getLogger('overwatch.models.ppe')


class PPEDetectionModel(BaseModel):
    """Detect PPE and identify safety violations"""
    
    # PPE class mappings (customize based on your model)
    PPE_CLASSES = {
        0: 'person',
        1: 'hard_hat',
        2: 'safety_vest',
        3: 'mask',
        4: 'gloves',
        5: 'goggles',
        6: 'safety_shoes'
    }
    
    # Required PPE by zone type (configurable)
    ZONE_REQUIREMENTS = {
        'construction': {'hard_hat', 'safety_vest'},
        'industrial': {'hard_hat', 'safety_vest', 'safety_shoes'},
        'laboratory': {'mask', 'gloves', 'goggles'},
        'medical': {'mask', 'gloves'},
        'warehouse': {'safety_vest'}
    }
    
    async def initialize(self):
        """Initialize PPE detection model"""
        # Use custom trained PPE model or pre-trained from Roboflow
        model_path = self.config.get('model_path', 'yolov8n.pt')
        
        logger.info(f"Loading PPE Detection model: {model_path}")
        
        # Load custom class names if provided
        custom_classes = self.config.get('class_names')
        if custom_classes:
            self.PPE_CLASSES = {i: name for i, name in enumerate(custom_classes)}
        
        # Get zone type for this camera
        self.zone_type = self.config.get('zone_type', 'construction')
        self.required_ppe = set(self.ZONE_REQUIREMENTS.get(self.zone_type, set()))
        
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(model_path)
        )
        
        logger.info(f"PPE Detection loaded for {self.zone_type} zone, requiring: {self.required_ppe}")
        
    async def detect(self, frame: np.ndarray):
        """
        Detect PPE and identify violations
        
        Returns detections with compliance status
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
        
        # Collect all detections
        all_detections = []
        people = []
        ppe_items = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy().tolist()
                
                # Get class name
                if class_id in result.names:
                    class_name = result.names[class_id]
                elif class_id in self.PPE_CLASSES:
                    class_name = self.PPE_CLASSES[class_id]
                else:
                    class_name = f'class_{class_id}'
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox
                }
                
                all_detections.append(detection)
                
                # Separate people from PPE items
                if class_name == 'person':
                    people.append(detection)
                else:
                    ppe_items.append(detection)
        
        # Analyze compliance for each person
        compliance_results = self._analyze_compliance(people, ppe_items)
        
        # Combine all detections with compliance info
        final_detections = []
        
        for detection in all_detections:
            # Add compliance info if it's a person
            if detection['class_name'] == 'person':
                person_id = self._get_person_id(detection, people)
                compliance = compliance_results.get(person_id, {})
                
                detection.update({
                    'compliance': compliance.get('compliant', False),
                    'missing_ppe': compliance.get('missing_ppe', []),
                    'present_ppe': compliance.get('present_ppe', []),
                    'violation_severity': compliance.get('severity', 'none'),
                    'detection_type': 'ppe_person'
                })
                
                # Log violations
                if not compliance.get('compliant', True):
                    logger.warning(
                        f"PPE VIOLATION: Person missing {compliance.get('missing_ppe', [])} "
                        f"(severity: {compliance.get('severity', 'none')})"
                    )
            else:
                detection['detection_type'] = 'ppe_item'
            
            final_detections.append(detection)
        
        return final_detections
    
    def _analyze_compliance(self, people: List[dict], ppe_items: List[dict]) -> Dict[int, dict]:
        """
        Analyze PPE compliance for each person
        
        Returns dict mapping person index to compliance info
        """
        compliance = {}
        
        for i, person in enumerate(people):
            person_bbox = person['bbox']
            
            # Find PPE items near this person
            nearby_ppe = self._find_nearby_ppe(person_bbox, ppe_items)
            
            # Check which required PPE is present
            present_ppe = set(nearby_ppe.keys())
            missing_ppe = self.required_ppe - present_ppe
            
            # Determine compliance
            is_compliant = len(missing_ppe) == 0
            
            # Assess severity
            if not is_compliant:
                if len(missing_ppe) >= len(self.required_ppe):
                    severity = 'critical'  # Missing all PPE
                elif any(item in missing_ppe for item in ['hard_hat', 'mask']):
                    severity = 'high'  # Missing critical items
                else:
                    severity = 'medium'
            else:
                severity = 'none'
            
            compliance[i] = {
                'compliant': is_compliant,
                'missing_ppe': list(missing_ppe),
                'present_ppe': list(present_ppe),
                'severity': severity
            }
        
        return compliance
    
    def _find_nearby_ppe(self, person_bbox: List[float], ppe_items: List[dict]) -> Dict[str, dict]:
        """
        Find PPE items that are close to this person
        
        Returns dict of PPE type -> detection
        """
        nearby = {}
        
        # Calculate person center and size
        px1, py1, px2, py2 = person_bbox
        person_center_x = (px1 + px2) / 2
        person_center_y = (py1 + py2) / 2
        person_height = py2 - py1
        
        # Search radius (1.5x person height)
        search_radius = person_height * 1.5
        
        for ppe in ppe_items:
            ppe_bbox = ppe['bbox']
            ppx1, ppy1, ppx2, ppy2 = ppe_bbox
            ppe_center_x = (ppx1 + ppx2) / 2
            ppe_center_y = (ppy1 + ppy2) / 2
            
            # Calculate distance
            distance = np.sqrt(
                (ppe_center_x - person_center_x)**2 + 
                (ppe_center_y - person_center_y)**2
            )
            
            # If PPE is close enough, associate with person
            if distance < search_radius:
                ppe_type = ppe['class_name']
                
                # Keep closest item of each type
                if ppe_type not in nearby or distance < nearby[ppe_type].get('distance', float('inf')):
                    nearby[ppe_type] = {
                        **ppe,
                        'distance': distance
                    }
        
        return nearby
    
    def _get_person_id(self, person: dict, people: List[dict]) -> int:
        """Get index of person in people list"""
        for i, p in enumerate(people):
            if p['bbox'] == person['bbox']:
                return i
        return 0
    
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None


