"""
Workflow Templates/Subflows API
CRUD operations for reusable workflow templates
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from core.database import get_db, Base
from sqlalchemy import Column, String, Text, DateTime, JSON


router = APIRouter()
logger = logging.getLogger('overwatch.api.workflow_templates')


# Template/Subflow model
class WorkflowTemplate(Base):
    """Workflow template/subflow configuration"""
    __tablename__ = "workflow_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # e.g., "detection", "notification", "filter"
    version = Column(String, default="1.0.0")
    parameters = Column(JSON, default=list)  # Parameter definitions
    nodes = Column(JSON, nullable=False)
    edges = Column(JSON, nullable=False)
    inputs = Column(JSON, default=list)  # Input node IDs
    outputs = Column(JSON, default=list)  # Output node IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateCreate(BaseModel):
    """Template creation model"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = "1.0.0"
    parameters: List[dict] = []
    nodes: list
    edges: list
    inputs: List[str] = []
    outputs: List[str] = []


@router.get("/")
async def list_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all workflow templates"""
    query = db.query(WorkflowTemplate)
    
    if category:
        query = query.filter(WorkflowTemplate.category == category)
    
    templates = query.all()
    
    return {"templates": [
        {
            "id": tpl.id,
            "name": tpl.name,
            "description": tpl.description,
            "category": tpl.category,
            "version": tpl.version,
            "parameter_count": len(tpl.parameters),
            "node_count": len(tpl.nodes),
            "created_at": tpl.created_at.isoformat(),
            "updated_at": tpl.updated_at.isoformat()
        }
        for tpl in templates
    ]}


@router.get("/{template_id}")
async def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get template configuration"""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "version": template.version,
        "parameters": template.parameters,
        "nodes": template.nodes,
        "edges": template.edges,
        "inputs": template.inputs,
        "outputs": template.outputs,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat()
    }


@router.post("/")
async def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """Create new template"""
    existing = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Template already exists")
    
    logger.info(f"Creating template: {template.id}")
    
    new_template = WorkflowTemplate(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        version=template.version,
        parameters=template.parameters,
        nodes=template.nodes,
        edges=template.edges,
        inputs=template.inputs,
        outputs=template.outputs
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    return {"message": "Template created", "id": new_template.id}


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Update template"""
    existing = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    logger.info(f"Updating template: {template_id}")
    
    existing.name = template.name
    existing.description = template.description
    existing.category = template.category
    existing.version = template.version
    existing.parameters = template.parameters
    existing.nodes = template.nodes
    existing.edges = template.edges
    existing.inputs = template.inputs
    existing.outputs = template.outputs
    existing.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Template updated"}


@router.delete("/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete template"""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted"}


@router.post("/{template_id}/instantiate")
async def instantiate_template(
    template_id: str,
    parameters: dict = {},
    position: dict = {"x": 0, "y": 0},
    db: Session = Depends(get_db)
):
    """
    Instantiate a template with given parameters
    Returns nodes and edges with parameters applied
    """
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create instance nodes and edges
    import copy
    import uuid
    
    instance_id = str(uuid.uuid4())[:8]
    
    # Deep copy nodes and edges
    nodes = copy.deepcopy(template.nodes)
    edges = copy.deepcopy(template.edges)
    
    # Map old node IDs to new ones
    node_id_map = {}
    for node in nodes:
        old_id = node['id']
        new_id = f"{old_id}_{instance_id}"
        node_id_map[old_id] = new_id
        node['id'] = new_id
        
        # Offset position
        node['position']['x'] += position.get('x', 0)
        node['position']['y'] += position.get('y', 0)
        
        # Apply parameters to node data
        node_data = node.get('data', {})
        for param_name, param_value in parameters.items():
            if param_name in node_data:
                node_data[param_name] = param_value
    
    # Update edge IDs
    for edge in edges:
        edge['id'] = f"{edge['id']}_{instance_id}"
        edge['source'] = node_id_map.get(edge['source'], edge['source'])
        edge['target'] = node_id_map.get(edge['target'], edge['target'])
    
    return {
        "nodes": nodes,
        "edges": edges,
        "instance_id": instance_id,
        "template_id": template_id
    }


