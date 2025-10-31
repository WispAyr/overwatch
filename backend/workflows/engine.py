"""
Workflow Engine
Manages AI processing workflows
"""
import asyncio
import logging
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

import yaml
import numpy as np

from core.config import settings
from .workflow import Workflow


logger = logging.getLogger('overwatch.workflows')


class WorkflowEngine:
    """Workflow execution engine"""
    
    def __init__(self, event_manager):
        self.event_manager = event_manager
        self.workflows: Dict[str, Workflow] = {}
        self._frame_queues: Dict[str, asyncio.Queue] = {}
        
    async def load_workflows(self):
        """Load workflow configurations"""
        config_path = Path(settings.WORKFLOWS_CONFIG)
        
        if not config_path.exists():
            logger.warning(f"Workflow config not found: {config_path}")
            logger.info("Using example config...")
            config_path = Path(settings.CONFIG_DIR) / "workflows.example.yaml"
            
        if not config_path.exists():
            logger.warning("No workflow configuration found")
            return
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        workflows = config.get('workflows', {})
        logger.info(f"Loading {len(workflows)} workflows...")
        
        for workflow_id, workflow_config in workflows.items():
            try:
                workflow = Workflow(
                    workflow_id=workflow_id,
                    config=workflow_config,
                    event_manager=self.event_manager
                )
                
                if workflow_config.get('enabled', True):
                    await workflow.initialize()
                    self.workflows[workflow_id] = workflow
                    logger.info(f"Loaded workflow: {workflow_id}")
                    
            except Exception as e:
                logger.error(f"Failed to load workflow {workflow_id}: {e}", exc_info=True)
                
        logger.info(f"Loaded {len(self.workflows)} workflows")
        
    async def process_frame(
        self,
        camera_id: str,
        workflow_id: str,
        frame: np.ndarray,
        timestamp: datetime
    ):
        """Process a frame through a workflow"""
        if workflow_id not in self.workflows:
            logger.warning(f"Workflow {workflow_id} not found")
            return
            
        workflow = self.workflows[workflow_id]
        
        try:
            await workflow.process_frame(
                camera_id=camera_id,
                frame=frame,
                timestamp=timestamp
            )
        except Exception as e:
            logger.error(
                f"Error in workflow {workflow_id} for camera {camera_id}: {e}",
                exc_info=True
            )
            
    async def cleanup(self):
        """Cleanup all workflows"""
        logger.info("Cleaning up workflows...")
        
        for workflow in self.workflows.values():
            try:
                await workflow.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up workflow: {e}")
                
        self.workflows.clear()

