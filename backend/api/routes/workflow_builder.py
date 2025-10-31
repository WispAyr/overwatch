"""
Workflow Builder API
Save and load visual workflow configurations
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from core.database import get_db, Base
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from workflows.schema import SCHEMA_VERSION, redact_sensitive_data
from workflows.validator import WorkflowValidator
from workflows.event_bus import get_event_bus


router = APIRouter()
logger = logging.getLogger('overwatch.api.workflow_builder')


# Workflow configuration model (stored workflows from visual builder)
class VisualWorkflow(Base):
    """Visual workflow configuration"""
    __tablename__ = "visual_workflows"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    site_id = Column(String, nullable=True, index=True)  # Site-specific workflow
    site_name = Column(String, nullable=True)  # Denormalized site name
    is_master = Column(Integer, default=0, index=True)  # Master template flag
    status = Column(String, default='draft')  # draft, running, stopped
    created_by = Column(String, nullable=True)  # User who created it
    version = Column(String, default="1.0.0")
    schema_version = Column(String, default=SCHEMA_VERSION)
    nodes = Column(JSON, nullable=False)
    edges = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowCreate(BaseModel):
    """Workflow creation model"""
    id: str
    name: str
    description: Optional[str] = None
    site_id: Optional[str] = None
    version: Optional[str] = "1.0.0"
    nodes: list
    edges: list


@router.get("/", include_in_schema=False)
@router.get("")
async def list_workflows(db: Session = Depends(get_db)):
    """List all visual workflows"""
    workflows = db.query(VisualWorkflow).all()
    
    return {"workflows": [
        {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "site_id": wf.site_id,
            "version": getattr(wf, 'version', "1.0.0"),
            "schema_version": getattr(wf, 'schema_version', SCHEMA_VERSION),
            "node_count": len(wf.nodes),
            "edge_count": len(wf.edges),
            "created_at": wf.created_at.isoformat(),
            "updated_at": wf.updated_at.isoformat()
        }
        for wf in workflows
    ]}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Get workflow configuration"""
    workflow = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "site_id": workflow.site_id,
        "version": getattr(workflow, 'version', "1.0.0"),
        "schema_version": getattr(workflow, 'schema_version', SCHEMA_VERSION),
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "created_at": workflow.created_at.isoformat(),
        "updated_at": workflow.updated_at.isoformat()
    }


@router.post("/")
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """Create new workflow with validation"""
    existing = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Workflow already exists")
    
    # Validate workflow graph
    validator = WorkflowValidator(workflow.nodes, workflow.edges)
    is_valid, errors, warnings = validator.validate()
    
    if not is_valid:
        logger.error(f"Workflow validation failed: {errors}")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Workflow validation failed",
                "errors": errors,
                "warnings": warnings
            }
        )
    
    # Log warnings but don't block creation
    if warnings:
        logger.warning(f"Workflow {workflow.id} has warnings: {warnings}")
    
    # Scrub sensitive data from logs
    safe_data = redact_sensitive_data({
        "id": workflow.id,
        "name": workflow.name,
        "node_count": len(workflow.nodes),
        "edge_count": len(workflow.edges)
    })
    logger.info(f"Creating workflow: {safe_data}")
    
    new_workflow = VisualWorkflow(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        site_id=workflow.site_id,
        version=workflow.version or "1.0.0",
        schema_version=SCHEMA_VERSION,
        nodes=workflow.nodes,
        edges=workflow.edges
    )
    
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    
    return {
        "message": "Workflow created",
        "id": new_workflow.id,
        "warnings": warnings if warnings else None
    }


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    workflow: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """Update workflow with validation"""
    existing = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Validate workflow graph
    validator = WorkflowValidator(workflow.nodes, workflow.edges)
    is_valid, errors, warnings = validator.validate()
    
    if not is_valid:
        logger.error(f"Workflow validation failed: {errors}")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Workflow validation failed",
                "errors": errors,
                "warnings": warnings
            }
        )
    
    if warnings:
        logger.warning(f"Workflow {workflow_id} has warnings: {warnings}")
    
    # Scrub sensitive data from logs
    safe_data = redact_sensitive_data({
        "id": workflow_id,
        "name": workflow.name,
        "node_count": len(workflow.nodes),
        "edge_count": len(workflow.edges)
    })
    logger.info(f"Updating workflow: {safe_data}")
    
    existing.name = workflow.name
    existing.description = workflow.description
    existing.site_id = workflow.site_id
    # Only update version if column exists
    if hasattr(existing, 'version'):
        existing.version = workflow.version or getattr(existing, 'version', "1.0.0")
    existing.nodes = workflow.nodes
    existing.edges = workflow.edges
    existing.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Workflow updated",
        "warnings": warnings if warnings else None
    }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Delete workflow"""
    workflow = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    db.delete(workflow)
    db.commit()
    
    return {"message": "Workflow deleted"}


@router.post("/{workflow_id}/deploy")
async def deploy_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Convert visual workflow to YAML and deploy with validation and diffing"""
    workflow = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Validate workflow before deploy
    validator = WorkflowValidator(workflow.nodes, workflow.edges)
    is_valid, errors, warnings = validator.validate()
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot deploy invalid workflow",
                "errors": errors,
                "warnings": warnings
            }
        )
        
    # Convert visual workflow to executable configuration
    from workflows.visual_executor import VisualWorkflowExecutor
    import yaml
    from pathlib import Path
    
    executor = VisualWorkflowExecutor()
    workflow_config = executor.parse_visual_workflow(workflow.nodes, workflow.edges)
    
    # Add version headers (with fallback for old DB schemas)
    workflow_config['version'] = getattr(workflow, 'version', "1.0.0")
    workflow_config['schema_version'] = getattr(workflow, 'schema_version', SCHEMA_VERSION)
    workflow_config['deployed_at'] = datetime.utcnow().isoformat()
    
    # Save to YAML
    output_path = f"config/workflows/{workflow_id}.yaml"
    
    # Load existing YAML if present for diffing
    existing_yaml = None
    diff = None
    if Path(output_path).exists():
        try:
            with open(output_path, 'r') as f:
                existing_yaml = f.read()
                existing_config = yaml.safe_load(existing_yaml)
                
            # Simple diff (list changes)
            diff = _compute_yaml_diff(existing_config, workflow_config)
        except Exception as e:
            logger.warning(f"Could not load existing YAML for diff: {e}")
    
    executor.save_to_yaml(workflow_config, output_path)
    
    logger.info(f"Deployed workflow {workflow_id} to {output_path}")
    
    return {
        "message": "Workflow deployed",
        "workflow_id": workflow_id,
        "config_path": output_path,
        "workflows": workflow_config.get('workflows', []),
        "warnings": warnings if warnings else None,
        "diff": diff
    }


@router.post("/{workflow_id}/preview")
async def preview_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Preview the generated YAML configuration with validation"""
    workflow = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Validate workflow
    validator = WorkflowValidator(workflow.nodes, workflow.edges)
    is_valid, errors, warnings = validator.validate()
        
    from workflows.visual_executor import VisualWorkflowExecutor
    import yaml
    from pathlib import Path
    
    executor = VisualWorkflowExecutor()
    workflow_config = executor.parse_visual_workflow(workflow.nodes, workflow.edges)
    
    # Add version headers (with fallback for old DB schemas)
    workflow_config['version'] = getattr(workflow, 'version', "1.0.0")
    workflow_config['schema_version'] = getattr(workflow, 'schema_version', SCHEMA_VERSION)
    
    # Convert to YAML string
    yaml_str = yaml.dump(workflow_config, default_flow_style=False, sort_keys=False)
    
    # Load existing YAML if present for diffing
    output_path = f"config/workflows/{workflow_id}.yaml"
    diff = None
    if Path(output_path).exists():
        try:
            with open(output_path, 'r') as f:
                existing_config = yaml.safe_load(f)
            diff = _compute_yaml_diff(existing_config, workflow_config)
        except Exception as e:
            logger.warning(f"Could not load existing YAML for diff: {e}")
    
    return {
        "workflow_id": workflow_id,
        "yaml": yaml_str,
        "config": workflow_config,
        "is_valid": is_valid,
        "errors": errors if errors else None,
        "warnings": warnings if warnings else None,
        "diff": diff
    }


def _compute_yaml_diff(old_config: dict, new_config: dict) -> dict:
    """Compute simple diff between two YAML configs"""
    changes = {
        "added": [],
        "removed": [],
        "modified": []
    }
    
    # Compare workflow counts
    old_workflows = old_config.get('workflows', [])
    new_workflows = new_config.get('workflows', [])
    
    old_camera_ids = {wf.get('camera_id') for wf in old_workflows}
    new_camera_ids = {wf.get('camera_id') for wf in new_workflows}
    
    added_cameras = new_camera_ids - old_camera_ids
    removed_cameras = old_camera_ids - new_camera_ids
    
    for cam_id in added_cameras:
        changes["added"].append(f"Camera workflow: {cam_id}")
        
    for cam_id in removed_cameras:
        changes["removed"].append(f"Camera workflow: {cam_id}")
        
    # Check for modifications in common cameras
    for cam_id in old_camera_ids & new_camera_ids:
        old_wf = next((wf for wf in old_workflows if wf.get('camera_id') == cam_id), None)
        new_wf = next((wf for wf in new_workflows if wf.get('camera_id') == cam_id), None)
        
        if old_wf and new_wf:
            if old_wf.get('model') != new_wf.get('model'):
                changes["modified"].append(f"{cam_id}: Model changed")
            if old_wf.get('actions') != new_wf.get('actions'):
                changes["modified"].append(f"{cam_id}: Actions changed")
            if old_wf.get('zones') != new_wf.get('zones'):
                changes["modified"].append(f"{cam_id}: Zones changed")
                
    return changes


@router.post("/execute")
async def execute_workflow_realtime(workflow: WorkflowCreate):
    """Execute workflow in real-time (for testing/preview without saving)"""
    from workflows.realtime_executor import RealtimeWorkflowExecutor
    
    # IMPORTANT: Stop all existing workflows first to prevent duplicates
    await RealtimeWorkflowExecutor.stop_all_workflows()
    
    # Create executor for this workflow
    executor = RealtimeWorkflowExecutor(
        nodes=workflow.nodes,
        edges=workflow.edges,
        workflow_id=workflow.id
    )
    
    # Start execution (non-blocking)
    await executor.start()
    
    return {
        "message": "Workflow execution started",
        "workflow_id": workflow.id,
        "status": "running"
    }


@router.post("/{workflow_id}/execute")
async def execute_saved_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Execute a saved workflow in real-time"""
    workflow = db.query(VisualWorkflow).filter(VisualWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    from workflows.realtime_executor import RealtimeWorkflowExecutor
    
    executor = RealtimeWorkflowExecutor(
        nodes=workflow.nodes,
        edges=workflow.edges,
        workflow_id=workflow_id
    )
    
    await executor.start()
    
    return {
        "message": "Workflow execution started",
        "workflow_id": workflow_id,
        "status": "running"
    }


@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str):
    """Stop a running workflow"""
    from workflows.realtime_executor import RealtimeWorkflowExecutor
    
    await RealtimeWorkflowExecutor.stop_workflow(workflow_id)
    
    return {
        "message": "Workflow stopped",
        "workflow_id": workflow_id
    }


@router.post("/stop-all")
async def stop_all_workflows():
    """Stop all running workflows (cleanup endpoint)"""
    from workflows.realtime_executor import RealtimeWorkflowExecutor
    
    await RealtimeWorkflowExecutor.stop_all_workflows()
    
    return {
        "message": "All workflows stopped"
    }


@router.get("/status")
async def workflow_status():
    """Get status of all running workflows"""
    from workflows.realtime_executor import _running_workflows
    
    return {
        "running_workflows": len(_running_workflows),
        "workflow_ids": list(_running_workflows.keys())
    }


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get detailed real-time status for a specific workflow"""
    from workflows.realtime_executor import _running_workflows
    from time import time
    
    # Check if workflow is running
    if workflow_id not in _running_workflows:
        return {
            "workflow_id": workflow_id,
            "state": "stopped",
            "uptime": 0,
            "fps": 0,
            "total_detections": 0,
            "error_count": 0,
            "warning_count": 0,
            "detections_per_minute": 0,
            "latest_error": None,
            "error_timestamp": None,
            "node_metrics": {}
        }
    
    # Get runtime data
    runtime = _running_workflows[workflow_id]
    start_time = runtime.get("start_time", time())
    uptime = int(time() - start_time)
    
    return {
        "workflow_id": workflow_id,
        "state": runtime.get("state", "running"),
        "uptime": uptime,
        "fps": runtime.get("fps", 0),
        "total_detections": runtime.get("total_detections", 0),
        "error_count": runtime.get("error_count", 0),
        "warning_count": runtime.get("warning_count", 0),
        "detections_per_minute": runtime.get("detections_per_minute", 0),
        "latest_error": runtime.get("latest_error"),
        "error_timestamp": runtime.get("error_timestamp"),
        "node_metrics": runtime.get("node_metrics", {}),
        "frames_processed": runtime.get("frames_processed", 0),
        "last_detection_time": runtime.get("last_detection_time")
    }

