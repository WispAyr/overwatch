# AI Models Guide

## Currently Integrated

### Vision Models

✅ **Ultralytics YOLOv8** (5 variants)
- YOLOv8n/s/m/l/x for object detection
- 80 COCO classes (people, vehicles, objects)

✅ **YOLOv8-Pose** (5 variants)
- YOLOv8n/s/m/l/x-pose for pose estimation
- 17 keypoint tracking (COCO format)
- Fall detection, activity recognition
- Use in workflows: `yolov8n-pose`, `yolov8s-pose`, etc.

✅ **YOLOv8-Seg** (5 variants)
- YOLOv8n/s/m/l/x-seg for instance segmentation
- Pixel-perfect object masks
- Precise area detection
- Use in workflows: `yolov8n-seg`, `yolov8s-seg`, etc.

✅ **Object Tracking** (ByteTrack/BoT-SORT)
- Persistent object IDs across frames
- Track movement and paths
- Dwell time analysis
- Use in workflows: `yolov8n-track`, `yolov8s-track`, etc.

✅ **Face Recognition** (DeepFace)
- Face detection and identification
- Age, gender, emotion analysis
- Face database matching
- Use in workflows: `face-recognition` or `deepface`

✅ **License Plate Recognition** (ALPR)
- YOLOv8 + EasyOCR
- Vehicle detection + plate reading
- Automatic plate number extraction
- Use in workflows: `license-plate-recognition` or `alpr`

✅ **Weapon Detection**
- Detect guns, knives, weapons
- Critical security alerts
- High confidence threshold
- Use in workflows: `weapon-detection`

✅ **Fire & Smoke Detection**
- ML + color-based detection
- Early warning system
- Severity assessment
- Use in workflows: `fire-detection` or `smoke-detection`

✅ **PPE Detection**
- Personal Protective Equipment compliance
- Hard hats, vests, masks, gloves
- Safety violation alerts
- Use in workflows: `ppe-detection`

### Audio Models

✅ **Whisper** (5 variants)
- Speech-to-text transcription
- Multi-language support
- Use in workflows: `whisper-tiny`, `whisper-base`, `whisper-small`, `whisper-medium`, `whisper-large`

✅ **YAMNet**
- Google's sound classification model
- 521 audio event classes
- General audio classification
- Use in workflows: `yamnet`

✅ **PANNs** (Pretrained Audio Neural Networks)
- Advanced audio event detection
- Gunshot, glass breaking, alarms
- Superior for security events
- Use in workflows: `panns` or `panns-cnn14`

## Additional Models Available to Add

### 1. **Face Recognition**
**Use Cases**: Access control, person identification, VIP detection

**Models**:
- **DeepFace** - Face recognition and analysis
- **FaceNet** - Face embeddings
- **InsightFace** - State-of-the-art face recognition
- **RetinaFace** - Face detection

**Integration**:
```python
# backend/models/face_recognition.py
from deepface import DeepFace
from .base import BaseModel

class FaceRecognitionModel(BaseModel):
    async def detect(self, frame):
        faces = DeepFace.find(frame, db_path="faces/")
        return self.format_detections(faces)

# Register
MODEL_REGISTRY['deepface'] = FaceRecognitionModel
```

### 2. **License Plate Recognition (ALPR)**
**Use Cases**: Parking management, access control, vehicle tracking

**Models**:
- **EasyOCR** + YOLOv8 - Plate detection + OCR
- **Tesseract OCR** - Text recognition
- **PaddleOCR** - High accuracy OCR
- **OpenALPR** - Dedicated ALPR

**Integration**:
```python
# backend/models/license_plate.py
import easyocr
from .base import BaseModel

class LicensePlateModel(BaseModel):
    def __init__(self, *args):
        super().__init__(*args)
        self.reader = easyocr.Reader(['en'])
        
    async def detect(self, frame):
        # Detect plates with YOLO
        plates = self.yolo(frame)
        # Read text
        for plate in plates:
            text = self.reader.readtext(plate_region)
        return results
```

### 3. **Pose Estimation**
**Use Cases**: Fall detection, behavior analysis, activity recognition

**Models**:
- **YOLOv8-Pose** - Body keypoints
- **MediaPipe Pose** - Real-time pose estimation
- **OpenPose** - Multi-person pose
- **MoveNet** - Fast pose detection

**Integration**:
```python
# backend/models/pose_estimation.py
from ultralytics import YOLO

class PoseEstimationModel(BaseModel):
    def __init__(self, *args):
        super().__init__(*args)
        self.model = YOLO('yolov8n-pose.pt')
        
    async def detect(self, frame):
        results = self.model(frame)
        poses = self.extract_keypoints(results)
        return poses
```

### 4. **Crowd Counting**
**Use Cases**: Occupancy monitoring, crowd management, safety compliance

**Models**:
- **CSRNet** - Crowd counting
- **MCNN** - Multi-column CNN
- **SANet** - Scale-aware network

**Integration**:
```python
# backend/models/crowd_counter.py
class CrowdCounterModel(BaseModel):
    async def detect(self, frame):
        count = self.model.predict(frame)
        return {'count': count, 'density_map': density}
```

### 5. **Action Recognition**
**Use Cases**: Suspicious behavior, fall detection, violence detection

**Models**:
- **SlowFast** - Video action recognition
- **I3D** - Inflated 3D ConvNet
- **TSM** - Temporal Shift Module

**Integration**:
```python
# backend/models/action_recognition.py
class ActionRecognitionModel(BaseModel):
    async def detect(self, frame_sequence):
        # Requires multiple frames
        action = self.model(frame_sequence)
        return {'action': action, 'confidence': conf}
```

### 6. **PPE Detection**
**Use Cases**: Safety compliance, construction sites, industrial areas

**Models**:
- **Custom YOLOv8** - Trained on hard hats, vests, masks
- **Roboflow PPE** - Pre-trained PPE detector

**Integration**:
```python
# backend/models/ppe_detection.py
class PPEDetectionModel(BaseModel):
    async def detect(self, frame):
        # Detect hard hat, vest, mask, gloves
        ppe_items = self.model(frame)
        violations = self.check_compliance(ppe_items)
        return violations
```

### 7. **Weapon Detection**
**Use Cases**: Security, threat detection, critical areas

**Models**:
- **Custom YOLOv8** - Trained on weapons
- **Roboflow Weapons** - Pre-trained detector

**Integration**:
```python
# backend/models/weapon_detection.py
class WeaponDetectionModel(BaseModel):
    async def detect(self, frame):
        weapons = self.model(frame)
        # High confidence threshold
        return [w for w in weapons if w['confidence'] > 0.85]
```

### 8. **Smoke/Fire Detection**
**Use Cases**: Fire safety, early warning, industrial monitoring

**Models**:
- **Custom CNN** - Smoke/fire classifier
- **FireNet** - Fire detection
- **YOLOv8 Custom** - Trained on fire/smoke

**Integration**:
```python
# backend/models/fire_detection.py
class FireDetectionModel(BaseModel):
    async def detect(self, frame):
        fire = self.classifier(frame)
        if fire['confidence'] > 0.9:
            return [{'type': 'fire', 'confidence': fire['confidence']}]
```

### 9. **Object Tracking**
**Use Cases**: Track people/vehicles across cameras, dwell time

**Models**:
- **ByteTrack** - Multi-object tracking
- **DeepSORT** - Deep learning tracking
- **BoT-SORT** - State-of-the-art tracker

**Integration**:
```python
# backend/models/object_tracker.py
from boxmot import ByteTrack

class ObjectTrackerModel(BaseModel):
    def __init__(self, *args):
        super().__init__(*args)
        self.tracker = ByteTrack()
        
    async def detect(self, frame):
        # Track objects across frames
        tracks = self.tracker.update(detections, frame)
        return tracks
```

### 10. **Anomaly Detection**
**Use Cases**: Unusual behavior, loitering, abandoned objects

**Models**:
- **Autoencoders** - Learn normal patterns
- **One-Class SVM** - Anomaly detection
- **LSTM** - Temporal anomalies

**Integration**:
```python
# backend/models/anomaly_detection.py
class AnomalyDetectionModel(BaseModel):
    async def detect(self, frame_history):
        anomaly_score = self.model(frame_history)
        if anomaly_score > threshold:
            return [{'type': 'anomaly', 'score': anomaly_score}]
```

## Specialty Models

### 11. **OCR / Text Recognition**
- **EasyOCR** - Multi-language OCR
- **PaddleOCR** - High accuracy
- **Tesseract** - Classic OCR
- **MMOCR** - Advanced text detection

**Use Cases**: Read signs, license plates, documents

### 12. **Instance Segmentation**
- **YOLOv8-Seg** - Pixel-level object masks
- **Mask R-CNN** - Instance segmentation
- **SAM (Segment Anything)** - Universal segmenter

**Use Cases**: Precise object boundaries, parking space detection

### 13. **Age/Gender Classification**
- **DeepFace** - Age and gender
- **FairFace** - Demographic classification

**Use Cases**: Demographics, retail analytics

### 14. **Emotion Detection**
- **DeepFace** - Emotion recognition
- **FER** - Facial expression recognition

**Use Cases**: Customer experience, security

### 15. **Animal Detection**
- **MegaDetector** - Wildlife detection
- **Custom YOLOv8** - Specific animals

**Use Cases**: Wildlife monitoring, farm security

## Cloud AI Services (Easy Integration)

### 16. **Google Cloud Vision**
```python
from google.cloud import vision

class GoogleVisionModel(BaseModel):
    async def detect(self, frame):
        response = client.label_detection(image=frame)
        return self.format_labels(response)
```

### 17. **AWS Rekognition**
```python
import boto3

class AWSRekognitionModel(BaseModel):
    async def detect(self, frame):
        response = rekognition.detect_labels(Image={'Bytes': frame})
        return response
```

### 18. **Azure Computer Vision**
```python
from azure.cognitiveservices.vision.computervision import ComputerVisionClient

class AzureVisionModel(BaseModel):
    async def detect(self, frame):
        analysis = client.analyze_image(frame)
        return analysis
```

## How to Add Any Model

### Quick Add (3 steps):

**Step 1**: Create model file
```python
# backend/models/my_model.py
from .base import BaseModel
import numpy as np

class MyCustomModel(BaseModel):
    """Your custom AI model"""
    
    async def initialize(self):
        # Load your model
        self.model = load_my_model()
        
    async def detect(self, frame: np.ndarray):
        # Run inference
        results = self.model.predict(frame)
        
        # Format as detections
        detections = []
        for result in results:
            detections.append({
                'class_id': result.class_id,
                'class_name': result.name,
                'confidence': result.confidence,
                'bbox': [x1, y1, x2, y2]
            })
        return detections
        
    async def cleanup(self):
        del self.model
```

**Step 2**: Register model
```python
# backend/models/__init__.py
from .my_model import MyCustomModel

MODEL_REGISTRY['my-custom-model'] = MyCustomModel
```

**Step 3**: Restart backend
```bash
./run.sh
```

**Result**: Model appears in workflow builder sidebar automatically!

## Recommended Models for Security

### High Priority:
1. ✅ **YOLOv8** - Already integrated (general detection)
2. **License Plate Recognition** - Vehicle tracking
3. **Face Recognition** - Access control
4. **Weapon Detection** - Critical security
5. **PPE Detection** - Safety compliance

### Medium Priority:
6. **Pose Estimation** - Fall detection
7. **Crowd Counting** - Occupancy limits
8. **Object Tracking** - Follow suspects
9. **Anomaly Detection** - Unusual behavior
10. **Fire/Smoke Detection** - Safety

### Nice to Have:
11. **Age/Gender** - Demographics
12. **Emotion Detection** - Customer service
13. **OCR** - Read signs/documents
14. **Animal Detection** - Wildlife/pets

## Pre-trained Models Available

### Ultralytics Hub
- 1000+ pre-trained models
- Download and use directly
- https://hub.ultralytics.com/

### Roboflow Universe
- 50,000+ pre-trained models
- Security, safety, retail
- https://universe.roboflow.com/

### Hugging Face
- Thousands of vision models
- Easy integration with transformers
- https://huggingface.co/models?pipeline_tag=object-detection

## Performance Comparison

| Model | Speed (FPS) | Accuracy | Use Case |
|-------|-------------|----------|----------|
| YOLOv8n | 150 | Good | General, many cameras |
| YOLOv8m | 50 | Excellent | Balanced |
| Face Recognition | 30 | Excellent | Identification |
| License Plate | 40 | Very Good | Vehicles |
| Pose Estimation | 60 | Good | Activity |
| Weapon Detection | 40 | Critical | Security |
| Crowd Counting | 20 | Good | Occupancy |

## Next Steps

Want me to implement any of these? Popular choices:

1. **License Plate Recognition** - Track all vehicles
2. **Face Recognition** - Identify known people
3. **Weapon Detection** - Critical security
4. **PPE Detection** - Safety compliance
5. **Custom YOLOv8** - Train on your specific needs

Just tell me which model you want and I'll integrate it into Overwatch with full workflow builder support!

