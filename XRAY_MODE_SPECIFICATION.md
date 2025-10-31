# X-RAY Mode - Complete Specification

**Feature Name:** X-RAY Mode  
**Purpose:** See what AI models see in a human-readable visual form  
**Date:** October 31, 2025  
**Status:** 🚧 IN PROGRESS

---

## 🔍 Concept

**X-RAY Mode** lets you "peer inside" any AI model to visualize its understanding of the scene in real-time.

### Philosophy
- **Transparency**: See exactly what the AI detects
- **Flexibility**: Multiple visualization modes for different use cases
- **Universal**: Works with all AI model types (detection, segmentation, pose, etc.)
- **Diagnostic**: Essential for debugging and tuning models

---

## 🎨 X-RAY Visualization Modes

### For Object Detection Models (YOLO, etc.)

#### 1. **Boxes Mode** (Default)
- Bounding boxes with labels
- Confidence scores
- Track IDs
- Original image preserved

#### 2. **Schematic Mode**
- Pure boxes on black background
- No original image - just AI's understanding
- Like a blueprint or wireframe
- Minimal visual noise

#### 3. **Heatmap Mode**
- Gaussian blur showing detection density
- Hotspots where objects cluster
- Color-coded by confidence or count

#### 4. **Hybrid Mode**
- Combines boxes + heatmap
- Best of both worlds

---

### For Segmentation Models (SAM, YOLOv8-seg, etc.)

#### 1. **Mask Overlay**
- Semi-transparent colored masks
- Shows exact object boundaries
- Each instance different color

#### 2. **Contour Only**
- Just mask outlines
- Clean, minimal view
- See object shapes clearly

#### 3. **Solid Masks**
- Fully opaque colored regions
- Clear object separation
- Like paint-by-numbers

#### 4. **Schematic Masks**
- Masks on black background
- Pure AI vision - no original image
- Architectural/blueprint style

#### 5. **Mask Heatmap**
- Density map showing overlap
- Identifies crowded regions
- Viridis/Jet colormap

#### 6. **Quad View**
```
┌─────────────┬─────────────┐
│  Original   │  Contours   │
├─────────────┼─────────────┤
│   Masks     │   Density   │
└─────────────┴─────────────┘
```
- Four views simultaneously
- Compare different visualizations
- Perfect for model tuning

#### 7. **Object Cutouts**
- Extract each detected object separately
- Transparent background
- Use for galleries or comparisons

---

### For Pose Estimation Models

#### 1. **Skeleton View**
- Keypoints connected with lines
- Body structure visualization
- Original image preserved

#### 2. **Keypoints Only**
- Just the detected points
- No skeleton lines
- Schematic mode available

#### 3. **Confidence Heatmap**
- Color keypoints by confidence
- Red = low, Green = high
- Identify weak detections

---

## 🎨 Color Schemes

### 1. **Default (Hash-based)**
- Each class gets unique color
- Consistent across sessions
- Good for general use

### 2. **Confidence Gradient**
- Red (low) → Green (high)
- Visualize detection confidence
- Spot weak detections instantly

### 3. **Class-Specific**
- Predefined colors per class
- Person = Blue, Car = Green, etc.
- Intuitive color coding

### 4. **Thermal**
- Thermal camera style
- Jet colormap
- Cool = blue, Hot = red

### 5. **Neon**
- Bright, vivid colors
- Cyberpunk aesthetic
- High contrast for dark scenes

### 6. **Monochrome**
- Single color (green, cyan, etc.)
- Matrix/radar style
- Minimal distraction

---

## ⚙️ Model Node X-RAY Settings

### Enable X-RAY Toggle
```javascript
enableXRay: true/false
```

### X-RAY Mode Selection
```javascript
xrayMode: 
  - 'boxes'           // Bounding boxes
  - 'schematic'       // Boxes without image
  - 'heatmap'         // Detection density
  - 'boxes+heatmap'   // Combined
  - 'masks'           // Segmentation masks
  - 'masks-contour'   // Mask outlines only
  - 'masks-solid'     // Opaque masks
  - 'masks-schematic' // Masks without image
  - 'masks-heatmap'   // Mask density
  - 'quad'            // 4-view comparison
  - 'pose-skeleton'   // Body pose
  - 'pose-keypoints'  // Points only
```

### Display Options
```javascript
showBoxes: true/false
showLabels: true/false
showConfidence: true/false
showTrackIds: true/false
showMasks: true/false
showContours: true/false
```

### Color Options
```javascript
colorScheme: 
  - 'default'
  - 'confidence'
  - 'class_specific'
  - 'thermal'
  - 'neon'
  - 'monochrome'

customColors: {
  person: '#00FF00',
  car: '#FF0000',
  // ...
}
```

### Overlay Options
```javascript
overlayAlpha: 0.5        // Transparency 0.0-1.0
heatmapIntensity: 0.7    // Heatmap strength
lineThickness: 2         // Box line width
fontSize: 0.6            // Label font size
```

---

## 🔌 Node Connections

### X-RAY View Node (Output)

**Accepts connections from:**
- Detection models (YOLO, etc.)
- Segmentation models (SAM, YOLOv8-seg)
- Pose estimation models
- Detection Filter nodes
- Any node with visual output

**Displays:**
- Live annotated frames
- FPS counter
- Detection/mask count
- Processing latency
- Resolution info

---

## 📊 X-RAY View Node Features

### Display Modes
1. **Live Stream** - Continuous updates
2. **Snapshot** - Freeze on current frame
3. **Comparison** - Side-by-side original vs X-RAY
4. **Fullscreen** - Expand to full canvas

### Controls
- **Play/Pause** - Freeze X-RAY view
- **Screenshot** - Save current X-RAY frame
- **Mode Toggle** - Switch visualization types on the fly
- **Color Picker** - Adjust color scheme
- **Alpha Slider** - Adjust transparency

### Stats Overlay
- FPS (frames per second)
- Detection count
- Processing latency
- Model name
- Resolution
- Color scheme indicator

---

## 🎯 Use Cases

### 1. Model Debugging
```
Video → YOLOv8N → X-RAY View
        (boxes mode)
```
See what model detects vs what you expect

### 2. Confidence Tuning
```
Video → YOLOv8N → X-RAY View
        (confidence gradient)
```
Identify weak vs strong detections

### 3. Segmentation Analysis
```
Video → SAM → X-RAY View
        (quad mode)
```
Compare different mask visualizations

### 4. Filter Verification
```
Video → YOLO → Filter → X-RAY View
               (person)  (schematic)
```
Verify filter is working correctly

### 5. Multi-Model Comparison
```
Video → YOLOv8N → X-RAY View #1 (boxes)
     └→ YOLOv8X → X-RAY View #2 (boxes)
```
Compare different model outputs side-by-side

---

## 🔧 Advanced Features

### 1. Schematic Rendering (No Original Image)
**Use Cases:**
- Focus on AI detections only
- Reduce visual clutter
- Export clean data for overlays
- AR/VR applications
- Simplified monitoring

**Technical:**
```python
# Black canvas with just detections
schematic = create_blank_canvas(width, height, color=(0, 0, 0))
schematic = draw_boxes_only(schematic, detections)
```

### 2. Configurable Color Coding

**By Class:**
```python
colors = {
  'person': (255, 100, 100),  # Blue
  'car': (100, 255, 100),     # Green
  'truck': (100, 200, 255),   # Orange
}
```

**By Confidence:**
```python
# Low confidence = Red
# High confidence = Green
color = interpolate(red, green, confidence)
```

**By Instance:**
```python
# Each detected instance gets unique color
# Useful for tracking/counting
```

### 3. Heatmapping

**Detection Density:**
- Shows where detections concentrate
- Gaussian blur for smooth gradients
- Useful for traffic analysis, crowd monitoring

**Temporal Heatmap:**
- Accumulate detections over time
- Show movement patterns
- Historical activity visualization

**Confidence Heatmap:**
- Show confidence distribution spatially
- Identify areas with weak detections
- Model confidence mapping

### 4. Mask Operations

**Boolean Operations:**
- Union: Combined mask of all objects
- Intersection: Overlapping regions
- Difference: Non-overlapping regions

**Morphological Operations:**
- Erosion: Shrink masks
- Dilation: Expand masks
- Opening: Remove noise
- Closing: Fill holes

**Mask Algebra:**
- Foreground/background separation
- Object counting by region
- Area calculations
- Coverage statistics

---

## 📐 Segmentation Model Planning

### Supported Models (Future)

#### 1. **SAM (Segment Anything Model)**
```yaml
Capabilities:
  - Interactive segmentation
  - Click-to-segment
  - Everything mode (segment all)
  - Prompt-based masking
  
X-RAY Modes:
  - Full masks (colored)
  - Mask boundaries only
  - Confidence overlay
  - Hierarchical view
```

#### 2. **YOLOv8-seg (Instance Segmentation)**
```yaml
Capabilities:
  - Object detection + masks
  - Real-time performance
  - 80 COCO classes
  
X-RAY Modes:
  - Boxes + masks combined
  - Masks with class labels
  - Per-instance coloring
  - Density heatmap
```

#### 3. **Mask R-CNN**
```yaml
Capabilities:
  - Precise instance segmentation
  - Slower but accurate
  
X-RAY Modes:
  - High-quality mask rendering
  - Detailed contours
  - Object cutouts
```

#### 4. **DeepLab (Semantic Segmentation)**
```yaml
Capabilities:
  - Pixel-level classification
  - Scene understanding
  
X-RAY Modes:
  - Per-class segmentation
  - Scene layout visualization
  - Depth-style rendering
```

---

## 🎬 X-RAY Rendering Pipeline

### Stage 1: Model Inference
```python
model.detect(frame) → detections/masks
```

### Stage 2: Apply X-RAY Settings
```python
if xray_mode == 'schematic':
    canvas = create_blank_canvas()
else:
    canvas = frame.copy()
```

### Stage 3: Render Based on Type
```python
if model_type == 'detection':
    visualizer.draw_detections(canvas, detections, ...)
elif model_type == 'segmentation':
    visualizer.draw_masks(canvas, masks, ...)
elif model_type == 'pose':
    visualizer.draw_pose(canvas, keypoints, ...)
```

### Stage 4: Apply Enhancements
```python
# Add overlays
canvas = add_detection_count(canvas)
canvas = add_stats_panel(canvas)
canvas = add_color_legend(canvas)
```

### Stage 5: Encode & Stream
```python
jpeg = encode_jpeg(canvas, quality=85)
base64 = encode_base64(jpeg)
websocket.send(base64)
```

---

## 🎨 Color Scheme Examples

### Thermal Vision
```
Cold (0%) ──────► Hot (100%)
Blue → Cyan → Green → Yellow → Red
```

### Confidence Gradient
```
Low (0%) ──────► High (100%)
Red → Orange → Yellow → Green
```

### Class-Specific (Security)
```
Person:     🔵 Blue
Vehicle:    🟢 Green
Animal:     🟡 Yellow
Unknown:    ⚪ Gray
```

### Neon/Cyberpunk
```
Saturated, bright colors
High contrast
Perfect for low-light
```

---

## 💡 Advanced Visualization Ideas

### 1. **Attention Maps**
- Show where model "looks"
- Grad-CAM style heatmaps
- Understand model focus

### 2. **Temporal Trails**
- Show object paths over time
- Motion visualization
- Track history overlay

### 3. **3D Projection**
- Depth estimation overlay
- Height/distance indicators
- Spatial understanding

### 4. **Multi-Model Fusion**
- Combine outputs from multiple models
- Show agreements/disagreements
- Ensemble visualization

### 5. **Uncertainty Visualization**
- Show model uncertainty regions
- Confidence distribution
- Decision boundaries

### 6. **Feature Maps**
- Show intermediate layer outputs
- Deep learning visualization
- Advanced debugging

---

## 🔧 Implementation Phases

### ✅ Phase 1: Detection Basics (CURRENT)
- [x] Bounding boxes
- [x] Labels and confidence
- [x] Color coding
- [x] Schematic mode
- [x] Basic heatmap

### 🚧 Phase 2: Segmentation Support (NEXT)
- [ ] Mask rendering
- [ ] Contour extraction
- [ ] Mask overlays
- [ ] Density heatmaps
- [ ] Quad view comparison

### 📋 Phase 3: Advanced Features
- [ ] Multiple color schemes
- [ ] Configurable UI for all modes
- [ ] Custom color picker
- [ ] Export capabilities
- [ ] Screenshot/save

### 📋 Phase 4: Pose & Beyond
- [ ] Pose skeleton rendering
- [ ] Keypoint visualization
- [ ] Tracking trails
- [ ] Attention maps
- [ ] Multi-model views

---

## 🎮 UI Controls (Model Node)

### X-RAY Settings Panel
```
┌─────────────────────────────┐
│ 🔍 X-RAY Mode               │
├─────────────────────────────┤
│ [✓] Enable X-RAY            │
│                             │
│ Mode: [Boxes ▼]             │
│   • Boxes                   │
│   • Schematic               │
│   • Heatmap                 │
│   • Boxes + Heatmap         │
│                             │
│ Color Scheme: [Default ▼]  │
│   • Default                 │
│   • Confidence Gradient     │
│   • Class-Specific          │
│   • Thermal                 │
│   • Neon                    │
│                             │
│ Display Options:            │
│ [✓] Show Boxes              │
│ [✓] Show Labels             │
│ [✓] Show Confidence         │
│ [✓] Show Track IDs          │
│                             │
│ Advanced:                   │
│ Line Thickness: ━━━○━━ 2px  │
│ Overlay Alpha:  ━━━━○━ 0.5  │
│ Font Size:      ━━○━━━ 0.6  │
│                             │
│ [Preview X-RAY Output]      │
└─────────────────────────────┘
```

---

## 📊 X-RAY View Node (Output)

### Features
```
┌──────────────────────────────┐
│ 🔍 X-RAY View      [📊][⚙️]│
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │                          │ │
│ │   [Annotated Frame]      │ │
│ │                          │ │
│ └──────────────────────────┘ │
│                              │
│ Stats Overlay:               │
│ • FPS: 15                    │
│ • Detections: 3              │
│ • Latency: 45ms              │
│ • Mode: Boxes                │
│ • Scheme: Default            │
│                              │
│ [⏸️] [📸] [🎨] [⚙️]         │
└──────────────────────────────┘
```

### Controls
- **⏸️ Pause** - Freeze current frame
- **📸 Screenshot** - Save X-RAY frame
- **🎨 Color** - Change color scheme on fly
- **⚙️ Settings** - Display preferences

---

## 🔗 Data Flow

### Normal Flow
```
Video → Model → Debug Console
              → Actions
```

### With X-RAY
```
Video → Model ┬→ X-RAY View (annotated frames)
   (X-RAY ON) ├→ Debug Console (data)
              └→ Actions (triggers)
```

### With Filter
```
Video → Model → Filter ┬→ X-RAY View (filtered, annotated)
                       └→ Debug (filtered data)
```

---

## 💾 Data Structures

### Detection Data (YOLO)
```json
{
  "class": "person",
  "class_name": "person",
  "confidence": 0.95,
  "bbox": {
    "x": 100,
    "y": 200,
    "width": 150,
    "height": 300
  },
  "track_id": 5,
  "speed": 12.5
}
```

### Segmentation Data
```json
{
  "class": "person",
  "confidence": 0.92,
  "bbox": {...},
  "mask": [[0,0,1,1,0], [0,1,1,1,0], ...],  // 2D array
  "mask_rle": "compressed_mask_data",         // Run-length encoding
  "area": 45000,  // pixels
  "centroid": {"x": 175, "y": 350}
}
```

### Pose Data
```json
{
  "person_id": 1,
  "confidence": 0.88,
  "bbox": {...},
  "keypoints": [
    {"name": "nose", "x": 175, "y": 120, "confidence": 0.95},
    {"name": "left_eye", "x": 165, "y": 115, "confidence": 0.92},
    // ... 17 total keypoints
  ]
}
```

### X-RAY Frame Message (WebSocket)
```json
{
  "type": "xray_frame",
  "workflow_id": "workflow-123",
  "node_id": "videoPreview-456",
  "frame_data": "base64_jpeg_data...",
  "xray_mode": "boxes",
  "color_scheme": "default",
  "detections_count": 3,
  "fps": 15,
  "processing_time_ms": 45,
  "resolution": {"width": 1920, "height": 1080},
  "model_type": "detection",  // or "segmentation", "pose"
  "timestamp": "2025-10-31T21:00:00Z"
}
```

---

## 🚀 Performance Considerations

### Bandwidth Optimization
- JPEG quality: 85 (good balance)
- Resize for preview (optional)
- FPS throttling (default 10fps)
- Only when X-RAY View connected

### Processing Overhead
- Visualization: ~5-10ms per frame
- Encoding: ~10-15ms per frame
- Total: ~15-25ms overhead
- Negligible impact on detection performance

### Memory
- Keep only latest frame in memory
- No buffering (live stream)
- Cleanup when disconnected

---

## 🎓 Educational Value

X-RAY Mode is perfect for:
- **Learning**: See how AI "thinks"
- **Training**: Understand model behavior
- **Debugging**: Spot false positives/negatives
- **Demos**: Show AI in action
- **Optimization**: Tune confidence thresholds
- **Validation**: Verify model accuracy

---

## 🔮 Future Enhancements

### 1. Temporal Features
- Motion trails (object paths over time)
- Historical heatmaps
- Trajectory prediction visualization

### 2. 3D Visualization
- Depth estimation overlay
- 3D bounding boxes
- Point cloud rendering

### 3. Interactive Features
- Click box to see details
- Hover for confidence tooltip
- Select instance to highlight
- Draw custom regions

### 4. Export Capabilities
- Save annotated video
- Export frame sequences
- Generate reports
- Create training datasets

### 5. AR/VR Integration
- Pass-through with overlays
- Real-time AR annotations
- Spatial computing support

---

## 📋 Next Steps

1. ✅ Add schematic mode support to backend
2. ✅ Implement color scheme system
3. ⏳ Add X-RAY toggle UI to Model nodes
4. ⏳ Test full pipeline: Model → X-RAY View
5. ⏳ Add screenshot capability
6. ⏳ Document usage examples
7. ⏳ Performance testing
8. ⏳ Extend to segmentation models
9. ⏳ Add pose visualization
10. ⏳ Create demo workflows

---

**Status:** Foundation complete, integration in progress. X-RAY Mode will revolutionize how users interact with AI models in Overwatch! 🚀

