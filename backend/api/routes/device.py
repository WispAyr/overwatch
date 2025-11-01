"""
Device Management API Routes
Handles device configuration, updates, and discovery
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel


router = APIRouter()


class DeviceSettingsUpdate(BaseModel):
    """Device settings update model"""
    autostart_enabled: Optional[bool] = None
    auto_update_enabled: Optional[bool] = None
    update_channel: Optional[str] = None
    max_cpu_percent: Optional[int] = None
    max_memory_percent: Optional[int] = None
    enable_gpu: Optional[bool] = None
    enable_discovery: Optional[bool] = None
    discovery_interval: Optional[int] = None
    auto_sync_enabled: Optional[bool] = None
    sync_workflows: Optional[bool] = None
    sync_cameras: Optional[bool] = None
    sync_rules: Optional[bool] = None
    max_recording_days: Optional[int] = None
    max_snapshot_days: Optional[int] = None
    auto_cleanup_enabled: Optional[bool] = None
    custom_settings: Optional[Dict[str, Any]] = None


@router.get("/info")
async def get_device_info(request: Request):
    """Get device information and configuration"""
    device_manager = request.app.state.device_manager
    
    return await device_manager.get_system_info()


@router.get("/config")
async def get_device_config(request: Request):
    """Get device configuration"""
    device_manager = request.app.state.device_manager
    
    return device_manager.config.to_dict()


@router.patch("/config")
async def update_device_config(
    settings: DeviceSettingsUpdate,
    request: Request
):
    """Update device configuration"""
    device_manager = request.app.state.device_manager
    
    # Convert to dict, removing None values
    settings_dict = {
        k: v for k, v in settings.dict().items()
        if v is not None
    }
    
    device_manager.config.update_settings(settings_dict)
    
    return {
        'success': True,
        'config': device_manager.config.to_dict()
    }


@router.get("/updates/check")
async def check_for_updates(request: Request):
    """Check for available updates"""
    device_manager = request.app.state.device_manager
    
    result = await device_manager.check_for_updates()
    
    return result


@router.post("/updates/apply")
async def apply_updates(
    restart: bool = False,
    request: Request = None
):
    """Apply available updates"""
    device_manager = request.app.state.device_manager
    
    result = await device_manager.apply_update(restart=restart)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Update failed'))
    
    return result


@router.get("/branch")
async def get_current_branch(request: Request):
    """Get current git branch"""
    device_manager = request.app.state.device_manager
    
    branch = await device_manager.get_current_branch()
    commit = await device_manager._get_current_commit()
    recommended_branch = device_manager.config.get_branch_for_device()
    
    return {
        'current_branch': branch,
        'current_commit': commit,
        'recommended_branch': recommended_branch,
        'is_recommended': branch == recommended_branch
    }


@router.post("/branch/switch")
async def switch_branch(
    branch: str,
    request: Request
):
    """Switch to a different branch"""
    device_manager = request.app.state.device_manager
    
    result = await device_manager.switch_branch(branch)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Branch switch failed'))
    
    return result


@router.post("/autostart/enable")
async def enable_autostart(request: Request):
    """Enable autostart on boot"""
    device_manager = request.app.state.device_manager
    
    result = await device_manager.enable_autostart()
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to enable autostart'))
    
    # Update config
    device_manager.config.update_settings({'autostart_enabled': True})
    
    return result


@router.post("/autostart/disable")
async def disable_autostart(request: Request):
    """Disable autostart on boot"""
    device_manager = request.app.state.device_manager
    
    result = await device_manager.disable_autostart()
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to disable autostart'))
    
    # Update config
    device_manager.config.update_settings({'autostart_enabled': False})
    
    return result


@router.post("/restart")
async def restart_system(
    delay: int = 5,
    request: Request = None
):
    """Restart the Overwatch system"""
    device_manager = request.app.state.device_manager
    
    # Schedule restart
    import asyncio
    asyncio.create_task(device_manager._schedule_restart(delay))
    
    return {
        'success': True,
        'message': f'System will restart in {delay} seconds',
        'restart_in': delay
    }


@router.get("/discovery/devices")
async def get_discovered_devices(request: Request):
    """Get devices discovered on local network"""
    discovery_service = request.app.state.discovery_service
    
    devices = discovery_service.get_discovered_devices()
    
    return {
        'devices': list(devices.values()),
        'count': len(devices)
    }


@router.get("/discovery/status")
async def get_discovery_status(request: Request):
    """Get discovery service status"""
    discovery_service = request.app.state.discovery_service
    
    return {
        'running': discovery_service._running,
        'device_id': discovery_service.device_id,
        'device_type': discovery_service.device_type,
        'port': discovery_service.port,
        'discovered_count': len(discovery_service.discovered_devices)
    }


@router.post("/discovery/scan")
async def trigger_discovery_scan(request: Request):
    """Trigger a manual discovery scan"""
    discovery_service = request.app.state.discovery_service
    
    if not discovery_service._running:
        raise HTTPException(status_code=400, detail="Discovery service not running")
    
    # The service continuously discovers, so just return current state
    devices = discovery_service.get_discovered_devices()
    
    return {
        'success': True,
        'devices': list(devices.values()),
        'count': len(devices)
    }

