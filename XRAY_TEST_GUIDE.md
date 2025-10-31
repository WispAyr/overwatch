# X-RAY View Testing Guide

## Quick Test Checklist

### 1. Setup
- [ ] Backend is running (`./run.sh` or check http://localhost:8000)
- [ ] Workflow Builder is open (http://localhost:7003)
- [ ] Workflow has: Video Input → Ultralytics YoloV8N → X-RAY View

### 2. Configure X-RAY Mode
- [ ] Click the Ultralytics YoloV8N node to open settings
- [ ] Scroll down to "🔍 X-RAY Mode" section
- [ ] Toggle to **ON** (should be purple/bright color)
- [ ] Optional: Click "Show Settings" to adjust:
  - X-RAY Mode: boxes / heatmap / schematic
  - Show confidence, labels, boxes
  - Overlay alpha

### 3. Start Video
- [ ] In Video Input node, verify video is loaded
- [ ] Click "Pause" button to unpause if needed
- [ ] Video should be playing (scrubber moving)

### 4. Execute Workflow
- [ ] Click the **Save** button (💾 Save) in top toolbar
- [ ] Click the **Execute** button (▶️ Execute) in top toolbar
- [ ] Button should change to "⏹ Stop"
- [ ] Green "Running" indicator should appear

### 5. Verify X-RAY Output
- [ ] X-RAY View node should show "Waiting for frames..."
- [ ] After a few seconds, annotated frames should appear
- [ ] FPS counter should update
- [ ] Detection count should show number of objects found
- [ ] Boxes/heatmaps should be visible on the video

### 6. Troubleshooting

#### No frames appearing in X-RAY View?

**Check Browser Console (F12):**
```javascript
// Should see messages like:
X-RAY View <node_id>: Received message xray_frame <node_id>
X-RAY View <node_id>: Processing X-RAY frame!
```

**Check Backend Logs:**
```bash
tail -f /tmp/overwatch-run.log
# Should see messages about workflow execution and frame processing
```

**Verify connections:**
- Ensure green line connects Video Input → Model → X-RAY View
- Connections must be from output handle (right side) to input handle (left side)

**Restart workflow:**
1. Click Stop button
2. Wait 2 seconds  
3. Click Execute again

#### Model not detecting anything?

- Check "Detect Classes" - ensure "All classes" is selected or specific classes are chosen
- Lower the "Confidence Threshold" (try 0.3 or 0.4)
- Verify the video has objects that YOLOv8 can detect (people, cars, etc.)

#### Performance issues?

- Reduce "Processing FPS" in Model node (try 5 fps)
- Use "Batch Size: 1 (Real-time)" for lowest latency
- Close other browser tabs

## Expected Behavior

### ✅ Working Correctly:
- X-RAY View updates 5-10 times per second
- Detection boxes/labels overlay on video frames
- FPS counter shows around the same as "Processing FPS" setting
- Detection count updates in real-time
- Latency stays under 100ms

### ❌ Not Working:
- X-RAY View stuck on "Waiting for frames..."
- No detection boxes visible
- FPS shows 0
- Console errors about WebSocket connection

## Advanced Testing

### Test Different X-RAY Modes:
1. **Boxes Mode** - Traditional bounding boxes with labels
2. **Heatmap Mode** - Heat map overlay showing detection density
3. **Schematic Mode** - Simplified technical view
4. **Both Mode** - Combines boxes and heatmap

### Test Multiple X-RAY Views:
- Add multiple X-RAY View nodes connected to the same Model
- Each should receive the same frames
- Can configure different display options per view

### Test with Live Camera:
- Replace Video Input with Camera Node
- Configure RTSP stream URL
- X-RAY mode works the same way

## Technical Details

### WebSocket Messages
X-RAY frames are sent via WebSocket with this structure:
```json
{
  "type": "xray_frame",
  "workflow_id": "workflow-123",
  "node_id": "xray-view-node-id",
  "timestamp": "2025-10-31T12:00:00",
  "frame_data": "base64-encoded-jpeg...",
  "fps": 10,
  "detections_count": 3,
  "processing_time_ms": 25,
  "xray_mode": "boxes",
  "resolution": {
    "width": 1920,
    "height": 1080
  }
}
```

### Flow Path
```
Video Input Node
  ↓ (frame data)
Model Node (X-RAY ON)
  ↓ (processes frame)
  ↓ (draws detection boxes)
  ↓ (encodes to base64 JPEG)
WebSocket Broadcast (type: xray_frame)
  ↓
X-RAY View Node (frontend)
  ↓ (receives via WebSocket)
  ↓ (renders to canvas)
Display ✨
```

## Success!

If you see annotated frames with detection boxes updating in real-time in the X-RAY View node, the system is working correctly! 🎉

The X-RAY mode gives you real-time visual feedback on what the AI model is detecting, making it perfect for:
- Debugging detection accuracy
- Tuning confidence thresholds
- Visualizing model performance
- Creating monitoring dashboards
- Demonstrating AI capabilities

