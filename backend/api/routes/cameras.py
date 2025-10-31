"""
Camera management API routes
"""
from typing import List
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel


router = APIRouter()


class CameraCreate(BaseModel):
    """Camera creation model"""
    id: str
    sublocation_id: str
    name: str
    rtsp_url: str
    type: str = "generic"
    sensor_type: str = "camera"
    enabled: bool = True
    workflows: List[str] = []
    

class CameraUpdate(BaseModel):
    """Camera update model"""
    name: str = None
    rtsp_url: str = None
    enabled: bool = None
    workflows: List[str] = None
    

@router.post("/reload")
async def reload_cameras(request: Request):
    """Reload cameras from database"""
    stream_manager = request.app.state.stream_manager
    await stream_manager.load_cameras()
    return {
        "message": "Cameras reloaded",
        "count": len(stream_manager.cameras)
    }


@router.get("/")
async def list_cameras(request: Request):
    """List all cameras"""
    stream_manager = request.app.state.stream_manager
    
    cameras = []
    for camera_id, camera in stream_manager.cameras.items():
        status = stream_manager.get_stream_status(camera_id)
        cameras.append({
            **camera,
            'status': status or {'running': False}
        })
        
    return {"cameras": cameras}
    

@router.get("/{camera_id}")
async def get_camera(camera_id: str, request: Request):
    """Get camera details"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera = stream_manager.cameras[camera_id]
    status = stream_manager.get_stream_status(camera_id)
    
    return {
        **camera,
        'status': status or {'running': False}
    }
    

@router.post("/")
async def create_camera(camera: CameraCreate, request: Request):
    """Create a new camera"""
    stream_manager = request.app.state.stream_manager
    
    camera_dict = camera.dict()
    success = await stream_manager.add_camera(camera_dict)
    
    if not success:
        raise HTTPException(status_code=409, detail="Camera already exists")
        
    return {"message": "Camera created", "camera": camera_dict}
    

@router.put("/{camera_id}")
async def update_camera(camera_id: str, camera: CameraUpdate, request: Request):
    """Update camera configuration"""
    stream_manager = request.app.state.stream_manager
    
    if camera_id not in stream_manager.cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    # Update camera config
    current = stream_manager.cameras[camera_id]
    update_data = camera.dict(exclude_unset=True)
    current.update(update_data)
    
    # Restart stream if running
    if camera_id in stream_manager.streams:
        await stream_manager.stop_stream(camera_id)
        if current.get('enabled', True):
            await stream_manager.start_stream(camera_id)
            
    return {"message": "Camera updated", "camera": current}
    

@router.delete("/{camera_id}")
async def delete_camera(camera_id: str, request: Request):
    """Delete a camera"""
    stream_manager = request.app.state.stream_manager
    
    success = await stream_manager.remove_camera(camera_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    return {"message": "Camera deleted"}

