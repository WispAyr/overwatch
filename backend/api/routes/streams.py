"""
Stream control API routes
"""
from fastapi import APIRouter, Request, HTTPException


router = APIRouter()


@router.get("/{camera_id}/status")
async def get_stream_status(camera_id: str, request: Request):
    """Get stream status"""
    stream_manager = request.app.state.stream_manager
    
    status = stream_manager.get_stream_status(camera_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    return {
        'camera_id': camera_id,
        **status
    }
    

@router.post("/{camera_id}/start")
async def start_stream(camera_id: str, request: Request):
    """Start a camera stream"""
    stream_manager = request.app.state.stream_manager
    
    success = await stream_manager.start_stream(camera_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start stream")
        
    return {"message": "Stream started", "camera_id": camera_id}
    

@router.post("/{camera_id}/stop")
async def stop_stream(camera_id: str, request: Request):
    """Stop a camera stream"""
    stream_manager = request.app.state.stream_manager
    
    success = await stream_manager.stop_stream(camera_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop stream")
        
    return {"message": "Stream stopped", "camera_id": camera_id}
    

@router.get("/{camera_id}/url")
async def get_stream_url(camera_id: str, request: Request):
    """Get stream URL for playback"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera = stream_manager.cameras[camera_id]
    
    return {
        'camera_id': camera_id,
        'rtsp_url': camera['rtsp_url']
    }

