# 🚀 Quick Start Guide - Local Connect NOC

## Your Camera Configuration

✅ **Organization**: Local Connect  
✅ **Site**: NOC Location  
✅ **Area**: Outdoors  
✅ **Camera**: NOC Outdoor Camera 1  
✅ **Stream**: `rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp`  
✅ **Workflow**: People Detection (enabled)  

## Start Overwatch

### 1. Install Dependencies

```bash
# Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
npm install
```

### 2. Download AI Model

The system will auto-download YOLOv8n on first run, or download manually:

```bash
mkdir -p models
cd models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
cd ..
```

### 3. Build Frontend

```bash
npm run build:css
```

### 4. Start the Backend

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start Overwatch
python backend/main.py
```

You should see:
```
Starting Overwatch...
Loading 1 cameras...
Started stream: noc-outdoor-cam-01 (NOC Outdoor Camera 1)
Loaded 1 workflows...
API server: http://0.0.0.0:8000
Dashboard: http://localhost:7002
```

### 5. Start the Dashboard (New Terminal)

```bash
./scripts/start_dashboard.sh
```

Or manually:
```bash
python3 -m http.server 7002 --directory frontend
```

### 6. Access Dashboard

Open your browser:
```
http://localhost:7002
```

**Note**: Dashboard runs on port 7002 [[memory:6124235]]

You should see:
- ✅ 1 Active Camera
- ✅ Live event feed
- ✅ Organization tree showing "Local Connect → NOC Location → Outdoors"
- ✅ Camera in grid view

## Check Camera Stream

### Test RTSP Connection

```bash
# Using FFmpeg
ffmpeg -rtsp_transport tcp -i "rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp" -frames:v 1 test.jpg

# Using VLC
vlc "rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp"
```

### Check Stream Status

```bash
curl http://localhost:8000/api/streams/noc-outdoor-cam-01/status
```

Expected response:
```json
{
  "camera_id": "noc-outdoor-cam-01",
  "running": true,
  "fps": 24.5,
  "frame_count": 1234,
  "uptime": 60,
  "workflows": ["people_detection"]
}
```

## Monitor Detection Events

### Via Dashboard
- Go to "Events" tab
- See real-time people detections
- Filter by severity

### Via API
```bash
curl http://localhost:8000/api/events?limit=10
```

### Via Logs
```bash
tail -f logs/overwatch.log
```

## Troubleshooting

### Camera Not Connecting

1. **Check network connectivity**:
   ```bash
   ping 10.10.10.1
   ```

2. **Verify RTSP URL**:
   - Ensure credentials are correct
   - Check port 7441 is accessible
   - SRTP might need specific configuration

3. **Test with FFmpeg**:
   ```bash
   ffmpeg -rtsp_transport tcp -i "rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp" -f null -
   ```

4. **Check logs**:
   ```bash
   grep "noc-outdoor-cam-01" logs/overwatch.log
   ```

### No Detections Appearing

1. **Verify workflow is running**:
   ```bash
   curl http://localhost:8000/api/workflows/people_detection
   ```

2. **Check model downloaded**:
   ```bash
   ls -lh models/yolov8n.pt
   ```

3. **Lower confidence threshold** (in `config/workflows.yaml`):
   ```yaml
   detection:
     confidence: 0.5  # Lower from 0.7
   ```

### High CPU Usage

1. **Reduce processing FPS** (in `config/workflows.yaml`):
   ```yaml
   processing:
     fps: 5  # Lower from 10
   ```

2. **Use GPU if available** (in `.env`):
   ```bash
   DEVICE=cuda
   ```

## Adding More Cameras

Edit `config/hierarchy.yaml`:

```yaml
cameras:
  - id: noc-outdoor-cam-01
    name: "NOC Outdoor Camera 1"
    rtsp_url: "rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp"
    enabled: true
    workflows:
      - people_detection
      
  - id: noc-outdoor-cam-02  # NEW CAMERA
    name: "NOC Outdoor Camera 2"
    rtsp_url: "rtsps://10.10.10.2:7441/xxxxx"
    enabled: true
    workflows:
      - people_detection
```

Restart Overwatch to load new cameras.

## Next Steps

1. ✅ Verify camera stream is working
2. ✅ Check people detection events
3. Add more cameras to the NOC location
4. Set up additional sites (if needed)
5. Configure alerts/webhooks
6. Enable federation for distributed deployments
7. Set up ZeroTier for secure networking

## Support

Check documentation:
- [Architecture](docs/ARCHITECTURE.md)
- [Workflows](docs/WORKFLOWS.md)
- [API Reference](docs/API.md)
- [Federation](docs/FEDERATION.md)
- [ZeroTier](docs/ZEROTIER.md)

## Health Checks

```bash
# API health
curl http://localhost:8000/health

# System status
curl http://localhost:8000/api/system/status

# Camera list
curl http://localhost:8000/api/cameras

# Live events
curl http://localhost:8000/api/events?limit=5
```

---

**Ready to go! 🎯**

Start the backend, open the dashboard, and you should see your NOC outdoor camera streaming with people detection active!

