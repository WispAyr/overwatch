"""
Configuration API
Manage which models and nodes are available to users
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from pathlib import Path

router = APIRouter()

CONFIG_FILE = Path("config/workflow_config.json")

class ComponentConfig(BaseModel):
    id: str
    enabled: bool
    version: str
    requirements: List[str] = []
    notes: Optional[str] = None

class WorkflowConfig(BaseModel):
    models: List[ComponentConfig]
    nodes: List[ComponentConfig]
    global_settings: Dict = {}

def load_config() -> WorkflowConfig:
    """Load workflow configuration from file"""
    if not CONFIG_FILE.exists():
        # Create default config
        default_config = {
            "models": [
                {
                    "id": "ultralytics-yolov8n",
                    "enabled": True,
                    "version": "8.0.0",
                    "requirements": ["ultralytics>=8.0.0"],
                    "notes": "Fast, lightweight detection"
                },
                {
                    "id": "ultralytics-yolov8s",
                    "enabled": True,
                    "version": "8.0.0",
                    "requirements": ["ultralytics>=8.0.0"],
                    "notes": "Balanced speed/accuracy"
                },
                {
                    "id": "ultralytics-yolov8m",
                    "enabled": True,
                    "version": "8.0.0",
                    "requirements": ["ultralytics>=8.0.0"],
                    "notes": "Higher accuracy"
                }
            ],
            "nodes": [
                {
                    "id": "camera",
                    "enabled": True,
                    "version": "1.0.0",
                    "requirements": ["opencv-python"],
                    "notes": "Live camera streams"
                },
                {
                    "id": "videoInput",
                    "enabled": True,
                    "version": "1.0.0",
                    "requirements": [],
                    "notes": "Upload video/image files"
                },
                {
                    "id": "youtube",
                    "enabled": True,
                    "version": "1.0.0",
                    "requirements": ["yt-dlp"],
                    "notes": "YouTube live streams and videos"
                }
            ],
            "global_settings": {
                "max_models_per_workflow": 10,
                "enable_experimental": False,
                "auto_update_models": False
            }
        }
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(default_config, indent=2))
        return WorkflowConfig(**default_config)
    
    config_data = json.loads(CONFIG_FILE.read_text())
    return WorkflowConfig(**config_data)

def save_config(config: WorkflowConfig):
    """Save workflow configuration to file"""
    CONFIG_FILE.write_text(config.json(indent=2))

@router.get("/")
async def get_workflow_config():
    """Get current workflow configuration"""
    config = load_config()
    return config

@router.put("/")
async def update_workflow_config(config: WorkflowConfig):
    """Update workflow configuration"""
    save_config(config)
    return {"status": "success", "message": "Configuration updated"}

@router.post("/models/{model_id}/toggle")
async def toggle_model(model_id: str):
    """Enable/disable a specific model"""
    config = load_config()
    
    for model in config.models:
        if model.id == model_id:
            model.enabled = not model.enabled
            save_config(config)
            return {"status": "success", "enabled": model.enabled}
    
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

@router.post("/nodes/{node_id}/toggle")
async def toggle_node(node_id: str):
    """Enable/disable a specific node type"""
    config = load_config()
    
    for node in config.nodes:
        if node.id == node_id:
            node.enabled = not node.enabled
            save_config(config)
            return {"status": "success", "enabled": node.enabled}
    
    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

@router.get("/enabled-models")
async def get_enabled_models():
    """Get list of enabled models only"""
    config = load_config()
    enabled = [m for m in config.models if m.enabled]
    return {"models": enabled, "count": len(enabled)}

@router.get("/enabled-nodes")
async def get_enabled_nodes():
    """Get list of enabled node types only"""
    config = load_config()
    enabled = [n for n in config.nodes if n.enabled]
    return {"nodes": enabled, "count": len(enabled)}

@router.post("/check-requirements")
async def check_requirements():
    """Check if all requirements are installed"""
    import importlib
    import pkg_resources
    
    config = load_config()
    results = {
        "models": {},
        "nodes": {}
    }
    
    # Check model requirements
    for model in config.models:
        if not model.enabled:
            continue
            
        requirements_met = []
        for req in model.requirements:
            try:
                pkg_name = req.split('>=')[0].split('==')[0]
                importlib.import_module(pkg_name.replace('-', '_'))
                requirements_met.append({"requirement": req, "installed": True})
            except ImportError:
                requirements_met.append({"requirement": req, "installed": False})
        
        results["models"][model.id] = {
            "enabled": model.enabled,
            "requirements": requirements_met,
            "all_met": all(r["installed"] for r in requirements_met)
        }
    
    # Check node requirements
    for node in config.nodes:
        if not node.enabled:
            continue
            
        requirements_met = []
        for req in node.requirements:
            try:
                pkg_name = req.split('>=')[0].split('==')[0]
                importlib.import_module(pkg_name.replace('-', '_'))
                requirements_met.append({"requirement": req, "installed": True})
            except ImportError:
                requirements_met.append({"requirement": req, "installed": False})
        
        results["nodes"][node.id] = {
            "enabled": node.enabled,
            "requirements": requirements_met,
            "all_met": all(r["installed"] for r in requirements_met) if requirements_met else True
        }
    
    return results


