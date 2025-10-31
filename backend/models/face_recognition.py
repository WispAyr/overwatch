"""
Face Recognition Model Plugin
Face detection and identification using DeepFace
"""
import asyncio
import logging
from typing import List, Optional
from pathlib import Path
import numpy as np

from .base import BaseModel


logger = logging.getLogger('overwatch.models.face')


class FaceRecognitionModel(BaseModel):
    """Face recognition and identification using DeepFace"""
    
    async def initialize(self):
        """Initialize DeepFace model"""
        logger.info("Loading DeepFace model...")
        
        try:
            # Import DeepFace
            from deepface import DeepFace
            self.DeepFace = DeepFace
            
            # Create face database directory
            self.face_db = Path(self.config.get('face_db_path', 'data/faces'))
            self.face_db.mkdir(parents=True, exist_ok=True)
            
            # Model configuration
            self.model_name = self.config.get('model_name', 'Facenet')  # Facenet, VGG-Face, ArcFace
            self.detector_backend = self.config.get('detector_backend', 'opencv')  # opencv, ssd, mtcnn, retinaface
            
            logger.info(f"DeepFace initialized with model={self.model_name}, detector={self.detector_backend}")
            
        except ImportError:
            logger.error("DeepFace not installed. Install with: pip install deepface")
            raise
        
    async def detect(self, frame: np.ndarray):
        """
        Detect and recognize faces in frame
        
        Returns detections with face identity and attributes
        """
        if not hasattr(self, 'DeepFace'):
            logger.error("DeepFace not initialized")
            return []
        
        # Run detection in executor
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            None,
            self._process_faces,
            frame
        )
        
        return detections
    
    def _process_faces(self, frame: np.ndarray) -> List[dict]:
        """Process faces (blocking operation)"""
        try:
            # Detect faces with attributes
            faces = self.DeepFace.extract_faces(
                frame,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=True
            )
            
            detections = []
            
            for i, face_data in enumerate(faces):
                # Get facial area
                facial_area = face_data.get('facial_area', {})
                bbox = [
                    facial_area.get('x', 0),
                    facial_area.get('y', 0),
                    facial_area.get('x', 0) + facial_area.get('w', 0),
                    facial_area.get('y', 0) + facial_area.get('h', 0)
                ]
                
                confidence = float(face_data.get('confidence', 0))
                
                # Try to identify face
                identity = 'Unknown'
                identity_confidence = 0.0
                
                if self.face_db.exists() and any(self.face_db.iterdir()):
                    try:
                        # Search in face database
                        results = self.DeepFace.find(
                            img_path=frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])],
                            db_path=str(self.face_db),
                            model_name=self.model_name,
                            detector_backend=self.detector_backend,
                            enforce_detection=False,
                            silent=True
                        )
                        
                        if len(results) > 0 and len(results[0]) > 0:
                            # Get best match
                            match = results[0].iloc[0]
                            identity_path = Path(match['identity'])
                            identity = identity_path.parent.name  # Folder name = person name
                            
                            # Convert distance to confidence (lower distance = higher confidence)
                            distance = match.get('distance', 1.0)
                            identity_confidence = max(0.0, 1.0 - distance)
                            
                    except Exception as e:
                        logger.debug(f"Face identification error: {e}")
                
                # Analyze face attributes (age, gender, emotion)
                attributes = {}
                try:
                    analysis = self.DeepFace.analyze(
                        img_path=frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])],
                        actions=['age', 'gender', 'emotion'],
                        detector_backend=self.detector_backend,
                        enforce_detection=False,
                        silent=True
                    )
                    
                    if isinstance(analysis, list) and len(analysis) > 0:
                        analysis = analysis[0]
                    
                    attributes = {
                        'age': analysis.get('age'),
                        'gender': analysis.get('dominant_gender'),
                        'gender_confidence': analysis.get('gender', {}).get(analysis.get('dominant_gender', 'Man'), 0),
                        'emotion': analysis.get('dominant_emotion'),
                        'emotion_confidence': analysis.get('emotion', {}).get(analysis.get('dominant_emotion', 'neutral'), 0)
                    }
                    
                except Exception as e:
                    logger.debug(f"Face analysis error: {e}")
                
                detection = {
                    'class_id': i,
                    'class_name': f'face_{identity}',
                    'confidence': confidence,
                    'bbox': bbox,
                    'identity': identity,
                    'identity_confidence': identity_confidence,
                    'attributes': attributes,
                    'detection_type': 'face'
                }
                
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup model resources"""
        if hasattr(self, 'DeepFace'):
            delattr(self, 'DeepFace')


