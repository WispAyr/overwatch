# Configuration Node Guide

## Overview

**Config Nodes** provide a powerful way to manage reusable configurations in your workflows. Instead of configuring each AI model or action node individually, you can create Config Nodes with pre-defined settings and connect them to multiple nodes.

## Features

✅ **Reusable Configurations** - Define once, use many times  
✅ **Working Examples** - Library of pre-built configurations for common use cases  
✅ **Visual JSON Editor** - Edit configurations with syntax validation  
✅ **Template Library** - Quick-start templates for all major AI models  
✅ **Clean Interface** - No clutter on main nodes, config kept separate  

---

## Using Config Nodes

### Method 1: Drag from Sidebar

1. Open **Configuration** tab in sidebar
2. Drag one of these to canvas:
   - **Config Node** - Blank configuration
   - **Model Config** - Pre-configured for AI models
   - **Webhook Config** - Pre-configured for webhooks
   - **Recording Config** - Pre-configured for recordings

3. **Connect** Config Node → Model/Action Node
4. Configuration automatically applies!

### Method 2: From Examples Library

1. Click **📚 Examples** button (top right)
2. Browse **AI Models** or **Actions** tab
3. Select an example (e.g., "Person Detection - High Accuracy")
4. Click **🎯 Create Config Node**
5. Config Node appears on canvas with example settings
6. Connect to your Model node

---

## Configuration Examples

### AI Model Examples

#### 1. Person Detection - Standard
```json
{
  "confidence": 0.7,
  "classes": [0],
  "iou": 0.45,
  "maxDetections": 100,
  "fps": 10
}
```
**Use Case**: General surveillance, entry monitoring  
**Model**: `ultralytics-yolov8n`

#### 2. Person Detection - High Accuracy
```json
{
  "confidence": 0.85,
  "classes": [0],
  "iou": 0.4,
  "maxDetections": 50,
  "fps": 5
}
```
**Use Case**: Security zones, restricted areas  
**Model**: `ultralytics-yolov8m`

#### 3. Vehicle Detection - Parking
```json
{
  "confidence": 0.6,
  "classes": [2, 3, 5, 7],
  "iou": 0.5,
  "maxDetections": 50,
  "fps": 5
}
```
**Use Case**: Parking lot monitoring, traffic counting  
**Model**: `ultralytics-yolov8s`  
**Classes**: car (2), motorcycle (3), bus (5), truck (7)

#### 4. Fast Detection - Low Latency
```json
{
  "confidence": 0.6,
  "classes": [0, 2],
  "iou": 0.5,
  "maxDetections": 50,
  "fps": 30,
  "batchSize": 1
}
```
**Use Case**: Real-time monitoring, live dashboards  
**Model**: `ultralytics-yolov8n`

#### 5. Crowd Counting
```json
{
  "confidence": 0.5,
  "classes": [0],
  "iou": 0.3,
  "maxDetections": 500,
  "fps": 5
}
```
**Use Case**: Events, retail analytics, capacity monitoring  
**Model**: `ultralytics-yolov8m`

---

### Action Examples

#### Webhook - Slack Notification
```json
{
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "timeout": 10,
  "retries": 3
}
```

#### Email - Security Team
```json
{
  "to": "security@company.com",
  "cc": ["manager@company.com"],
  "subject": "Security Alert - {{camera_name}}",
  "includeSnapshot": true,
  "includeDetections": true
}
```

#### Recording - Extended
```json
{
  "duration": 120,
  "preBuffer": 10,
  "postBuffer": 10,
  "format": "mp4",
  "quality": "high"
}
```

---

## Editing Configurations

### In the Config Node

1. **Click** the Config Node
2. **Click** 📝 icon to open editor
3. **Edit JSON** directly
4. **Select template** from dropdown for quick start
5. **Copy/Clear** with action buttons

### JSON Structure

Configurations are stored as JSON objects with these common fields:

**For AI Models:**
- `confidence` (0.0-1.0) - Minimum detection confidence
- `classes` ([int]) - Array of COCO class IDs to detect
- `iou` (0.0-1.0) - Intersection over Union threshold
- `maxDetections` (int) - Maximum detections per frame
- `fps` (int) - Processing frames per second
- `batchSize` (int) - Frames to batch together

**For Actions:**
- **Webhook**: `url`, `method`, `headers`, `timeout`, `retries`
- **Email**: `to`, `cc`, `subject`, `includeSnapshot`, `includeDetections`
- **Recording**: `duration`, `preBuffer`, `postBuffer`, `format`, `quality`
- **Snapshot**: `drawBoxes`, `drawZones`, `format`, `quality`

---

## How Config Nodes Work

### Visual Workflow
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Config     │─────▶│    Model     │─────▶│   Action     │
│ confidence:  │      │  YOLOv8n     │      │   Email      │
│   0.85       │      │              │      │              │
│ classes: [0] │      │              │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

### Execution Flow

1. **Parse**: Visual executor finds Config node connected to Model
2. **Merge**: Config from ConfigNode merges with Model's config
3. **Priority**: ConfigNode settings override Model defaults
4. **Execute**: Model runs with merged configuration

### Benefits

- ✅ **Reusability**: One config → many nodes
- ✅ **Maintainability**: Change config once, affects all connected nodes
- ✅ **Clean UI**: Keep complex configs separate from workflow logic
- ✅ **Version Control**: Config nodes can be templated and shared
- ✅ **A/B Testing**: Swap configs by changing connections

---

## Advanced Usage

### Multiple Configs

You can connect **multiple Config nodes** to a single Model:
```
Config A (confidence) ─┐
                       ├─→ Model (merges all configs)
Config B (classes)    ─┘
```

Later configs override earlier ones in case of conflicts.

### Conditional Configs

Use **Link Call** nodes to switch between configs based on time/conditions:

```
[9AM-5PM] → Config: High Accuracy
[5PM-9AM] → Config: Fast Detection
```

### Shared Configs

Connect one Config node to **multiple Models** for consistent settings:

```
                    ┌─→ Model 1 (Camera A)
Config: Standard ───┼─→ Model 2 (Camera B)
                    └─→ Model 3 (Camera C)
```

---

## API Endpoint

**GET** `/api/workflow-components/examples`

Returns:
```json
{
  "examples": [
    {
      "name": "Person Detection - Standard",
      "description": "...",
      "modelId": "ultralytics-yolov8n",
      "config": { ... },
      "useCase": "..."
    }
  ],
  "action_examples": [ ... ]
}
```

---

## COCO Class IDs Reference

Common classes for detection:

| ID | Class | Use Case |
|----|-------|----------|
| 0 | person | People detection, crowd counting |
| 1 | bicycle | Bike parking, traffic monitoring |
| 2 | car | Vehicle detection, parking management |
| 3 | motorcycle | Traffic monitoring |
| 5 | bus | Public transport tracking |
| 7 | truck | Loading dock monitoring |
| 15 | cat | Pet detection |
| 16 | dog | Pet detection |
| 24 | backpack | Security screening |
| 26 | handbag | Security screening |
| 28 | suitcase | Security screening |

**Full list**: `/api/workflow-components/classes`

---

## Best Practices

### 1. Name Your Configs
Give descriptive names: "High Accuracy Person Detection" not "Config 1"

### 2. Document Use Cases
Add descriptions explaining when to use each config

### 3. Start with Examples
Browse the examples library before creating custom configs

### 4. Test Incrementally
Start with low confidence, increase gradually to find sweet spot

### 5. Consider Performance
- Lower FPS = less CPU usage
- Fewer classes = faster detection
- Smaller models (n/s) = lower latency

---

## Keyboard Shortcuts (Planned v1.1)

- `Cmd/Ctrl + E` - Open Examples
- `Cmd/Ctrl + Shift + C` - Create Config Node
- `Cmd/Ctrl + D` - Duplicate selected Config Node

---

*Last updated: October 30, 2025*


