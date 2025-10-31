# Complete System Restart Guide

## Quick Restart

**Stop everything and restart cleanly:**

```bash
cd /Users/ewanrichardson/Development/overwatch
./restart-all.sh
```

This will:
1. ✅ Kill all existing processes
2. ✅ Free up all ports (7001, 7002, 7003, 8000, 8554)
3. ✅ Start Backend API (port 8000)
4. ✅ Start Dashboard (port 7002)
5. ✅ Start Workflow Builder (port 7003)

## Access After Restart

Once running, open these URLs:

| Service | URL | Description |
|---------|-----|-------------|
| 🔧 Backend API | http://localhost:8000 | FastAPI backend |
| 📚 API Docs | http://localhost:8000/docs | Swagger documentation |
| 🎛️ Dashboard | http://localhost:7002 | Main UI (alarms, cameras, etc.) |
| 🎨 Workflow Builder | http://localhost:7003 | Visual workflow editor |

## Just Stop Everything

```bash
./stop-all.sh
```

## Manual Restart (if scripts fail)

### Terminal 1: Backend
```bash
cd /Users/ewanrichardson/Development/overwatch
./run.sh
```

### Terminal 2: Dashboard
```bash
cd /Users/ewanrichardson/Development/overwatch
./scripts/start_dashboard.sh
```

### Terminal 3: Workflow Builder
```bash
cd /Users/ewanrichardson/Development/overwatch
./scripts/start_workflow_builder.sh
```

## Check What's Running

```bash
# Check all ports
lsof -i :8000  # Backend
lsof -i :7002  # Dashboard
lsof -i :7003  # Workflow Builder

# Check processes
ps aux | grep -E "backend/main|http.server|vite"
```

## View Logs

```bash
# All logs
tail -f logs/*.log

# Individual logs
tail -f logs/backend.log
tail -f logs/dashboard.log
tail -f logs/workflow-builder.log
```

## Troubleshooting

### Port Already in Use

```bash
# Kill specific port
lsof -ti:8000 | xargs kill -9   # Backend
lsof -ti:7002 | xargs kill -9   # Dashboard
lsof -ti:7003 | xargs kill -9   # Workflow Builder
```

### Backend Won't Start

```bash
# Check Python environment
source venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"

# Reinstall if needed
./install.sh
```

### Workflow Builder Won't Start

```bash
cd workflow-builder

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Start manually
npm run dev
```

### Dashboard Won't Load

```bash
# Rebuild CSS
npm run build:css

# Start manually
python3 -m http.server 7002 --directory frontend
```

## Fresh Start (Nuclear Option)

If everything is broken:

```bash
# 1. Stop everything
./stop-all.sh

# 2. Kill all ports
lsof -ti:8000,7001,7002,7003,8554 | xargs kill -9

# 3. Clean logs
rm -f logs/*.log

# 4. Restart
./restart-all.sh

# 5. Wait 10 seconds for everything to initialize

# 6. Open browser
open http://localhost:7002
open http://localhost:7003
```

## Port Reference

| Port | Service | Process |
|------|---------|---------|
| 8000 | Backend API | python backend/main.py |
| 7001 | Dashboard (alt) | http.server |
| 7002 | Dashboard (main) | http.server |
| 7003 | Workflow Builder | npm run dev (Vite) |
| 8554 | MediaMTX RTSP | mediamtx |
| 1935 | MediaMTX RTMP | mediamtx |
| 8888 | MediaMTX WebRTC | mediamtx |

## Common Issues

### "Connection Refused" in Browser

**Problem**: Backend not running  
**Solution**: `./restart-all.sh` or check `logs/backend.log`

### Workflow Builder Shows Blank Page

**Problem**: Vite dev server crashed  
**Solution**: 
```bash
cd workflow-builder
npm run dev
```

### Admin Panel Dropdowns Empty

**Problem**: Backend not responding or data not loaded  
**Solution**: Wait for backend to fully start (check http://localhost:8000/api/system/status)

### CSS Not Loading

**Problem**: Tailwind not built  
**Solution**: `npm run build:css`

## Success Indicators

After `./restart-all.sh`, you should see:

✅ Backend API responds: `curl http://localhost:8000/api/system/status`  
✅ Dashboard loads: http://localhost:7002 shows UI  
✅ Workflow Builder loads: http://localhost:7003 shows editor  
✅ No errors in browser console (F12)  
✅ WebSocket connects (check browser console)  

## Quick Test

```bash
# After restart, test all endpoints
curl http://localhost:8000/api/system/status
curl http://localhost:8000/api/hierarchy/tree
curl http://localhost:8000/api/cameras/
curl http://localhost:8000/api/organizations/

# All should return JSON (not connection errors)
```

## Summary

**Best practice**: Use `./restart-all.sh` for clean restarts  
**Logs location**: `logs/` directory  
**Stop cleanly**: `./stop-all.sh` before manual restarts  
**Wait time**: ~10 seconds for all services to fully initialize  

