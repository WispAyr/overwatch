"""
Video streaming routes
Serves video frames as MJPEG stream
"""
import asyncio
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import cv2

from stream.fast_processor import get_processor


router = APIRouter()
logger = logging.getLogger('overwatch.api.video')

# Get global frame processor (uses C++ if available, falls back to Python)
frame_processor = get_processor()


async def generate_mjpeg_stream(camera_id: str, stream_manager):
    """Generate MJPEG stream from camera frames using buffered frames"""
    if camera_id not in stream_manager.streams:
        raise HTTPException(status_code=404, detail="Camera stream not found")
        
    stream = stream_manager.streams[camera_id]
    
    if not stream.running:
        raise HTTPException(status_code=503, detail="Camera not streaming")
    
    frame_interval = 1.0 / 30.0  # Target 30 FPS
    
    while True:
        try:
            # Get latest frame from buffer instead of reading directly
            frame = stream.get_latest_frame()
            
            if frame is None:
                # No frame available yet, wait and retry
                await asyncio.sleep(0.1)
                continue
                
            # Encode frame as JPEG using fast processor (2-6x faster with C++)
            try:
                jpeg_bytes = frame_processor.encode_jpeg(frame, quality=85)
            except Exception as e:
                logger.error(f"JPEG encoding failed: {e}")
                await asyncio.sleep(0.1)
                continue
                
            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
            
            # Control frame rate
            await asyncio.sleep(frame_interval)
            
        except Exception as e:
            logger.error(f"Error streaming camera {camera_id}: {e}")
            await asyncio.sleep(1)
            # Don't break - keep trying


@router.get("/{camera_id}/mjpeg")
async def get_mjpeg_stream(camera_id: str, request: Request):
    """Get MJPEG stream for a camera"""
    stream_manager = request.app.state.stream_manager
    
    return StreamingResponse(
        generate_mjpeg_stream(camera_id, stream_manager),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
    

@router.get("/{camera_id}/snapshot")
async def get_snapshot(camera_id: str, request: Request):
    """Get current frame snapshot"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.streams:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    stream = stream_manager.streams[camera_id]
    
    # Get latest frame from buffer
    frame = stream.get_latest_frame()
    
    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available")
        
    # Encode as JPEG using fast processor
    try:
        jpeg_bytes = frame_processor.encode_jpeg(frame, quality=95)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to encode image: {e}")
        
    from fastapi.responses import Response
    return Response(content=jpeg_bytes, media_type="image/jpeg")

