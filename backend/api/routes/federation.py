"""
Federation API routes
Handles server-to-server communication
"""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime

from core.config import settings


router = APIRouter()


# Simple service auth dependency (Comment 4)
async def require_service_auth(request: Request):
    """Require authentication for federation endpoints"""
    if not settings.ENABLE_AUTH:
        return True
    
    # Check for Authorization header or API key
    auth_header = request.headers.get('Authorization')
    api_key = request.headers.get('X-API-Key')
    
    if not auth_header and not api_key:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # TODO: Implement proper service credential validation
    # For now, just require presence of auth header
    return True


class NodeRegistration(BaseModel):
    """Node registration model"""
    node_id: str
    node_type: str  # 'central' or 'edge'
    url: str
    metadata: Optional[dict] = None
    

class NodeHeartbeat(BaseModel):
    """Node heartbeat model"""
    node_id: str
    timestamp: str
    status: str
    

class FederatedEvent(BaseModel):
    """Federated event model"""
    event_id: str
    source_node: str
    camera_id: str
    workflow_id: str
    timestamp: str
    severity: str
    detections: list
    

@router.post("/register")
async def register_node(
    node: NodeRegistration,
    request: Request,
    auth=Depends(require_service_auth)  # Comment 4
):
    """Register a federated node"""
    federation_manager = request.app.state.federation_manager
    
    success = await federation_manager.register_node(node.dict())
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to register node")
        
    return {"message": "Node registered", "node_id": node.node_id}
    

@router.post("/unregister")
async def unregister_node(node_id: str, request: Request):
    """Unregister a federated node"""
    federation_manager = request.app.state.federation_manager
    
    success = await federation_manager.unregister_node(node_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
        
    return {"message": "Node unregistered"}
    

@router.post("/heartbeat")
async def heartbeat(
    heartbeat: NodeHeartbeat,
    request: Request,
    auth=Depends(require_service_auth)  # Comment 4
):
    """Receive heartbeat from federated node"""
    federation_manager = request.app.state.federation_manager
    
    if heartbeat.node_id in federation_manager.nodes:
        node = federation_manager.nodes[heartbeat.node_id]
        node.last_heartbeat = datetime.utcnow()
        
    return {"status": "acknowledged"}
    

@router.post("/events")
async def receive_event(
    event: FederatedEvent,
    request: Request,
    auth=Depends(require_service_auth)  # Comment 4
):
    """Receive event from federated node"""
    event_manager = request.app.state.event_manager
    
    # Store event locally
    event_data = {
        'id': event.event_id,
        'camera_id': event.camera_id,
        'workflow_id': event.workflow_id,
        'timestamp': datetime.fromisoformat(event.timestamp),
        'severity': event.severity,
        'detections': event.detections,
        'metadata': {
            'source_node': event.source_node,
            'federated': True
        }
    }
    
    await event_manager.create_event(event_data)
    
    return {"message": "Event received", "event_id": event.event_id}
    

@router.get("/cluster/status")
async def get_cluster_status(request: Request):
    """Get status of all nodes in the federation"""
    federation_manager = request.app.state.federation_manager
    
    status = await federation_manager.get_cluster_status()
    
    return status
    

@router.get("/cluster/nodes")
async def list_nodes(request: Request):
    """List all federated nodes"""
    federation_manager = request.app.state.federation_manager
    
    nodes = []
    for node_id, node in federation_manager.nodes.items():
        nodes.append({
            'node_id': node_id,
            'node_type': node.node_type,
            'url': node.url,
            'metadata': node.metadata,
            'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None
        })
        
    return {'nodes': nodes}
    

@router.post("/sync/hierarchy")
async def sync_hierarchy(request: Request):
    """Sync hierarchy from central server (edge nodes)"""
    federation_manager = request.app.state.federation_manager
    
    if federation_manager.node_type != 'edge':
        raise HTTPException(
            status_code=400,
            detail="Only edge nodes can sync hierarchy"
        )
        
    hierarchy = await federation_manager.sync_hierarchy()
    
    return hierarchy

