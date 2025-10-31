# Debug Console Fix Summary

## Issue
Debug Console wasn't receiving messages from the realtime workflow executor.

## Root Causes Found

### 1. ✅ WebSocket Topic Filtering (CRITICAL)
**Problem**: WebSocket only allowed `{'events', 'alarms', 'streams'}` topics by default.  
**Fix**: Added `'debug_message'`, `'detection_data'`, `'status_update'`, `'metrics_update'` to default subscriptions.  
**File**: `backend/api/websocket.py` line 22

### 2. ✅ Wrong WebSocket URL  
**Problem**: Nodes connected to `ws://localhost:7003/api/ws` (Vite dev server) instead of backend.  
**Fix**: Changed to use `wsBaseUrl` from `config.ts` → `ws://localhost:8000/api/ws`  
**Files**: 
- `workflow-builder/src/nodes/DebugNode.jsx`
- `workflow-builder/src/nodes/DataPreviewNode.jsx`

### 3. ✅ Reconnect Loop
**Problem**: `getEdges` in dependency array caused WebSocket to reconnect every render.  
**Fix**: Removed `getEdges` from `useEffect` dependencies.  
**Files**:
- `workflow-builder/src/nodes/DebugNode.jsx` line 93
- `workflow-builder/src/nodes/DataPreviewNode.jsx` line 92

### 4. ✅ Recursive Node Search
**Problem**: Debug nodes connected through model weren't found.  
**Fix**: Added `_find_output_nodes_recursive()` to search up to 3 levels deep.  
**File**: `backend/workflows/realtime_executor.py`

### 5. ✅ Database Schema
**Problem**: Missing `version` and `schema_version` columns caused errors.  
**Fix**: Added columns via SQL ALTER TABLE and added `getattr()` fallbacks.  
**Files**:
- Database: `ALTER TABLE visual_workflows ADD COLUMN version/schema_version`
- `backend/api/routes/workflow_builder.py`

## Test Script

Run this to verify the fix:

```bash
cd /Users/ewanrichardson/Development/overwatch

# 1. Verify backend is running
lsof -i :8000 | grep LISTEN

# 2. Test WebSocket connection
python3 << 'EOF'
import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8000/api/ws") as ws:
        print("✅ WebSocket connected!")
        
        # Listen for 10 seconds
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            print(f"📨 Received: {msg}")
        except asyncio.TimeoutError:
            print("⏰ No messages (but connection works!)")

asyncio.run(test())
EOF

# 3. Check connected clients
python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')
from api.websocket import manager
print(f"Clients: {len(manager.connections)}")
EOF

# 4. Send test message
python3 << 'EOF'
import asyncio, sys
sys.path.insert(0, 'backend')

async def send():
    from api.websocket import manager
    await manager.broadcast({
        'type': 'debug_message',
        'node_id': 'YOUR_DEBUG_NODE_ID',  # Update with actual ID
        'message': 'TEST!',
        'detections': []
    })
    print("Sent!")

asyncio.run(send())
EOF
```

## Current Status

**Backend**: ✅ All fixes applied and running (PID 29814)  
**Frontend**: ⏳ Needs page refresh to load fixed DebugNode.jsx  
**Database**: ✅ Migration complete  
**WebSocket**: ⏳ Clients not staying connected

## Next Steps

1. **Hard refresh browser**: `Cmd+Shift+R` to clear cache
2. **Drag Debug node** to canvas
3. **Connect**: YouTube → Model → Debug
4. **Check console** for: `DebugNode xxx: WebSocket connected` (should stay connected)
5. **Click Execute**
6. **Watch for 🔔 emoji logs** in console showing messages

## Files Modified

- `backend/api/websocket.py` - Added workflow message types to default topics
- `backend/workflows/realtime_executor.py` - Recursive output node search
- `backend/api/routes/workflow_builder.py` - Database compatibility
- `workflow-builder/src/nodes/DebugNode.jsx` - Fix WebSocket URL & dependencies
- `workflow-builder/src/nodes/DataPreviewNode.jsx` - Fix WebSocket URL & dependencies
- `workflow-builder/src/config.ts` - Created (environment config)
- Database: Added version columns

## Known Issues

- YouTube frame retrieval via yt-dlp times out frequently
- No WebSocket heartbeat/ping implemented yet
- Messages only flow when detections actually occur (no frames = no messages)

---

**If messages still don't appear after hard refresh, check:**
1. Browser console for WebSocket connection status
2. Backend logs: `tail -f logs/overwatch.log | grep WebSocket`
3. Run test script above to verify WebSocket works


