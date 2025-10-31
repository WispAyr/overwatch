"""
Workflow management API routes
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict


router = APIRouter()


@router.get("/")
async def list_workflows(request: Request):
    """List all workflows"""
    workflow_engine = request.app.state.workflow_engine
    
    workflows = []
    for workflow_id, workflow in workflow_engine.workflows.items():
        workflows.append({
            'id': workflow_id,
            **workflow.get_info()
        })
        
    return {"workflows": workflows}
    

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request):
    """Get workflow details"""
    workflow_engine = request.app.state.workflow_engine
    
    if workflow_id not in workflow_engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    workflow = workflow_engine.workflows[workflow_id]
    
    return {
        'id': workflow_id,
        **workflow.get_info()
    }


@router.get("/drone/list")
async def list_drone_workflows(request: Request):
    """List all drone workflows"""
    drone_workflow_manager = getattr(request.app.state, 'drone_workflow_manager', None)
    if not drone_workflow_manager:
        raise HTTPException(status_code=503, detail="Drone workflow manager not available")
    
    return drone_workflow_manager.list_workflows()


@router.post("/drone/{workflow_id}/start")
async def start_drone_workflow(workflow_id: str, workflow_config: Dict, request: Request):
    """Start a drone workflow"""
    drone_workflow_manager = getattr(request.app.state, 'drone_workflow_manager', None)
    if not drone_workflow_manager:
        raise HTTPException(status_code=503, detail="Drone workflow manager not available")
    
    try:
        await drone_workflow_manager.start_workflow(workflow_id, workflow_config)
        return {"status": "started", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drone/{workflow_id}/stop")
async def stop_drone_workflow(workflow_id: str, request: Request):
    """Stop a drone workflow"""
    drone_workflow_manager = getattr(request.app.state, 'drone_workflow_manager', None)
    if not drone_workflow_manager:
        raise HTTPException(status_code=503, detail="Drone workflow manager not available")
    
    try:
        await drone_workflow_manager.stop_workflow(workflow_id)
        return {"status": "stopped", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/drone/{workflow_id}/status")
async def get_drone_workflow_status(workflow_id: str, request: Request):
    """Get drone workflow status"""
    drone_workflow_manager = getattr(request.app.state, 'drone_workflow_manager', None)
    if not drone_workflow_manager:
        raise HTTPException(status_code=503, detail="Drone workflow manager not available")
    
    status = drone_workflow_manager.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return status

