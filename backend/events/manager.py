"""
Event Manager
Handles detection events and storage
"""
import logging
from typing import List, Optional
from datetime import datetime

from .storage import EventStorage
from api.websocket import broadcast_event


logger = logging.getLogger('overwatch.events')


class EventManager:
    """Manages detection events"""
    
    def __init__(self):
        self.storage = EventStorage()
        self._callbacks = []
        
    async def initialize(self):
        """Initialize event manager"""
        logger.info("Initializing event manager...")
        await self.storage.initialize()
        
    def subscribe(self, callback):
        """Subscribe to event creation"""
        self._callbacks.append(callback)
        
    async def create_event(self, event: dict):
        """Create a new event"""
        # Store event
        await self.storage.store_event(event)
        
        # Broadcast to connected clients
        await broadcast_event(event)
        
        # Notify subscribers
        for callback in self._callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        
        logger.info(
            f"Event created: {event['workflow_id']} on {event['camera_id']} "
            f"({len(event.get('detections', []))} detections)"
        )
        
    async def get_event(self, event_id: str) -> Optional[dict]:
        """Get a specific event"""
        return await self.storage.get_event(event_id)
        
    async def query_events(self, **kwargs) -> List[dict]:
        """Query events with filters"""
        return await self.storage.query_events(**kwargs)
        
    async def count_events(self, **kwargs) -> int:
        """Count events with filters"""
        return await self.storage.count_events(**kwargs)
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.storage.cleanup()

