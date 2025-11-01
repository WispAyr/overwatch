"""
AI Model plugins
"""
import logging
from typing import Optional

from .base import BaseModel
from .ultralytics import UltralyticsModel
from .hailo_yolo import HailoYOLOModel
from .audio_base import AudioBaseModel
from .whisper_model import WhisperModel
from .yamnet_model import YAMNetModel
from .pose_estimation import PoseEstimationModel
from .segmentation import SegmentationModel
from .object_tracking import ObjectTrackingModel
from .face_recognition import FaceRecognitionModel
from .license_plate import LicensePlateModel
from .weapon_detection import WeaponDetectionModel
from .panns_audio import PANNsModel
from .fire_detection import FireDetectionModel
from .ppe_detection import PPEDetectionModel


logger = logging.getLogger('overwatch.models')


# Model registry
MODEL_REGISTRY = {
    # YOLOv8 Object Detection
    'ultralytics-yolov8n': UltralyticsModel,
    'ultralytics-yolov8s': UltralyticsModel,
    'ultralytics-yolov8m': UltralyticsModel,
    'ultralytics-yolov8l': UltralyticsModel,
    'ultralytics-yolov8x': UltralyticsModel,
    
    # Hailo-Accelerated YOLO (13 TOPS on Raspberry Pi)
    'hailo-yolov8s': HailoYOLOModel,
    'hailo-yolov6n': HailoYOLOModel,
    
    # YOLOv8 Pose Estimation
    'yolov8n-pose': PoseEstimationModel,
    'yolov8s-pose': PoseEstimationModel,
    'yolov8m-pose': PoseEstimationModel,
    'yolov8l-pose': PoseEstimationModel,
    'yolov8x-pose': PoseEstimationModel,
    
    # YOLOv8 Instance Segmentation
    'yolov8n-seg': SegmentationModel,
    'yolov8s-seg': SegmentationModel,
    'yolov8m-seg': SegmentationModel,
    'yolov8l-seg': SegmentationModel,
    'yolov8x-seg': SegmentationModel,
    
    # Object Tracking
    'yolov8n-track': ObjectTrackingModel,
    'yolov8s-track': ObjectTrackingModel,
    'yolov8m-track': ObjectTrackingModel,
    'yolov8l-track': ObjectTrackingModel,
    'yolov8x-track': ObjectTrackingModel,
    
    # Face Recognition
    'face-recognition': FaceRecognitionModel,
    'deepface': FaceRecognitionModel,
    
    # License Plate Recognition (ALPR)
    'license-plate-recognition': LicensePlateModel,
    'alpr': LicensePlateModel,
    
    # Weapon Detection
    'weapon-detection': WeaponDetectionModel,
    
    # Fire & Smoke Detection
    'fire-detection': FireDetectionModel,
    'smoke-detection': FireDetectionModel,
    
    # PPE Detection
    'ppe-detection': PPEDetectionModel,
    
    # Audio Models
    'whisper-tiny': WhisperModel,
    'whisper-base': WhisperModel,
    'whisper-small': WhisperModel,
    'whisper-medium': WhisperModel,
    'whisper-large': WhisperModel,
    'yamnet': YAMNetModel,
    'audio-spectrogram-transformer': YAMNetModel,
    'panns-cnn14': PANNsModel,
    'panns': PANNsModel,
}


async def get_model(model_id: str, config: dict) -> Optional[BaseModel]:
    """Get a model instance, automatically using Hailo if available"""
    from core.config import settings
    
    # Auto-convert to Hailo model if Hailo is available
    if settings.USE_HAILO and settings.DEVICE == 'hailo':
        try:
            from core.hailo_detector import convert_model_to_hailo
            original_model_id = model_id
            model_id = convert_model_to_hailo(model_id)
            if model_id != original_model_id:
                logger.info(f"🚀 Using Hailo acceleration: {original_model_id} → {model_id}")
        except Exception as e:
            logger.debug(f"Hailo conversion check failed: {e}")
    
    if model_id not in MODEL_REGISTRY:
        logger.error(f"Unknown model: {model_id}")
        return None
        
    model_class = MODEL_REGISTRY[model_id]
    model = model_class(model_id, config)
    await model.initialize()
    
    return model

