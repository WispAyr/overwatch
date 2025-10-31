# Video Input Node - Enhancements Summary

**Date:** October 31, 2025  
**Status:** ✅ COMPLETE

---

## New Features Added

### 1. ✅ File Upload System
- Upload videos/images directly from the browser
- Automatic server-side storage in `./data/uploads/`
- File validation (video/* and image/* only)
- Upload progress indicator
- Success/error feedback

### 2. ✅ Server File Browser
- Browse previously uploaded files without re-uploading
- View file details:
  - File name
  - File size (formatted)
  - Upload date/time
- Click to select a file
- Refresh button to reload file list
- Delete files directly from browser (with confirmation)

### 3. ✅ Auto-Play on Workflow Execution
- Video automatically plays when workflow starts
- Video automatically pauses when workflow stops
- Real-time sync with workflow state via WebSocket
- Visual indicator showing "Playing" status

### 4. ✅ Live Video Preview
- See video playing in the node while workflow runs
- Progress bar with click-to-seek
- Play/pause controls
- Loop toggle
- Time display (current/duration)
- Playback speed control (0.1x - 2.0x)

---

## How to Use

### Upload a New Video

1. Click the **"📤 Upload"** button
2. Select a video or image file
3. Wait for "✅ Uploaded to server" message
4. File is ready to use

### Browse Server Files

1. Click the **"📁"** folder icon
2. Browse the list of uploaded files
3. Click a file to select it
4. File is ready to use immediately

### Delete a File

1. Open the file browser (📁 button)
2. Hover over a file in the list
3. Click the **🗑️** trash icon
4. Confirm deletion

### Run the Workflow

1. Ensure a file is selected (green checkmark shown)
2. Click **"Execute"** at the top right
3. Video will auto-play in the node preview
4. Data flows to connected nodes (YOLOv8N, Debug Console, etc.)

---

## UI Elements

### Buttons
- **📤 Upload** - Upload new file from computer
- **📁 Browse** - Browse files already on server
- **▶️ Play / ⏸️ Pause** - Manual playback control
- **🔄 Refresh** - Reload server file list
- **🗑️ Delete** - Remove file from server
- **👁️ Preview Toggle** - Show/hide video preview
- **⚙️ Config** - Show/hide configuration options

### Status Indicators
- **⏳ Uploading...** - File upload in progress
- **✅ Ready: filename** - File selected and ready
- **❌ Error message** - Upload or operation failed
- **🟢 Playing** - Workflow running, video playing

---

## Configuration Options

When you click the **⚙️** config button:

- **Processing FPS**: 1-60 fps (default: 30)
  - How many frames per second to process
  - Lower = faster but less detail
  - Higher = slower but more accurate

- **Playback Speed**: 0.1x - 2.0x (default: 1.0x)
  - Controls video playback speed
  - Also affects frame delivery rate

- **Skip Similar Frames**: On/Off
  - Skip frames that look similar to previous frame
  - Reduces processing load

---

## API Endpoints Used

### Upload File
```
POST /api/uploads/video
Content-Type: multipart/form-data
```

### List Files
```
GET /api/uploads/list
```

### Delete File
```
DELETE /api/uploads/video/{filename}
```

---

## Technical Details

### WebSocket Integration
- Listens to `ws://localhost:8000/api/ws`
- Tracks workflow state changes
- Auto-plays/pauses video based on workflow execution

### File Storage
- Server location: `./data/uploads/`
- Files persist between sessions
- Accessible from file browser in any workflow

### Supported Formats
- **Video**: MP4, MOV, AVI, WebM, etc.
- **Image**: JPG, PNG, GIF, etc.

---

## Example Workflow

1. **First Time Setup**:
   ```
   Upload → Select video.mp4 → ✅ Ready
   ```

2. **Subsequent Uses**:
   ```
   📁 Browse → Click video.mp4 → ✅ Ready
   ```

3. **Execute Workflow**:
   ```
   Execute → Video auto-plays → Data flows to YOLOv8N → Detections shown in Debug Console
   ```

---

## Benefits

✅ **No Re-uploading** - Use the same video across multiple workflow tests  
✅ **Quick Selection** - Browse and select from previously uploaded files  
✅ **Visual Feedback** - See the video playing as it's being processed  
✅ **Easy Management** - Delete unused files directly from the interface  
✅ **Auto-sync** - Video playback syncs with workflow execution state  

---

## Troubleshooting

### "No data flowing to Debug Console"
1. Check that file shows "✅ Ready: filename"
2. Click **Stop** then **Execute** to restart workflow with new file
3. Ensure nodes are properly connected

### "No files in browser"
1. Upload a file first using the Upload button
2. Click the 🔄 refresh button
3. Check backend is running on port 8000

### "Video not auto-playing"
1. Check workflow is running (green "Running" indicator)
2. Try manual play button (▶️)
3. Check browser console for WebSocket errors

---

## Status: Production Ready ✅

All features tested and working correctly.

