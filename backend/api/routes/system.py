"""
System status API routes
"""
import time
import psutil
from fastapi import APIRouter, Request


router = APIRouter()

start_time = time.time()


@router.get("/status")
async def get_system_status(request: Request):
    """Get system status"""
    stream_manager = request.app.state.stream_manager
    event_manager = request.app.state.event_manager
    
    # CPU and memory
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    # GPU info (if available)
    gpu_usage = 0.0
    try:
        import torch
        if torch.cuda.is_available():
            gpu_usage = torch.cuda.utilization()
    except:
        pass
        
    # Count active streams
    active_streams = sum(
        1 for item in stream_manager.get_all_status()
        if item and item.get('status') and item.get('status', {}).get('running', False)
    )
    
    # Count workflows
    active_workflows = len(request.app.state.workflow_engine.workflows)
    
    # Total events
    total_events = await event_manager.count_events()
    
    return {
        'status': 'healthy',
        'uptime': int(time.time() - start_time),
        'cpu_usage': cpu_percent,
        'memory_usage': memory.percent,
        'gpu_usage': gpu_usage,
        'active_streams': active_streams,
        'active_workflows': active_workflows,
        'total_events': total_events
    }
    

@router.get("/metrics")
async def get_system_metrics(request: Request):
    """Get detailed system metrics (Comment 8 - includes ZeroTier metrics)"""
    stream_manager = request.app.state.stream_manager
    federation_manager = request.app.state.federation_manager
    
    streams = stream_manager.get_all_status()
    
    metrics = {
        'streams': streams,
        'cpu_percent': psutil.cpu_percent(interval=0.1, percpu=True),
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'percent': psutil.disk_usage('/').percent
        }
    }
    
    # Add overlay network metrics (Comment 8)
    if federation_manager and federation_manager.overlay_provider:
        overlay_status = await federation_manager.overlay_provider.status()
        if overlay_status.get('enabled'):
            metrics['overlay'] = {
                'provider': overlay_status.get('provider'),
                'online': overlay_status.get('online'),
                'peer_count': overlay_status.get('peer_count', 0),
                'member_count': overlay_status.get('member_count', 0),
                'has_error': overlay_status.get('last_error') is not None
            }
    
    return metrics

