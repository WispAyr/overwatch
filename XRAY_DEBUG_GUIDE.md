# X-RAY View Debug Guide

## Comprehensive Logging Added

I've added detailed logging throughout the X-RAY visualization pipeline to help diagnose issues.

## Where to Find Logs

### Backend Logs
```bash
tail -f /tmp/overwatch-debug.log | grep -E "(🔍|X-RAY|xray|detections)"
```

### Frontend Logs
Open Browser Console (F12 → Console tab)

## What the Logs Show

### Backend X-RAY Flow

When X-RAY mode is working, you'll see:

```
🔍 _send_xray_frames called for model model-xxxxx
   Frame shape: (1080, 1920, 3), Detections: 2
   X-RAY settings: {'show_boxes': True, 'show_labels': True, ...}
   Found 1 X-RAY View nodes
     - X-RAY node: videoPreview-xxxxx (type: videoPreview)
   Drawing X-RAY frame: mode=boxes, schematic=False
   ✅ Drew 2 detections on frame
   ✅ Added detection count overlay: 2
   ✅ Encoded frame to JPEG: 45.3 KB
   📤 Broadcasting X-RAY frame to node videoPreview-xxxxx
      Frame size: 45.3 KB, Detections: 2
   ✅ X-RAY frame sent to videoPreview-xxxxx
```

### Frontend X-RAY Logs

When receiving and displaying frames, you'll see:

```
🔍 X-RAY View videoPreview-xxxxx: Received xray_frame message
   Target node_id: videoPreview-xxxxx, My id: videoPreview-xxxxx
   Match: true
   Has frame_data: true
   Frame size: 45.3 KB
   Detections: 2
✅ X-RAY View videoPreview-xxxxx: Processing X-RAY frame!
   Resolution: 1920x1080
   Detections: 2
✅ X-RAY View videoPreview-xxxxx: Frame state updated
🎨 X-RAY View videoPreview-xxxxx: Drawing frame to canvas
✅ X-RAY View videoPreview-xxxxx: Frame drawn! Canvas: 1920x1080
```

## Troubleshooting with Logs

### Issue: No X-RAY View nodes found

**Backend Log:**
```
⚠️ No X-RAY View nodes found connected to model-xxxxx
```

**Solution:**
- Verify the X-RAY View node is connected to the Model node
- Check the connection line is green (valid)
- Ensure connection is from Model → X-RAY View (left to right)

### Issue: No detections

**Backend Log:**
```
Model model-xxxxx detected 0 objects
```

**Solution:**
- Lower confidence threshold (try 0.3 or 0.4)
- Check "Detect Classes" is set to "All classes"
- Verify the video contains detectable objects (people, cars, etc.)
- Check video is actually playing

### Issue: Frame not matching node ID

**Frontend Log:**
```
⏭️  X-RAY View videoPreview-123: Skipping frame meant for videoPreview-456
```

**Solution:**
- Multiple X-RAY View nodes receiving the same broadcast
- This is normal - each node filters for its own ID
- If YOUR node never gets a match, the backend might be sending to wrong ID

### Issue: No frame_data in message

**Frontend Log:**
```
⚠️  X-RAY View videoPreview-xxxxx: Received xray_frame but no frame_data!
```

**Solution:**
- Backend failed to encode frame
- Check backend logs for encoding errors
- May be a memory or CV2 issue

### Issue: Canvas not drawing

**Frontend Log:**
```
X-RAY View videoPreview-xxxxx: No canvas ref
```

**Solution:**
- React ref not initialized yet
- Usually resolves itself on next frame
- Try refreshing browser

### Issue: Image load error

**Frontend Log:**
```
❌ X-RAY View videoPreview-xxxxx: Error loading image: ...
```

**Solution:**
- Base64 data may be corrupted
- Check backend encoding logs
- Try stopping and restarting workflow

## Common Patterns

### Working Correctly
Every 100-300ms you should see:
1. Backend: "🔍 _send_xray_frames called"
2. Backend: "✅ X-RAY frame sent"
3. Frontend: "🔍 X-RAY View: Received xray_frame"
4. Frontend: "✅ X-RAY View: Processing"
5. Frontend: "🎨 X-RAY View: Drawing frame"
6. Frontend: "✅ X-RAY View: Frame drawn!"

### Workflow Not Running
You'll see:
- No backend logs at all
- Frontend shows: "Waiting for frames..."
- Solution: Click Execute button

### X-RAY Mode Disabled
You'll see:
- Model processing frames
- No "🔍 _send_xray_frames" messages
- Solution: Enable X-RAY mode in Model settings

### WebSocket Disconnected
You'll see:
- Backend sending frames
- Frontend: "WebSocket closed"  
- Solution: Refresh browser page

## Debug Commands

### Watch Backend Logs (Real-time)
```bash
tail -f /tmp/overwatch-debug.log | grep --line-buffered "X-RAY\|🔍\|detections"
```

### Watch Model Detection Logs
```bash
tail -f /tmp/overwatch-debug.log | grep --line-buffered "Model.*detected"
```

### Check WebSocket Connections
```bash
tail -f /tmp/overwatch-debug.log | grep --line-buffered "WebSocket\|Broadcasting"
```

### Count FPS from Logs
```bash
# In a 10-second window, count X-RAY frames sent
timeout 10 tail -f /tmp/overwatch-debug.log | grep -c "X-RAY frame sent"
```

## Performance Metrics

### Normal Performance
- Backend processing: 50-100ms per frame
- Frame encoding: 10-20ms
- Frame size: 30-60 KB
- Frontend rendering: <16ms (60 FPS)
- Total latency: <150ms

### Slow Performance
If you see:
- Processing > 200ms: Lower Processing FPS or use smaller batch size
- Frame size > 100 KB: Reduce JPEG quality or resolution
- Frontend render > 50ms: Close other browser tabs

## Test Workflow

### Quick Test
1. Open browser console
2. Look for "VideoPreview: WebSocket connected"
3. Click Execute
4. Within 2 seconds, look for "🔍 X-RAY View: Received xray_frame"
5. If yes → System working!
6. If no → Check backend logs for errors

### Deep Test
```bash
# Terminal 1: Watch backend
tail -f /tmp/overwatch-debug.log | grep -E "(🔍|X-RAY|Model.*detected)"

# Terminal 2: Watch WebSocket
tail -f /tmp/overwatch-debug.log | grep "Broadcasting"
```

Then in browser:
1. Open Console (F12)
2. Filter console to show only "X-RAY"
3. Execute workflow
4. Watch logs in all 3 places simultaneously

## Success Indicators

✅ **System is working if you see:**
1. Backend: "Model detected N objects" (where N > 0)
2. Backend: "✅ X-RAY frame sent"
3. Frontend: "✅ X-RAY View: Processing X-RAY frame!"
4. Frontend: "✅ Frame drawn!"
5. Visual: Bounding boxes visible in X-RAY View node
6. Stats: FPS counter updating, detection count > 0

## Getting Help

If X-RAY View still isn't working after checking all logs:

1. **Capture logs:**
```bash
# Save 30 seconds of logs
( tail -f /tmp/overwatch-debug.log & echo $! > /tmp/log_pid ) &
sleep 30
kill $(cat /tmp/log_pid)
tail -200 /tmp/overwatch-debug.log > xray-debug-$(date +%s).log
```

2. **Capture browser console:**
- Right-click in console
- "Save as..."
- Include timestamp

3. **Share:**
- Backend log file
- Browser console export
- Screenshot of workflow
- Description of what you're trying to do

## Tips

- **Refresh often:** If things get stuck, hard refresh (Cmd+Shift+R)
- **One thing at a time:** Test with simple workflow first (Video → Model → X-RAY)
- **Lower settings:** Start with low FPS (3-5) and increase once working
- **Check basics:** Is video playing? Is Execute button pressed? Is X-RAY mode ON?
- **Read logs:** They're very detailed now - the answer is usually there!

