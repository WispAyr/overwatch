## Mediabunny Integration Guide

## Overview

Overwatch uses [Mediabunny](https://mediabunny.dev/) for efficient video playback from RTSP camera streams. Mediabunny is a JavaScript library for media processing directly in the browser.

## Reference Documentation

For complete Mediabunny API documentation, download:
- **mediabunny.d.ts**: Complete TypeScript API definitions
- **llms.txt**: Indexed guide
- **llms-full.txt**: Complete guide

From: https://mediabunny.dev/llms

## Current Status

The frontend has a placeholder for Mediabunny integration in `frontend/js/mediabunny.js`. 

### What's Needed

1. **RTSP → WebRTC/HLS Conversion**
   RTSP streams cannot be played directly in browsers. You need to convert them:
   
   **Option A: WebRTC (Recommended)**
   - Use a WebRTC gateway (e.g., MediaMTX, Janus)
   - Low latency (<500ms)
   - Best for live monitoring
   
   **Option B: HLS**
   - Use FFmpeg to convert RTSP → HLS
   - Higher latency (2-10s)
   - Better browser compatibility

2. **Mediabunny Setup**
   ```bash
   npm install mediabunny
   ```

3. **Player Implementation**
   ```javascript
   import { MediaBunny } from 'mediabunny';
   
   const player = new MediaBunny({
       container: document.getElementById('video-container'),
       src: 'https://your-stream-url',
       autoplay: true,
       muted: true
   });
   ```

## RTSP Stream Conversion

### Using MediaMTX (Recommended)

MediaMTX is a real-time media server that can convert RTSP to WebRTC.

1. **Install MediaMTX**
   ```bash
   # Download from https://github.com/bluenviron/mediamtx/releases
   wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_amd64.tar.gz
   tar -xzf mediamtx_linux_amd64.tar.gz
   ```

2. **Configure MediaMTX**
   ```yaml
   # mediamtx.yml
   paths:
     cam-001:
       source: rtsp://camera-ip:554/stream
       sourceOnDemand: yes
   ```

3. **Start MediaMTX**
   ```bash
   ./mediamtx mediamtx.yml
   ```

4. **Access WebRTC Stream**
   ```
   http://localhost:8889/cam-001/whep
   ```

### Using FFmpeg + HLS

For HLS conversion:

```bash
# Convert RTSP to HLS
ffmpeg -i rtsp://camera:554/stream \
  -c:v copy -c:a copy \
  -f hls -hls_time 2 -hls_list_size 3 \
  -hls_flags delete_segments \
  /var/www/html/streams/camera1.m3u8
```

## Integration Example

Update `frontend/js/mediabunny.js`:

```javascript
class MediaBunnyPlayer {
    constructor(containerId, cameraId, streamUrl) {
        this.container = document.getElementById(containerId);
        this.cameraId = cameraId;
        this.streamUrl = streamUrl;
        this.player = null;
    }
    
    async initialize() {
        // Convert RTSP URL to WebRTC
        const webrtcUrl = await this.getWebRTCUrl(this.cameraId);
        
        // Initialize Mediabunny
        this.player = new MediaBunny({
            container: this.container,
            src: webrtcUrl,
            autoplay: true,
            muted: true,
            controls: true,
            width: '100%',
            height: '100%'
        });
        
        this.player.on('error', (error) => {
            console.error('Player error:', error);
            this.showError(error.message);
        });
        
        this.player.on('ready', () => {
            console.log('Player ready:', this.cameraId);
        });
    }
    
    async getWebRTCUrl(cameraId) {
        // Get WebRTC URL from backend
        const response = await fetch(`/api/streams/${cameraId}/webrtc`);
        const data = await response.json();
        return data.url;
    }
    
    showError(message) {
        this.container.innerHTML = `
            <div class="error-state">
                <p>Stream Error</p>
                <p class="text-sm">${message}</p>
            </div>
        `;
    }
    
    play() {
        if (this.player) this.player.play();
    }
    
    pause() {
        if (this.player) this.player.pause();
    }
    
    destroy() {
        if (this.player) {
            this.player.destroy();
            this.player = null;
        }
    }
}
```

## Backend Stream Endpoint

Add WebRTC URL endpoint to `backend/api/routes/streams.py`:

```python
@router.get("/{camera_id}/webrtc")
async def get_webrtc_url(camera_id: str, request: Request):
    """Get WebRTC URL for camera stream"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera = stream_manager.cameras[camera_id]
    
    # Convert RTSP to WebRTC URL (via MediaMTX or similar)
    webrtc_url = f"http://localhost:8889/{camera_id}/whep"
    
    return {
        'camera_id': camera_id,
        'url': webrtc_url,
        'type': 'webrtc'
    }
```

## Features to Implement

1. **Multi-Camera Grid**
   - Load multiple players simultaneously
   - Resource management (pause off-screen cameras)
   - Synchronized playback

2. **Stream Controls**
   - Play/Pause
   - Fullscreen
   - Volume control
   - Screenshot capture

3. **Detection Overlays**
   - Draw bounding boxes on video
   - Show confidence scores
   - Highlight zones

4. **Recording**
   - DVR-style playback
   - Clip export
   - Timeline scrubbing

## Performance Optimization

1. **Lazy Loading**
   - Only load visible cameras
   - Pause when scrolled out of view

2. **Quality Adaptation**
   - Lower quality for grid view
   - Full quality for fullscreen

3. **Connection Pooling**
   - Reuse WebRTC connections
   - Graceful reconnection

## Browser Compatibility

- **Chrome/Edge**: Full WebRTC support
- **Firefox**: Full WebRTC support
- **Safari**: WebRTC supported (iOS 14.3+)
- **Mobile**: Use HLS for better compatibility

## Next Steps

1. Set up MediaMTX or another RTSP → WebRTC gateway
2. Install Mediabunny: `npm install mediabunny`
3. Implement `MediaBunnyPlayer` class
4. Add backend WebRTC endpoint
5. Test with live cameras

## Resources

- Mediabunny: https://mediabunny.dev/
- MediaMTX: https://github.com/bluenviron/mediamtx
- WebRTC Samples: https://webrtc.github.io/samples/
- HLS.js: https://github.com/video-dev/hls.js/

