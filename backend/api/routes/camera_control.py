"""
Camera Control Routes
Handle camera stream quality switching and controls
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel


router = APIRouter()


class StreamQualityChange(BaseModel):
    """Stream quality change model"""
    quality: str  # low, medium, high
    

@router.post("/{camera_id}/quality")
async def change_stream_quality(
    camera_id: str,
    quality_change: StreamQualityChange,
    request: Request
):
    """Change camera stream quality"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera = stream_manager.cameras[camera_id]
    streams = camera.get('streams', {})
    
    if not streams:
        raise HTTPException(status_code=400, detail="Camera does not support multi-resolution")
        
    if quality_change.quality not in streams:
        available = list(streams.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Quality '{quality_change.quality}' not available. Available: {available}"
        )
    
    # Stop current stream
    was_running = camera_id in stream_manager.streams
    if was_running:
        await stream_manager.stop_stream(camera_id)
        
    # Update camera config with new URL
    new_url = streams[quality_change.quality]['url']
    camera['rtsp_url'] = new_url
    camera['active_stream'] = quality_change.quality
    
    # Update database
    from core.database import SessionLocal, Camera
    db = SessionLocal()
    try:
        db_cam = db.query(Camera).filter(Camera.id == camera_id).first()
        if db_cam:
            db_cam.active_stream = quality_change.quality
            db.commit()
    finally:
        db.close()
    
    # Restart stream if it was running
    if was_running:
        await stream_manager.start_stream(camera_id)
        
    return {
        "message": "Stream quality changed",
        "camera_id": camera_id,
        "quality": quality_change.quality,
        "resolution": streams[quality_change.quality].get('resolution'),
        "url": new_url
    }
    

@router.get("/{camera_id}/quality")
async def get_stream_quality(camera_id: str, request: Request):
    """Get current stream quality and available options"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera = stream_manager.cameras[camera_id]
    streams = camera.get('streams', {})
    
    if not streams:
        return {
            "supports_multi_resolution": False,
            "active": "default",
            "available": []
        }
        
    return {
        "supports_multi_resolution": True,
        "active": camera.get('active_stream', 'medium'),
        "available": {
            quality: {
                "resolution": info.get('resolution'),
                "bitrate": info.get('bitrate')
            }
            for quality, info in streams.items()
        }
    }


