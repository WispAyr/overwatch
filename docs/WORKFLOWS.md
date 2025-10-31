# Workflow Guide

## Overview

Workflows in Overwatch define how video frames are processed through AI models and what actions to take on detections.

## Workflow Structure

A workflow consists of:
1. **Input Source**: Which camera(s) to process
2. **Processing Pipeline**: AI models to apply
3. **Detection Filters**: Confidence thresholds, zones, etc.
4. **Actions**: What to do with detections

## Built-in Workflows

### People Detection
Detects human presence in camera view.

```yaml
workflow:
  id: people_detection
  name: "People Detection"
  model: ultralytics-yolov8n
  classes: [0]  # person
  confidence: 0.7
  processing:
    fps: 10  # Process 10 frames per second
    skip_similar: true  # Skip if scene hasn't changed
  actions:
    - type: event
      severity: info
    - type: webhook
      url: ${WEBHOOK_URL}
      on_enter: true  # Only trigger when person enters view
```

### Weapon Detection
Identifies potential weapons in view.

```yaml
workflow:
  id: weapon_detection
  name: "Weapon Detection"
  model: custom-weapon-detector
  confidence: 0.85  # Higher threshold for weapons
  processing:
    fps: 15
    skip_similar: false  # Always process
  actions:
    - type: alert
      severity: critical
      notify: [security_team]
    - type: record
      duration: 30  # Record 30s of video
      pre_buffer: 10  # Include 10s before detection
```

### Bay Monitoring
Monitors loading bays for vehicle presence and safety.

```yaml
workflow:
  id: bay_monitoring
  name: "Bay Monitoring"
  model: ultralytics-yolov8m
  classes: [2, 5, 7]  # car, bus, truck
  zones:
    - name: bay_1
      polygon: [[100, 100], [500, 100], [500, 400], [100, 400]]
      max_occupancy: 1
  processing:
    fps: 5
  actions:
    - type: event
      on_zone_enter: true
      on_zone_exit: true
    - type: metric
      track: occupancy_time
```

### Parking Violation (Yellow Line)
Detects vehicles parked in restricted zones.

```yaml
workflow:
  id: parking_violation
  name: "Yellow Line Parking"
  model: ultralytics-yolov8s
  classes: [2, 5, 7]  # vehicles
  zones:
    - name: no_parking_zone
      polygon: [[200, 300], [800, 300], [800, 450], [200, 450]]
      dwell_time: 30  # Must be stationary for 30s
  processing:
    fps: 2
  actions:
    - type: alert
      severity: warning
      include_snapshot: true
    - type: record
      duration: 60
```

## Custom Workflows

### Creating a Workflow

1. Define the workflow YAML:

```yaml
workflow:
  id: custom_workflow
  name: "My Custom Workflow"
  model: ultralytics-yolov8n
  
  # Detection configuration
  classes: [0, 1, 2]  # Which object classes to detect
  confidence: 0.7     # Minimum confidence threshold
  
  # Optional: Define zones
  zones:
    - name: zone_1
      polygon: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
      
  # Processing settings
  processing:
    fps: 10                  # Frames per second to process
    skip_similar: true       # Skip if scene unchanged
    batch_size: 1           # Batch multiple frames
    
  # Actions on detection
  actions:
    - type: event           # Log to event system
      severity: info
    - type: webhook         # Call webhook
      url: https://example.com/webhook
      method: POST
    - type: record          # Record video clip
      duration: 30
```

2. Save to `config/workflows/custom_workflow.yaml`

3. Assign to cameras in `config/cameras.yaml`:

```yaml
cameras:
  - id: cam-001
    name: "Front Door"
    rtsp_url: "rtsp://..."
    workflows:
      - custom_workflow
```

## Advanced Features

### Zone-Based Detection

Define polygon zones for spatial filtering:

```yaml
zones:
  - name: restricted_area
    polygon: [[100, 100], [500, 100], [500, 400], [100, 400]]
    rules:
      - class: 0  # person
        action: alert
        confidence: 0.8
```

### Temporal Filters

Reduce false positives with time-based rules:

```yaml
temporal:
  dwell_time: 5          # Object must be present for 5s
  cooldown: 60           # Wait 60s before next alert
  active_hours:          # Only active during these hours
    start: "18:00"
    end: "06:00"
```

### Chained Models

Run multiple models in sequence:

```yaml
pipeline:
  - model: ultralytics-yolov8n
    classes: [0]  # Detect people
  - model: pose-estimation
    input: previous  # Only run on detected people
  - model: activity-classifier
    input: previous  # Classify activity
```

### Conditional Actions

Execute actions based on complex conditions:

```yaml
actions:
  - type: alert
    conditions:
      - detection_count: ">= 2"  # Multiple objects
      - time_of_day: "night"      # After hours
      - zone: "restricted"         # In restricted zone
    severity: critical
```

## Model Selection Guide

### YOLOv8 Variants

- **YOLOv8n**: Fastest, lowest accuracy (edge devices)
- **YOLOv8s**: Balanced speed/accuracy
- **YOLOv8m**: Higher accuracy (recommended)
- **YOLOv8l**: Best accuracy, slower
- **YOLOv8x**: Maximum accuracy, requires GPU

### Use Case Recommendations

- **People Counting**: YOLOv8n or YOLOv8s
- **Weapon Detection**: Custom model or YOLOv8m+
- **Vehicle Detection**: YOLOv8s or YOLOv8m
- **Fine-grained Analysis**: YOLOv8l or custom models

## Performance Optimization

1. **Reduce FPS**: Process fewer frames for static scenes
2. **Skip Similar Frames**: Enable frame difference detection
3. **Use Zones**: Only process relevant areas
4. **Batch Processing**: Group frames for GPU efficiency
5. **Model Selection**: Use smallest model that meets accuracy needs

## Testing Workflows

Use the workflow tester:

```bash
python backend/tools/test_workflow.py --workflow custom_workflow --video test.mp4
```

This will process a video file through your workflow and show results without needing live cameras.

