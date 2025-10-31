"""
Test that all AI models can be imported without errors
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def test_base_model_imports():
    """Test base model classes can be imported"""
    from models.base import BaseModel
    from models.audio_base import AudioBaseModel
    assert BaseModel is not None
    assert AudioBaseModel is not None


def test_existing_model_imports():
    """Test existing models can be imported"""
    from models.ultralytics import UltralyticsModel
    from models.whisper_model import WhisperModel
    from models.yamnet_model import YAMNetModel
    
    assert UltralyticsModel is not None
    assert WhisperModel is not None
    assert YAMNetModel is not None


def test_new_vision_model_imports():
    """Test new vision models can be imported"""
    from models.pose_estimation import PoseEstimationModel
    from models.segmentation import SegmentationModel
    from models.object_tracking import ObjectTrackingModel
    from models.face_recognition import FaceRecognitionModel
    from models.license_plate import LicensePlateModel
    from models.weapon_detection import WeaponDetectionModel
    from models.fire_detection import FireDetectionModel
    from models.ppe_detection import PPEDetectionModel
    
    assert PoseEstimationModel is not None
    assert SegmentationModel is not None
    assert ObjectTrackingModel is not None
    assert FaceRecognitionModel is not None
    assert LicensePlateModel is not None
    assert WeaponDetectionModel is not None
    assert FireDetectionModel is not None
    assert PPEDetectionModel is not None


def test_new_audio_model_imports():
    """Test new audio models can be imported"""
    from models.panns_audio import PANNsModel
    
    assert PANNsModel is not None


def test_model_registry():
    """Test MODEL_REGISTRY includes all new models"""
    from models import MODEL_REGISTRY
    
    # Check existing models
    assert 'ultralytics-yolov8n' in MODEL_REGISTRY
    assert 'whisper-base' in MODEL_REGISTRY
    assert 'yamnet' in MODEL_REGISTRY
    
    # Check new pose models
    assert 'yolov8n-pose' in MODEL_REGISTRY
    assert 'yolov8s-pose' in MODEL_REGISTRY
    
    # Check new segmentation models
    assert 'yolov8n-seg' in MODEL_REGISTRY
    assert 'yolov8s-seg' in MODEL_REGISTRY
    
    # Check new tracking models
    assert 'yolov8n-track' in MODEL_REGISTRY
    assert 'yolov8s-track' in MODEL_REGISTRY
    
    # Check specialized models
    assert 'face-recognition' in MODEL_REGISTRY
    assert 'alpr' in MODEL_REGISTRY
    assert 'weapon-detection' in MODEL_REGISTRY
    assert 'fire-detection' in MODEL_REGISTRY
    assert 'ppe-detection' in MODEL_REGISTRY
    assert 'panns' in MODEL_REGISTRY
    
    # Count total models
    assert len(MODEL_REGISTRY) >= 38, f"Expected at least 38 models, found {len(MODEL_REGISTRY)}"


def test_model_class_mapping():
    """Test that all model IDs map to valid classes"""
    from models import MODEL_REGISTRY
    from models.base import BaseModel
    from models.audio_base import AudioBaseModel
    
    for model_id, model_class in MODEL_REGISTRY.items():
        # Check that it's a class
        assert isinstance(model_class, type), f"{model_id} does not map to a class"
        
        # Check that it's a subclass of BaseModel or AudioBaseModel
        assert issubclass(model_class, (BaseModel, AudioBaseModel)), \
            f"{model_id} class {model_class} is not a subclass of BaseModel or AudioBaseModel"


def test_get_model_function():
    """Test get_model function exists"""
    from models import get_model
    
    assert get_model is not None
    assert callable(get_model)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


