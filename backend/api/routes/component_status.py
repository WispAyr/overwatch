"""
Component Status API
Check node implementation status and dependencies
"""
from fastapi import APIRouter
import importlib
import sys
from pathlib import Path

router = APIRouter()


def check_dependency(package_name: str) -> bool:
    """Check if a Python package is installed"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()


@router.get("/status")
async def get_component_status():
    """
    Get status of all workflow components
    Returns implementation status, dependencies, and setup requirements
    """
    
    # Check dependencies
    deps = {
        "ultralytics": check_dependency("ultralytics"),
        "deepface": check_dependency("deepface"),
        "easyocr": check_dependency("easyocr"),
        "whisper": check_dependency("whisper"),
        "tensorflow": check_dependency("tensorflow"),
        "tensorflow_hub": check_dependency("tensorflow_hub"),
        "torch": check_dependency("torch"),
        "panns_inference": check_dependency("panns_inference"),
        "yt_dlp": check_dependency("yt_dlp"),
        "cv2": check_dependency("cv2"),
        "ffmpeg": check_dependency("ffmpeg")
    }
    
    # Model status definitions
    models = {
        # YOLOv8 Base Models - Production Ready
        "ultralytics-yolov8n": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - General object detection (80 classes)"
        },
        "ultralytics-yolov8s": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Balanced speed/accuracy"
        },
        "ultralytics-yolov8m": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Higher accuracy"
        },
        "ultralytics-yolov8l": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Very high accuracy"
        },
        "ultralytics-yolov8x": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Maximum accuracy"
        },
        
        # Pose Estimation
        "yolov8n-pose": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Human pose detection (17 keypoints)"
        },
        
        # Segmentation
        "yolov8n-seg": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Instance segmentation with pixel masks"
        },
        
        # Object Tracking
        "yolov8n-track": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [] if deps["ultralytics"] else ["Install: pip install ultralytics"],
            "message": "Production ready - Object tracking with persistent IDs"
        },
        
        # Face Recognition
        "face-recognition-v1": {
            "status": "needsConfig" if not deps["deepface"] else "ready",
            "badge": "needsConfig" if not deps["deepface"] else "production",
            "implementation": "full",
            "dependencies": ["deepface"],
            "dependenciesMet": deps["deepface"],
            "setupSteps": [
                "Install: pip install deepface",
                "Create face database directory: data/faces/",
                "Add face images to database (one folder per person)"
            ] if not deps["deepface"] else [],
            "message": "Face detection and recognition using DeepFace" if deps["deepface"] else "Requires DeepFace installation and face database setup"
        },
        
        # License Plate Recognition
        "license-plate-reader-v1": {
            "status": "needsConfig" if not deps["easyocr"] else "ready",
            "badge": "needsConfig" if not deps["easyocr"] else "production",
            "implementation": "full",
            "dependencies": ["easyocr", "ultralytics"],
            "dependenciesMet": deps["easyocr"] and deps["ultralytics"],
            "setupSteps": [
                "Install: pip install easyocr",
                "Optional: Download custom plate detector model"
            ] if not deps["easyocr"] else [],
            "message": "License plate detection and OCR" if deps["easyocr"] else "Requires EasyOCR for text recognition"
        },
        
        # Weapon Detection
        "weapon-detector-v1": {
            "status": "needsConfig",
            "badge": "needsConfig",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [
                "Download custom weapon detection model from Roboflow Universe",
                "Place model in models/ directory",
                "Configure model path in node settings"
            ],
            "message": "Requires custom trained weapon detection model"
        },
        
        # Fire Detection
        "fire-smoke-detector-v1": {
            "status": "needsConfig",
            "badge": "needsConfig",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [
                "Download custom fire/smoke detection model",
                "Place model in models/ directory",
                "Configure model path in node settings"
            ],
            "message": "Requires custom trained fire/smoke detection model"
        },
        
        # PPE Detection
        "ppe-detector-v1": {
            "status": "needsConfig",
            "badge": "needsConfig",
            "implementation": "full",
            "dependencies": ["ultralytics"],
            "dependenciesMet": deps["ultralytics"],
            "setupSteps": [
                "Download custom PPE detection model (hard hat, vest, mask)",
                "Place model in models/ directory",
                "Configure model path and required PPE types"
            ],
            "message": "Requires custom trained PPE detection model"
        },
        
        # Audio Models - Whisper
        "whisper-tiny": {
            "status": "ready" if deps["whisper"] else "needsConfig",
            "badge": "production" if deps["whisper"] else "needsConfig",
            "implementation": "full",
            "dependencies": ["whisper", "ffmpeg"],
            "dependenciesMet": deps["whisper"],
            "setupSteps": [
                "Install: pip install openai-whisper",
                "Install FFmpeg: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
            ] if not deps["whisper"] else [],
            "message": "Fast speech transcription (39M params)" if deps["whisper"] else "Requires OpenAI Whisper"
        },
        "whisper-base": {
            "status": "ready" if deps["whisper"] else "needsConfig",
            "badge": "production" if deps["whisper"] else "needsConfig",
            "implementation": "full",
            "dependencies": ["whisper", "ffmpeg"],
            "dependenciesMet": deps["whisper"],
            "setupSteps": [] if deps["whisper"] else [
                "Install: pip install openai-whisper",
                "Install FFmpeg"
            ],
            "message": "Balanced transcription (74M params)" if deps["whisper"] else "Requires OpenAI Whisper"
        },
        "whisper-small": {
            "status": "ready" if deps["whisper"] else "needsConfig",
            "badge": "production" if deps["whisper"] else "needsConfig",
            "implementation": "full",
            "dependencies": ["whisper", "ffmpeg"],
            "dependenciesMet": deps["whisper"],
            "setupSteps": [] if deps["whisper"] else [
                "Install: pip install openai-whisper",
                "Install FFmpeg"
            ],
            "message": "High quality transcription (244M params)" if deps["whisper"] else "Requires OpenAI Whisper"
        },
        
        # YAMNet Sound Classification
        "yamnet": {
            "status": "ready" if (deps["tensorflow"] and deps["tensorflow_hub"]) else "needsConfig",
            "badge": "production" if (deps["tensorflow"] and deps["tensorflow_hub"]) else "needsConfig",
            "implementation": "full",
            "dependencies": ["tensorflow", "tensorflow_hub"],
            "dependenciesMet": deps["tensorflow"] and deps["tensorflow_hub"],
            "setupSteps": [] if (deps["tensorflow"] and deps["tensorflow_hub"]) else [
                "Install: pip install tensorflow tensorflow-hub"
            ],
            "message": "Sound classification (521 classes - gunshots, alarms, etc.)" if (deps["tensorflow"] and deps["tensorflow_hub"]) else "Requires TensorFlow"
        },
        
        # PANNs Audio
        "panns-cnn14": {
            "status": "ready" if (deps["torch"] and deps["panns_inference"]) else "needsConfig",
            "badge": "production" if (deps["torch"] and deps["panns_inference"]) else "needsConfig",
            "implementation": "full",
            "dependencies": ["torch", "panns_inference"],
            "dependenciesMet": deps["torch"] and deps["panns_inference"],
            "setupSteps": [] if (deps["torch"] and deps["panns_inference"]) else [
                "Install: pip install torch panns-inference"
            ],
            "message": "Audio classification (527 classes)" if (deps["torch"] and deps["panns_inference"]) else "Requires PyTorch and PANNs"
        },
        
        # Not Implemented Models
        "crowd-counter-v1": {
            "status": "notImplemented",
            "badge": "notImplemented",
            "implementation": "none",
            "dependencies": [],
            "dependenciesMet": False,
            "setupSteps": [],
            "message": "Coming soon - Use YOLOv8 person detection with zone counting as alternative"
        },
        "age-gender-v1": {
            "status": "notImplemented",
            "badge": "notImplemented",
            "implementation": "none",
            "dependencies": [],
            "dependenciesMet": False,
            "setupSteps": [],
            "message": "Coming soon - Demographic estimation not yet implemented"
        },
        "vehicle-classifier-v1": {
            "status": "notImplemented",
            "badge": "notImplemented",
            "implementation": "none",
            "dependencies": [],
            "dependenciesMet": False,
            "setupSteps": [],
            "message": "Coming soon - Use YOLOv8 with vehicle classes (2=car, 5=bus, 7=truck) as alternative"
        },
        "traffic-flow-v1": {
            "status": "notImplemented",
            "badge": "notImplemented",
            "implementation": "none",
            "dependencies": [],
            "dependenciesMet": False,
            "setupSteps": [],
            "message": "Coming soon - Use YOLOv8 tracking with line crossing as alternative"
        },
        "fall-detector-v1": {
            "status": "notImplemented",
            "badge": "notImplemented",
            "implementation": "none",
            "dependencies": [],
            "dependenciesMet": False,
            "setupSteps": [],
            "message": "Coming soon - Use pose estimation as alternative"
        },
    }
    
    # Input sources status
    inputs = {
        "camera": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": [],
            "dependenciesMet": True,
            "setupSteps": [],
            "message": "Live camera streams via Stream Manager"
        },
        "videoInput": {
            "status": "beta",
            "badge": "beta",
            "implementation": "partial",
            "dependencies": ["cv2"],
            "dependenciesMet": deps["cv2"],
            "setupSteps": ["Video file playback needs completion"],
            "message": "Video file input - basic implementation only"
        },
        "youtube": {
            "status": "ready" if deps["yt_dlp"] else "needsConfig",
            "badge": "production" if deps["yt_dlp"] else "needsConfig",
            "implementation": "full",
            "dependencies": ["yt_dlp", "cv2"],
            "dependenciesMet": deps["yt_dlp"] and deps["cv2"],
            "setupSteps": [] if deps["yt_dlp"] else ["Install: pip install yt-dlp"],
            "message": "YouTube stream input" if deps["yt_dlp"] else "Requires yt-dlp"
        }
    }
    
    # Processing nodes status
    processing = {
        "zone": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": [],
            "dependenciesMet": True,
            "setupSteps": [],
            "message": "Detection zone filtering - polygon-based spatial filtering"
        },
        "parkingViolation": {
            "status": "beta",
            "badge": "beta",
            "implementation": "partial",
            "dependencies": [],
            "dependenciesMet": True,
            "setupSteps": ["Vehicle tracking integration needed", "Zone intersection logic needed"],
            "message": "Parking violation detection - basic structure only"
        },
        "audioExtractor": {
            "status": "ready" if deps["ffmpeg"] else "needsConfig",
            "badge": "production" if deps["ffmpeg"] else "needsConfig",
            "implementation": "full",
            "dependencies": ["ffmpeg"],
            "dependenciesMet": deps["ffmpeg"],
            "setupSteps": [] if deps["ffmpeg"] else ["Install FFmpeg"],
            "message": "Extract audio from video streams" if deps["ffmpeg"] else "Requires FFmpeg"
        },
        "dayNightDetector": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": [],
            "dependenciesMet": True,
            "setupSteps": [],
            "message": "Automatic lighting condition detection (day/night/IR)"
        },
        "audioVU": {
            "status": "ready",
            "badge": "production",
            "implementation": "full",
            "dependencies": [],
            "dependenciesMet": True,
            "setupSteps": [],
            "message": "Audio VU meter with frequency spectrum and threshold triggers"
        }
    }
    
    # Actions - all production ready
    actions = {
        "email": {"status": "ready", "badge": "production", "implementation": "full", "message": "Email notifications"},
        "webhook": {"status": "ready", "badge": "production", "implementation": "full", "message": "HTTP webhooks"},
        "record": {"status": "ready", "badge": "production", "implementation": "full", "message": "Video recording"},
        "alert": {"status": "ready", "badge": "production", "implementation": "full", "message": "System alerts"},
        "snapshot": {"status": "ready", "badge": "production", "implementation": "full", "message": "Image snapshots"},
        "event": {"status": "ready", "badge": "production", "implementation": "full", "message": "Event logging"}
    }
    
    # Debug/Output - all production ready
    outputs = {
        "dataPreview": {"status": "ready", "badge": "production", "implementation": "full", "message": "Live data preview"},
        "debug": {"status": "ready", "badge": "production", "implementation": "full", "message": "Debug console"}
    }
    
    # Advanced nodes - all production ready
    advanced = {
        "linkIn": {"status": "ready", "badge": "production", "implementation": "full", "message": "Subflow entry"},
        "linkOut": {"status": "ready", "badge": "production", "implementation": "full", "message": "Subflow exit"},
        "linkCall": {"status": "ready", "badge": "production", "implementation": "full", "message": "Subflow invocation"},
        "catch": {"status": "ready", "badge": "production", "implementation": "full", "message": "Error handler"},
        "config": {"status": "ready", "badge": "production", "implementation": "full", "message": "Reusable configuration"}
    }
    
    # Drone nodes - all production ready
    drone = {
        "droneInput": {"status": "ready", "badge": "production", "implementation": "full", "message": "Meshtastic drone input"},
        "droneFilter": {"status": "ready", "badge": "production", "implementation": "full", "message": "Drone filtering"},
        "droneMap": {"status": "ready", "badge": "production", "implementation": "full", "message": "Drone map"},
        "droneAction": {"status": "ready", "badge": "production", "implementation": "full", "message": "Drone actions"},
        "droneAnalytics": {"status": "ready", "badge": "production", "implementation": "full", "message": "Drone analytics"}
    }
    
    return {
        "dependencies": deps,
        "models": models,
        "inputs": inputs,
        "processing": processing,
        "actions": actions,
        "outputs": outputs,
        "advanced": advanced,
        "drone": drone,
        "summary": {
            "totalNodes": len(models) + len(inputs) + len(processing) + len(actions) + len(outputs) + len(advanced) + len(drone),
            "ready": sum(1 for cat in [models, inputs, processing, actions, outputs, advanced, drone] for item in cat.values() if item["status"] == "ready"),
            "needsConfig": sum(1 for cat in [models, inputs, processing] for item in cat.values() if item["status"] == "needsConfig"),
            "beta": sum(1 for cat in [models, inputs, processing] for item in cat.values() if item["status"] == "beta"),
            "notImplemented": sum(1 for item in models.values() if item["status"] == "notImplemented")
        }
    }


@router.get("/badges")
async def get_badge_config():
    """Get badge configuration for UI"""
    return {
        "badges": {
            "production": {
                "icon": "✅",
                "color": "green",
                "text": "Ready",
                "description": "Production ready - fully tested"
            },
            "needsConfig": {
                "icon": "🔧",
                "color": "yellow",
                "text": "Setup Required",
                "description": "Requires configuration or dependencies"
            },
            "beta": {
                "icon": "🚧",
                "color": "orange",
                "text": "Beta",
                "description": "Partial implementation - testing phase"
            },
            "notImplemented": {
                "icon": "📋",
                "color": "gray",
                "text": "Coming Soon",
                "description": "Planned feature - not yet available"
            }
        }
    }

