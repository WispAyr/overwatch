# 🚀 Overwatch Quick Start

## One-Time Setup

Run the installation script:

```bash
cd /Users/ewanrichardson/Development/overwatch
./install.sh
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Build frontend CSS
- ✅ Download AI model
- ✅ Create data directories

## Running Overwatch

### Option 1: Use the run script (easiest)

```bash
# Terminal 1: Start backend
./run.sh

# Terminal 2: Start dashboard
./scripts/start_dashboard.sh
```

### Option 2: Manual start

```bash
# Terminal 1: Start backend (port 8000)
source venv/bin/activate
python backend/main.py

# Terminal 2: Start dashboard (port 7002)
python3 -m http.server 7002 --directory frontend

# Terminal 3 (Optional): Start workflow builder (port 7003)
cd workflow-builder
npm install
npm run dev
```

## Access Dashboard

Open browser: **http://localhost:7002**

Other access points:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Workflow Builder**: http://localhost:7003 (if running)

## Your Camera Setup

✅ **Camera**: NOC Outdoor Camera 1  
✅ **Location**: Local Connect → NOC Location → Outdoors  
✅ **Stream**: rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp  
✅ **Detection**: People detection (YOLOv8)  

## Troubleshooting

### "Module not found" errors
```bash
./install.sh
```

### Check if backend is running
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Check camera status
```bash
curl http://localhost:8000/api/cameras
```

### View logs
```bash
tail -f logs/overwatch.log
```

### Camera not connecting?
Test the RTSP stream:
```bash
ffmpeg -rtsp_transport tcp -i "rtsps://10.10.10.1:7441/uxHJV1J8px1TJR70?enableSrtp" -frames:v 1 test.jpg
```

## What You Should See

### Backend Terminal:
```
Starting Overwatch...
Initializing event manager...
Loading 1 workflows...
Loaded workflow: people_detection
Loading 1 cameras...
Connecting to noc-outdoor-cam-01...
Started stream: noc-outdoor-cam-01 (NOC Outdoor Camera 1)
Overwatch started successfully
API server: http://0.0.0.0:8000
Dashboard: http://localhost:7002
```

### Dashboard (http://localhost:7002):
- Active Cameras: 1
- Organization tree with "Local Connect"
- Camera grid showing NOC Outdoor Camera 1
- Live events feed

## Stop Overwatch

Press `Ctrl+C` in both terminal windows.

## Need Help?

Check the logs:
```bash
cat logs/overwatch.log
```

Test API:
```bash
# System status
curl http://localhost:8000/api/system/status

# Camera list  
curl http://localhost:8000/api/cameras

# Recent events
curl http://localhost:8000/api/events?limit=5
```

