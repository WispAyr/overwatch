"""
Drone Workflow Manager
Manages lifecycle of drone detection workflows
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from workflows.drone_executor import DroneWorkflowExecutor

logger = logging.getLogger(__name__)


class DroneWorkflowManager:
    """
    Manages drone workflow executors
    Similar to realtime workflow engine but for drone-specific workflows
    """
    
    def __init__(self, drone_event_manager, alarm_manager=None):
        self.drone_event_manager = drone_event_manager
        self.alarm_manager = alarm_manager
        self.executors: Dict[str, DroneWorkflowExecutor] = {}
        
    async def start_workflow(self, workflow_id: str, workflow_config: Dict):
        """Create and start a drone workflow executor"""
        if workflow_id in self.executors:
            logger.warning(f"Drone workflow {workflow_id} already running, stopping first")
            await self.stop_workflow(workflow_id)
        
        # Create executor
        executor = DroneWorkflowExecutor(
            workflow_id=workflow_id,
            workflow_config=workflow_config,
            drone_event_manager=self.drone_event_manager,
            alarm_manager=self.alarm_manager
        )
        
        # Start executor
        await executor.start()
        
        # Track executor
        self.executors[workflow_id] = executor
        
        logger.info(f"Started drone workflow: {workflow_id}")
    
    async def stop_workflow(self, workflow_id: str):
        """Stop a drone workflow executor"""
        if workflow_id not in self.executors:
            raise ValueError(f"Drone workflow {workflow_id} not found")
        
        executor = self.executors[workflow_id]
        await executor.stop()
        
        del self.executors[workflow_id]
        
        logger.info(f"Stopped drone workflow: {workflow_id}")
    
    async def stop_all(self):
        """Stop all drone workflow executors"""
        workflow_ids = list(self.executors.keys())
        
        for workflow_id in workflow_ids:
            try:
                await self.stop_workflow(workflow_id)
            except Exception as e:
                logger.error(f"Error stopping drone workflow {workflow_id}: {e}")
    
    def list_workflows(self) -> Dict:
        """List all active drone workflows"""
        workflows = []
        
        for workflow_id, executor in self.executors.items():
            workflows.append({
                "workflow_id": workflow_id,
                "running": executor.running,
                **executor.get_stats()
            })
        
        return {
            "total": len(workflows),
            "workflows": workflows
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get status of a specific drone workflow"""
        executor = self.executors.get(workflow_id)
        
        if not executor:
            return None
        
        return {
            "workflow_id": workflow_id,
            "running": executor.running,
            **executor.get_stats()
        }
    
    async def cleanup(self):
        """Cleanup all workflows on shutdown"""
        await self.stop_all()

