"""
Workflow Components API
Provides available components for the visual workflow builder
"""
from fastapi import APIRouter, Request
from pathlib import Path
import importlib
import inspect

from models import MODEL_REGISTRY


router = APIRouter()


@router.get("/models")
async def list_available_models():
    """List all available AI models for workflows"""
    models = []
    
    # YOLO base models
    for model_id in MODEL_REGISTRY.keys():
        variant = model_id.split('-')[-1] if '-' in model_id else model_id
        
        model_info = {
            "id": model_id,
            "name": model_id.replace('-', ' ').title(),
            "type": "object_detection",
            "variant": variant,
            "description": f"General object detection - YOLO {variant}",
            "speed": "fast" if 'n' in variant else "medium" if 's' in variant else "slow",
            "accuracy": "medium" if 'n' in variant else "high" if 'm' in variant else "very_high",
            "category": "General Detection"
        }
        models.append(model_info)
    
    # Specialized AI Models for real-world applications
    specialized_models = [
        # People & Crowd
        {
            "id": "face-recognition-v1",
            "name": "Face Recognition",
            "type": "face_recognition",
            "description": "Identify and match faces against database",
            "speed": "medium",
            "accuracy": "high",
            "category": "People Analytics",
            "use_cases": ["Access control", "VIP detection", "Watchlist matching"]
        },
        {
            "id": "crowd-counter-v1",
            "name": "Crowd Counting",
            "type": "crowd_counting",
            "description": "Count people in dense crowds",
            "speed": "fast",
            "accuracy": "high",
            "category": "People Analytics",
            "use_cases": ["Capacity monitoring", "Queue management", "Event monitoring"]
        },
        {
            "id": "age-gender-v1",
            "name": "Age & Gender Estimation",
            "type": "demographic",
            "description": "Estimate age range and gender",
            "speed": "medium",
            "accuracy": "medium",
            "category": "People Analytics",
            "use_cases": ["Demographics", "Marketing analytics", "Restricted area access"]
        },
        
        # Vehicles & Traffic
        {
            "id": "license-plate-reader-v1",
            "name": "License Plate Recognition",
            "type": "lpr_anpr",
            "description": "Read and recognize vehicle license plates",
            "speed": "fast",
            "accuracy": "very_high",
            "category": "Vehicle Analytics",
            "use_cases": ["Parking management", "Access control", "Traffic monitoring", "Stolen vehicle detection"]
        },
        {
            "id": "vehicle-classifier-v1",
            "name": "Vehicle Type Classifier",
            "type": "vehicle_classification",
            "description": "Classify vehicles (car, truck, bus, motorcycle)",
            "speed": "fast",
            "accuracy": "high",
            "category": "Vehicle Analytics",
            "use_cases": ["Traffic analysis", "Parking rules", "Toll classification"]
        },
        {
            "id": "parking-violation-v1",
            "name": "Parking Violation Detector",
            "type": "parking_violation",
            "description": "Detect illegal parking, yellow line violations",
            "speed": "medium",
            "accuracy": "high",
            "category": "Vehicle Analytics",
            "use_cases": ["Parking enforcement", "Loading zone monitoring", "Yellow line violations"]
        },
        {
            "id": "traffic-flow-v1",
            "name": "Traffic Flow Analysis",
            "type": "traffic_analysis",
            "description": "Count vehicles, measure speed, detect congestion",
            "speed": "fast",
            "accuracy": "high",
            "category": "Vehicle Analytics",
            "use_cases": ["Traffic monitoring", "Speed enforcement", "Congestion detection"]
        },
        
        # Safety & Security
        {
            "id": "ppe-detector-v1",
            "name": "PPE Detection",
            "type": "ppe_detection",
            "description": "Detect personal protective equipment (hard hat, vest, mask)",
            "speed": "fast",
            "accuracy": "high",
            "category": "Safety & Compliance",
            "use_cases": ["Construction safety", "Factory compliance", "COVID mask detection"]
        },
        {
            "id": "fire-smoke-detector-v1",
            "name": "Fire & Smoke Detection",
            "type": "fire_smoke",
            "description": "Early detection of fire and smoke",
            "speed": "very_fast",
            "accuracy": "high",
            "category": "Safety & Compliance",
            "use_cases": ["Fire safety", "Industrial monitoring", "Wildfire detection"]
        },
        {
            "id": "fall-detector-v1",
            "name": "Fall Detection",
            "type": "fall_detection",
            "description": "Detect person falling or collapsed",
            "speed": "fast",
            "accuracy": "high",
            "category": "Safety & Compliance",
            "use_cases": ["Elderly care", "Workplace safety", "Hospital monitoring"]
        },
        {
            "id": "weapon-detector-v1",
            "name": "Weapon Detection",
            "type": "weapon_detection",
            "description": "Detect firearms, knives, and weapons",
            "speed": "fast",
            "accuracy": "very_high",
            "category": "Safety & Compliance",
            "use_cases": ["Security screening", "Threat detection", "School safety"]
        },
        
        # Behavior & Anomaly
        {
            "id": "loitering-detector-v1",
            "name": "Loitering Detection",
            "type": "loitering",
            "description": "Detect people staying in area too long",
            "speed": "medium",
            "accuracy": "high",
            "category": "Behavior Analysis",
            "use_cases": ["Perimeter security", "Restricted areas", "Retail loss prevention"]
        },
        {
            "id": "intrusion-detector-v1",
            "name": "Intrusion Detection",
            "type": "intrusion",
            "description": "Detect unauthorized entry into restricted zones",
            "speed": "fast",
            "accuracy": "very_high",
            "category": "Behavior Analysis",
            "use_cases": ["Perimeter security", "After-hours monitoring", "Fence line detection"]
        },
        {
            "id": "violence-detector-v1",
            "name": "Violence Detection",
            "type": "violence",
            "description": "Detect fighting, aggressive behavior",
            "speed": "medium",
            "accuracy": "medium",
            "category": "Behavior Analysis",
            "use_cases": ["Public safety", "Bar/club security", "School monitoring"]
        },
        {
            "id": "left-object-detector-v1",
            "name": "Abandoned Object Detection",
            "type": "abandoned_object",
            "description": "Detect unattended bags or objects",
            "speed": "fast",
            "accuracy": "high",
            "category": "Behavior Analysis",
            "use_cases": ["Airport security", "Train stations", "Public venue safety"]
        },
        {
            "id": "queue-management-v1",
            "name": "Queue Management",
            "type": "queue_analysis",
            "description": "Detect long queues, estimate wait times",
            "speed": "fast",
            "accuracy": "high",
            "category": "Behavior Analysis",
            "use_cases": ["Retail optimization", "Bank/DMV monitoring", "Customer service"]
        },
        
        # Industrial & Specialized
        {
            "id": "social-distancing-v1",
            "name": "Social Distancing Monitor",
            "type": "social_distancing",
            "description": "Monitor social distancing compliance",
            "speed": "fast",
            "accuracy": "high",
            "category": "Health & Compliance",
            "use_cases": ["COVID compliance", "Workplace safety", "Density monitoring"]
        },
        {
            "id": "spill-detector-v1",
            "name": "Spill Detection",
            "type": "spill_detection",
            "description": "Detect liquid spills, slip hazards",
            "speed": "fast",
            "accuracy": "medium",
            "category": "Safety & Compliance",
            "use_cases": ["Retail safety", "Factory monitoring", "Liability prevention"]
        },
        {
            "id": "tampering-detector-v1",
            "name": "Camera Tampering Detection",
            "type": "tampering",
            "description": "Detect camera obstruction or manipulation",
            "speed": "very_fast",
            "accuracy": "very_high",
            "category": "System Health",
            "use_cases": ["Security system integrity", "Vandalism detection"]
        },
        {
            "id": "graffiti-detector-v1",
            "name": "Graffiti Detection",
            "type": "graffiti",
            "description": "Detect vandalism and graffiti",
            "speed": "medium",
            "accuracy": "medium",
            "category": "Vandalism Detection",
            "use_cases": ["Property protection", "Public transit", "Building maintenance"]
        }
    ]
    
    models.extend(specialized_models)
    
    return {"models": models, "total": len(models)}


@router.get("/actions")
async def list_available_actions():
    """List all available action types"""
    actions = [
        {
            "id": "event",
            "name": "Log Event",
            "icon": "📝",
            "description": "Store detection in event log",
            "color": "blue",
            "config": {
                "severity": {"type": "select", "options": ["info", "warning", "critical"]}
            }
        },
        {
            "id": "alert",
            "name": "Alert",
            "icon": "🚨",
            "description": "Send high-priority alert",
            "color": "red",
            "config": {
                "severity": {"type": "select", "options": ["warning", "critical"]},
                "notify": {"type": "text", "placeholder": "security_team"}
            }
        },
        {
            "id": "email",
            "name": "Email Alert",
            "icon": "📧",
            "description": "Send email notification",
            "color": "purple",
            "config": {
                "to": {"type": "email", "placeholder": "security@company.com"},
                "subject": {"type": "text", "default": "Security Alert"},
                "include_snapshot": {"type": "boolean", "default": True}
            }
        },
        {
            "id": "webhook",
            "name": "Webhook",
            "icon": "🔗",
            "description": "HTTP POST to external service",
            "color": "purple",
            "config": {
                "url": {"type": "url", "placeholder": "https://api.example.com/alert"},
                "method": {"type": "select", "options": ["POST", "PUT"]},
                "headers": {"type": "json", "optional": True}
            }
        },
        {
            "id": "record",
            "name": "Record Video",
            "icon": "🎥",
            "description": "Record video clip",
            "color": "orange",
            "config": {
                "duration": {"type": "number", "min": 10, "max": 300, "default": 30},
                "pre_buffer": {"type": "number", "min": 0, "max": 30, "default": 10}
            }
        },
        {
            "id": "snapshot",
            "name": "Save Snapshot",
            "icon": "📸",
            "description": "Capture still image with overlays",
            "color": "pink",
            "config": {
                "draw_boxes": {"type": "boolean", "default": True},
                "quality": {"type": "select", "options": ["low", "medium", "high"], "default": "high"}
            }
        }
    ]
    
    return {"actions": actions}


@router.get("/filters")
async def list_available_filters():
    """List all available filter/zone types"""
    filters = [
        {
            "id": "zone_polygon",
            "name": "Detection Zone",
            "icon": "📐",
            "description": "Define polygon area for detection",
            "color": "yellow",
            "config": {
                "polygon": {
                    "type": "polygon",
                    "placeholder": "[[100,100],[500,100],[500,400],[100,400]]"
                },
                "name": {"type": "text", "placeholder": "entrance_zone"}
            }
        },
        {
            "id": "confidence_filter",
            "name": "Confidence Filter",
            "icon": "🎯",
            "description": "Minimum confidence threshold",
            "color": "yellow",
            "config": {
                "min_confidence": {"type": "slider", "min": 0, "max": 1, "step": 0.05, "default": 0.7}
            }
        },
        {
            "id": "class_filter",
            "name": "Class Filter",
            "icon": "🏷️",
            "description": "Filter by object class",
            "color": "yellow",
            "config": {
                "classes": {
                    "type": "multiselect",
                    "options": ["person", "car", "truck", "bicycle", "motorcycle", "bus"]
                }
            }
        },
        {
            "id": "temporal_filter",
            "name": "Temporal Filter",
            "icon": "⏰",
            "description": "Time-based filtering",
            "color": "yellow",
            "config": {
                "dwell_time": {"type": "number", "min": 0, "max": 300, "default": 5, "unit": "seconds"},
                "cooldown": {"type": "number", "min": 0, "max": 3600, "default": 60, "unit": "seconds"}
            }
        }
    ]
    
    return {"filters": filters}


@router.get("/classes")
async def list_object_classes():
    """List all available object detection classes (COCO dataset)"""
    coco_classes = [
        {"id": 0, "name": "person"},
        {"id": 1, "name": "bicycle"},
        {"id": 2, "name": "car"},
        {"id": 3, "name": "motorcycle"},
        {"id": 5, "name": "bus"},
        {"id": 7, "name": "truck"},
        {"id": 14, "name": "bird"},
        {"id": 15, "name": "cat"},
        {"id": 16, "name": "dog"},
        {"id": 24, "name": "backpack"},
        {"id": 26, "name": "handbag"},
        {"id": 28, "name": "suitcase"},
        {"id": 39, "name": "bottle"},
        {"id": 41, "name": "cup"},
        {"id": 56, "name": "chair"},
        {"id": 62, "name": "tv"},
        {"id": 63, "name": "laptop"},
        {"id": 67, "name": "cell phone"},
    ]
    
    return {"classes": coco_classes}


@router.get("/examples")
async def get_configuration_examples():
    """Get working configuration examples for AI models and actions"""
    import json
    
    examples_file = Path("config/model_examples.json")
    
    if examples_file.exists():
        with open(examples_file, 'r') as f:
            return json.load(f)
    
    # Fallback examples if file doesn't exist
    return {
        "examples": [
            {
                "name": "Person Detection - Standard",
                "modelId": "ultralytics-yolov8n",
                "config": {"confidence": 0.7, "classes": [0], "fps": 10}
            }
        ],
        "action_examples": []
    }


@router.get("/audio-models")
async def list_audio_models():
    """List available audio AI models for transcription and sound classification"""
    models = [
        # Whisper Models (Speech-to-Text)
        {
            "id": "whisper-tiny",
            "name": "Whisper Tiny",
            "type": "transcription",
            "description": "Fastest Whisper model, 39M parameters",
            "speed": "very fast",
            "accuracy": "good",
            "languages": 99,
            "use_cases": ["Real-time transcription", "Low latency", "Edge devices"]
        },
        {
            "id": "whisper-base",
            "name": "Whisper Base",
            "type": "transcription",
            "description": "Balanced Whisper model, 74M parameters",
            "speed": "fast",
            "accuracy": "very good",
            "languages": 99,
            "use_cases": ["General transcription", "Meeting notes", "Voice commands"]
        },
        {
            "id": "whisper-small",
            "name": "Whisper Small",
            "type": "transcription",
            "description": "High quality Whisper model, 244M parameters",
            "speed": "medium",
            "accuracy": "excellent",
            "languages": 99,
            "use_cases": ["Professional transcription", "Subtitles", "Accessibility"]
        },
        {
            "id": "whisper-medium",
            "name": "Whisper Medium",
            "type": "transcription",
            "description": "Very high quality, 769M parameters",
            "speed": "slow",
            "accuracy": "near perfect",
            "languages": 99,
            "use_cases": ["Legal transcription", "Medical notes", "Archives"]
        },
        {
            "id": "whisper-large",
            "name": "Whisper Large",
            "type": "transcription",
            "description": "Best quality, 1550M parameters",
            "speed": "very slow",
            "accuracy": "state of the art",
            "languages": 99,
            "use_cases": ["Forensics", "Research", "Maximum accuracy"]
        },
        
        # Sound Classification Models
        {
            "id": "yamnet",
            "name": "YAMNet",
            "type": "sound_classification",
            "description": "Google's audio event detection, 521 classes",
            "speed": "fast",
            "accuracy": "good",
            "classes": 521,
            "use_cases": ["Gunshot detection", "Glass breaking", "Alarm sounds", "Environmental monitoring"]
        },
        {
            "id": "audio-spectrogram-transformer",
            "name": "Audio Spectrogram Transformer",
            "type": "sound_classification",
            "description": "Transformer-based audio classification",
            "speed": "medium",
            "accuracy": "excellent",
            "classes": 527,
            "use_cases": ["Complex sound scenes", "Music classification", "Environmental analysis"]
        },
        {
            "id": "panns-cnn14",
            "name": "PANNs CNN14",
            "type": "sound_classification",
            "description": "Pre-trained audio neural networks",
            "speed": "medium",
            "accuracy": "very good",
            "classes": 527,
            "use_cases": ["Security alerts", "Industrial monitoring", "Smart home"]
        },
    ]
    
    return {"models": models}

