# AI Models Quick Reference Card

## 🎯 Model Selection Guide

### Object Detection
```yaml
model_id: ultralytics-yolov8n  # Fast, general objects (80 classes)
# Use: General surveillance, people counting, vehicle detection
```

### Pose & Activity
```yaml
model_id: yolov8n-pose  # Body keypoints + fall detection
# Use: Fall detection, activity monitoring, posture analysis
```

### Precise Boundaries
```yaml
model_id: yolov8n-seg  # Pixel-level masks
# Use: Parking spaces, intrusion zones, area calculation
```

### Track Movement
```yaml
model_id: yolov8n-track  # Persistent IDs across frames
# Use: Follow people/vehicles, loitering, dwell time, paths
```

### Identify People
```yaml
model_id: face-recognition  # Face ID + demographics
# Use: Access control, VIP alerts, unauthorized persons
```

### Vehicle Tracking
```yaml
model_id: alpr  # License plate reading
# Use: Gate access, parking, vehicle logs
```

### Threat Detection
```yaml
model_id: weapon-detection  # Guns, knives, weapons
# Use: Security screening, critical alerts
```

### Fire Safety
```yaml
model_id: fire-detection  # Fire & smoke detection
# Use: Early warning, industrial safety
```

### Safety Compliance
```yaml
model_id: ppe-detection  # Hard hats, vests, masks
# Use: Construction, industrial, lab safety
```

### Speech Recognition
```yaml
model_id: whisper-base  # Speech-to-text
# Use: Audio transcription, voice commands
```

### Sound Classification
```yaml
model_id: yamnet  # General sounds (521 classes)
# Use: Ambient monitoring, general audio events
```

### Security Audio
```yaml
model_id: panns  # Gunshots, glass, alarms
# Use: Critical audio events, break-ins
```

## ⚡ Performance Tiers

### Fast (60+ FPS)
- `ultralytics-yolov8n` - General detection
- `yolov8n-pose` - Pose estimation
- `yolov8n-seg` - Segmentation
- `yolov8n-track` - Object tracking

### Balanced (30-60 FPS)
- `ultralytics-yolov8s` - Better accuracy
- `yolov8s-pose/seg/track` - Balanced variants
- `fire-detection` - Fire/smoke
- `ppe-detection` - Safety compliance

### Accurate (10-30 FPS)
- `ultralytics-yolov8m/l` - High accuracy
- `face-recognition` - Face ID
- `alpr` - License plates

### Specialized
- `weapon-detection` - Critical security
- `panns` - Audio events
- `whisper-*` - Speech transcription

## 🔧 Common Configurations

### High Accuracy
```yaml
config:
  confidence: 0.7  # Higher threshold
  variant: m  # Medium/large model
```

### High Speed
```yaml
config:
  confidence: 0.4  # Lower threshold
  variant: n  # Nano model
```

### Critical Security
```yaml
config:
  confidence: 0.85  # Very high threshold
  # For weapon/threat detection
```

## 📋 Workflow Combinations

### Complete Security
```yaml
- yolov8n-track  # Track all movement
- weapon-detection  # Threat detection
- face-recognition  # Identify people
- panns  # Audio monitoring
```

### Industrial Safety
```yaml
- ppe-detection  # Safety compliance
- fire-detection  # Fire/smoke
- yolov8n-pose  # Fall detection
```

### Smart Parking
```yaml
- yolov8n-seg  # Parking space masks
- alpr  # License plates
- yolov8n-track  # Vehicle tracking
```

### Perimeter Security
```yaml
- yolov8n-track  # Track intrusions
- face-recognition  # Identify persons
- weapon-detection  # Threat detection
```

## 💡 Tips

1. **Start with nano (n) variants** for testing
2. **Use tracking** when you need persistent IDs
3. **Combine models** in workflows for powerful detection
4. **Adjust confidence** based on false positive tolerance
5. **Test performance** before deploying to all cameras

## 📖 Full Documentation
- Complete guide: `NEW_MODELS_SUMMARY.md`
- Config examples: `config/model_examples.yaml`
- Technical details: `docs/AI_MODELS.md`


