# AI Model Visualization Feature

**Date:** October 31, 2025  
**Status:** 🚧 IN PROGRESS  

---

## 🎯 Feature Overview

Add visual previews to AI model nodes showing what the model detects with bounding boxes, labels, heatmaps, and other visualizations.

### Key Capabilities:
1. **Live Preview** - See annotated frames in real-time
2. **Multiple Viz Types** - Bounding boxes, heatmaps, pose skeletons, segmentation masks
3. **Output to Nodes** - Send annotated frames to Video Preview nodes
4. **Standard for All AI** - Apply to all AI models (YOLO, Pose, Segmentation, etc.)

---

## ✅ Completed

### 1. Backend Visualization Engine (`backend/workflows/visualization.py`)

**DetectionVisualizer Class:**
- ✅ `draw_detections()` - Bounding boxes with labels and confidence
- ✅ `draw_detection_count()` - Count overlay
- ✅ `draw_heatmap()` - Gaussian heatmap of detections
- ✅ `draw_zones()` - Detection zone polygons
- ✅ `create_thumbnail()` - Thumbnail generation
- ✅ `get_class_color()` - Consistent colors per class

**PoseVisualizer Class:**
- ✅ `draw_pose()` - Skeleton and keypoints for pose estimation

**SegmentationVisualizer Class:**
- ✅ `draw_masks()` - Instance segmentation masks with transparency

### 2. Video Preview Node (`workflow-builder/src/nodes/VideoPreviewNode.jsx`)

- ✅ Canvas-based frame display
- ✅ WebSocket connection for live frames
- ✅ Stats overlay (FPS, detections, latency)
- ✅ Connection detection
- ✅ Base64 image decoding

---

## 🚧 TODO

### Backend Integration

**1. Update Model Processing** (`backend/workflows/realtime_executor.py`)
```python
# Add to _process_through_model():
- Check if visualization enabled in model node data
- Create DetectionVisualizer instance
- Draw annotations on frame copy
- Encode to JPEG
- Convert to base64
- Send to Video Preview nodes via WebSocket
```

**2. WebSocket Frame Streaming**
```python
# Add method to send annotated frames:
async def _send_annotated_frame(node_id, frame, detections, stats):
    # Encode frame to JPEG
    # Convert to base64
    # Emit via WebSocket with type='annotated_frame'
```

**3. Handle Visualization Settings**
```python
# Read from model node data:
{
  "enableVisualization": true,
  "visualizationType": "boxes",  # boxes, heatmap, both
  "showConfidence": true,
  "showLabels": true,
  "minConfidence": 0.5
}
```

### Frontend Updates

**1. Update Model Node** (`workflow-builder/src/nodes/ModelNode.jsx`)

Add visualization settings panel:
```jsx
<div className="visualization-settings">
  <toggle> Enable Visualization </toggle>
  <select> Visualization Type </select>
  <checkbox> Show Confidence </checkbox>
  <checkbox> Show Labels </checkbox>
  <slider> Min Confidence </slider>
</div>
```

**2. Register Video Preview Node** (`workflow-builder/src/App.jsx`)
```javascript
import VideoPreviewNode from './nodes/VideoPreviewNode'

const nodeTypes = {
  // ... existing
  videoPreview: VideoPreviewNode,
}
```

**3. Add to Sidebar** (`workflow-builder/src/components/Sidebar.jsx`)
```javascript
debug: {
  items: [
    { type: 'videoPreview', label: 'Video Preview', icon: '📺', description: 'Live annotated video' },
    // ... existing
  ]
}
```

### Optimization

**1. Frame Rate Control**
- Only send visualization frames at specified FPS (default: 10 fps)
- Skip frames to reduce bandwidth

**2. JPEG Quality**
- Adjustable quality (50-95)
- Balance between quality and bandwidth

**3. Selective Streaming**
- Only send frames when Video Preview node connected
- Stop streaming when node disconnected

---

## 📋 Implementation Steps

### Phase 1: Basic Visualization (CURRENT)
1. ✅ Create visualization utilities
2. ✅ Create Video Preview node
3. ⏳ Integrate into model processing
4. ⏳ Add WebSocket streaming
5. ⏳ Register nodes and update UI

### Phase 2: Advanced Features
6. ⏳ Add heatmap visualization
7. ⏳ Add pose skeleton rendering
8. ⏳ Add segmentation masks
9. ⏳ Add zone overlays
10. ⏳ Performance optimization

### Phase 3: Extended Support
11. ⏳ Apply to all AI models
12. ⏳ Add custom visualization options
13. ⏳ Export/save annotated frames
14. ⏳ Recording functionality

---

## 🎨 Visualization Types

### 1. Bounding Boxes (Default)
```
┌────────────┐
│ person 0.95│ ← Label with confidence
│            │
│     ▓▓     │
│    ▓▓▓▓    │
│     ▓▓     │
└────────────┘
```

### 2. Heatmap
```
Gaussian blur overlays showing
detection density/concentration
```

### 3. Pose Skeleton
```
Keypoints connected with lines
showing body pose structure
```

### 4. Segmentation Masks
```
Colored semi-transparent overlays
showing exact object boundaries
```

---

## 🔌 Workflow Examples

### Example 1: Basic Detection Viz
```
Video Input → YOLOv8N → Video Preview
              (viz enabled)
```

### Example 2: Filtered Visualization
```
Video Input → YOLOv8N → Detection Filter → Video Preview
              (viz ON)   (person only)
```

### Example 3: Multiple Outputs
```
Video Input → YOLOv8N ┬→ Video Preview (visualized)
              (viz ON) ├→ Debug Console (data)
                       └→ Email Alert (action)
```

### Example 4: Pose Estimation
```
Video Input → Pose Model → Video Preview
              (skeleton ON)
```

---

## 💾 Data Format

### Annotated Frame Message
```json
{
  "type": "annotated_frame",
  "node_id": "model-12345",
  "workflow_id": "workflow-67890",
  "frame_data": "base64_encoded_jpeg...",
  "fps": 10,
  "detections_count": 3,
  "processing_time_ms": 45,
  "timestamp": "2025-10-31T20:00:00Z",
  "visualization_type": "boxes",
  "resolution": {
    "width": 1920,
    "height": 1080
  }
}
```

---

## 🚀 Quick Start (When Complete)

1. **Add Video Preview Node**
   - Drag from Debug & Output section
   - Connect to AI model output

2. **Enable Visualization on Model**
   - Click ⚙️ on model node
   - Toggle "Enable Visualization"
   - Choose visualization type

3. **Run Workflow**
   - Click Execute
   - See live annotated frames in Video Preview

---

## 🎯 Next Immediate Steps

1. Register Video Preview node in App.jsx and Sidebar.jsx
2. Add visualization toggle to Model node UI
3. Integrate DetectionVisualizer into backend model processing
4. Add WebSocket streaming for annotated frames
5. Test with simple workflow: Video → YOLO → Video Preview

---

## 🐛 Testing Checklist

- [ ] Video Preview node appears in sidebar
- [ ] Can drag Video Preview onto canvas
- [ ] Connects to model nodes
- [ ] Model node has visualization toggle
- [ ] Annotated frames display in preview
- [ ] Bounding boxes draw correctly
- [ ] Labels and confidence show
- [ ] FPS counter works
- [ ] Frame updates in real-time
- [ ] Works with detection filters
- [ ] Multiple preview nodes supported
- [ ] Disconnecting stops streaming

---

## 📝 Notes

- Visualization is optional and disabled by default
- Only active when Video Preview node connected
- Uses JPEG compression to reduce bandwidth
- Color coding consistent per object class
- Track IDs shown when available
- Supports all YOLO models (detection, pose, segmentation)

---

**Status:** Ready for Phase 1 completion - Need to integrate backend and register nodes.

