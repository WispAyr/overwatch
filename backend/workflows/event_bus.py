"""
Workflow Event Bus
Centralized event handling for node lifecycle, status updates, and error handling
"""
import asyncio
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict


logger = logging.getLogger('overwatch.workflows.event_bus')


class EventType(Enum):
    """Event types for workflow execution"""
    # Node lifecycle events
    NODE_STARTED = "node_started"
    NODE_PROCESSING = "node_processing"
    NODE_COMPLETED = "node_completed"
    NODE_ERROR = "node_error"
    NODE_PAUSED = "node_paused"
    NODE_RESUMED = "node_resumed"
    
    # Workflow lifecycle events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_STOPPED = "workflow_stopped"
    WORKFLOW_ERROR = "workflow_error"
    
    # Data flow events
    FRAME_RECEIVED = "frame_received"
    DETECTIONS_EMITTED = "detections_emitted"
    ACTION_TRIGGERED = "action_triggered"
    
    # Audio events
    AUDIO_EXTRACTED = "audio_extracted"
    AUDIO_TRANSCRIBED = "audio_transcribed"
    SOUND_DETECTED = "sound_detected"
    KEYWORD_DETECTED = "keyword_detected"
    
    # Status events
    STATUS_UPDATE = "status_update"
    METRICS_UPDATE = "metrics_update"


@dataclass
class WorkflowEvent:
    """Base event class"""
    event_type: EventType
    workflow_id: str
    node_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'event_type': self.event_type.value,
            'workflow_id': self.workflow_id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }


class WorkflowEventBus:
    """
    In-process event bus for workflow events
    Supports pub/sub pattern for node lifecycle and status events
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task = None
        
        # Event history (limited size)
        self._history: List[WorkflowEvent] = []
        self._history_max_size = 1000
        
        # Per-node status tracking
        self._node_status: Dict[str, Dict] = {}
        
    async def start(self):
        """Start event bus processing"""
        if self._running:
            return
            
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
        
    async def stop(self):
        """Stop event bus processing"""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Event bus stopped")
        
    def subscribe(self, event_type: EventType, callback: Callable):
        """
        Subscribe to event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
            
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")
        
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
                
    async def emit(self, event: WorkflowEvent):
        """
        Emit event to bus
        
        Args:
            event: Event to emit
        """
        await self._event_queue.put(event)
        
        # Add to history
        self._history.append(event)
        if len(self._history) > self._history_max_size:
            self._history.pop(0)
            
        # Update node status if applicable
        if event.node_id:
            self._update_node_status(event)
            
    async def emit_status(self, workflow_id: str, node_id: str, status: str, meta: Dict = None):
        """
        Emit status update event
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            status: Status string (e.g., 'running', 'idle', 'error')
            meta: Additional metadata
        """
        event = WorkflowEvent(
            event_type=EventType.STATUS_UPDATE,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data={
                'status': status,
                **(meta or {})
            }
        )
        await self.emit(event)
        
    async def emit_error(self, workflow_id: str, node_id: str, error: Exception, meta: Dict = None):
        """
        Emit error event
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            error: Exception that occurred
            meta: Additional metadata
        """
        event = WorkflowEvent(
            event_type=EventType.NODE_ERROR,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'recoverable': self._is_recoverable(error),
                **(meta or {})
            }
        )
        await self.emit(event)
        
    async def emit_complete(self, workflow_id: str, node_id: str, stats: Dict = None):
        """
        Emit completion event
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            stats: Processing statistics
        """
        event = WorkflowEvent(
            event_type=EventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data={
                'stats': stats or {}
            }
        )
        await self.emit(event)
        
    async def emit_metrics(self, workflow_id: str, node_id: str, metrics: Dict):
        """
        Emit metrics update
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            metrics: Metrics dictionary (fps, latency, queue_size, etc.)
        """
        event = WorkflowEvent(
            event_type=EventType.METRICS_UPDATE,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data=metrics
        )
        await self.emit(event)
    
    async def emit_audio_result(self, workflow_id: str, node_id: str, result_type: str, data: Dict):
        """
        Emit audio processing result
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            result_type: Type of result ('transcription' or 'sound_classification')
            data: Audio result data
        """
        if result_type == 'transcription':
            event_type = EventType.AUDIO_TRANSCRIBED
        elif result_type == 'sound_classification':
            event_type = EventType.SOUND_DETECTED
        else:
            event_type = EventType.AUDIO_EXTRACTED
        
        event = WorkflowEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            data=data
        )
        await self.emit(event)
    
    async def emit_keyword_alert(self, workflow_id: str, node_id: str, keywords: List[str], transcript: str, timestamp: datetime):
        """
        Emit keyword detection alert
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            keywords: List of detected keywords
            transcript: Full transcript text
            timestamp: Time of detection
        """
        event = WorkflowEvent(
            event_type=EventType.KEYWORD_DETECTED,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=timestamp,
            data={
                'keywords': keywords,
                'transcript': transcript,
                'keyword_count': len(keywords)
            }
        )
        await self.emit(event)
    
    async def emit_sound_alert(self, workflow_id: str, node_id: str, sound_class: str, confidence: float, timestamp: datetime):
        """
        Emit sound detection alert
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            sound_class: Detected sound class
            confidence: Detection confidence
            timestamp: Time of detection
        """
        event = WorkflowEvent(
            event_type=EventType.SOUND_DETECTED,
            workflow_id=workflow_id,
            node_id=node_id,
            timestamp=timestamp,
            data={
                'sound_class': sound_class,
                'confidence': confidence
            }
        )
        await self.emit(event)
        
    def get_node_status(self, node_id: str) -> Optional[Dict]:
        """Get current status of a node"""
        return self._node_status.get(node_id)
        
    def get_workflow_events(self, workflow_id: str, limit: int = 100) -> List[Dict]:
        """Get recent events for workflow"""
        events = [
            e for e in reversed(self._history)
            if e.workflow_id == workflow_id
        ][:limit]
        
        return [e.to_dict() for e in events]
        
    async def _process_events(self):
        """Process events from queue"""
        try:
            while self._running:
                try:
                    # Get event with timeout to allow checking _running flag
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=0.5
                    )
                    
                    # Notify subscribers
                    await self._notify_subscribers(event)
                    
                except asyncio.TimeoutError:
                    continue
                    
        except asyncio.CancelledError:
            logger.info("Event processor cancelled")
            
    async def _notify_subscribers(self, event: WorkflowEvent):
        """Notify all subscribers of event"""
        subscribers = self._subscribers.get(event.event_type, [])
        
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}", exc_info=True)
        
        # Also broadcast to WebSocket for UI
        await self._broadcast_to_websocket(event)
    
    async def _broadcast_to_websocket(self, event: WorkflowEvent):
        """Broadcast event to WebSocket clients for UI display"""
        try:
            from api.websocket import manager
            
            # Convert event to debug-friendly WebSocket message format
            # Debug nodes expect: type, node_id, workflow_id, timestamp, message
            event_type_str = event.event_type.value
            
            # Convert event to debug message format
            if event.event_type in [EventType.NODE_STARTED, EventType.NODE_COMPLETED, EventType.NODE_PROCESSING]:
                # Send as debug_message for debug nodes
                ws_message = {
                    'type': 'debug_message',
                    'node_id': event.node_id,
                    'workflow_id': event.workflow_id,
                    'timestamp': event.timestamp.isoformat(),
                    'message': f"📍 {event_type_str.upper()}: {event.data}",
                    'event_data': event.data
                }
            elif event.event_type == EventType.DETECTIONS_EMITTED:
                # Send as detection_data
                ws_message = {
                    'type': 'debug_message',
                    'node_id': event.node_id,
                    'workflow_id': event.workflow_id,
                    'timestamp': event.timestamp.isoformat(),
                    'message': f"🎯 Detections: {event.data.get('count', 0)} objects (filtered from {event.data.get('total_before_filter', 0)})",
                    'detections': event.data.get('detections', []),
                    'event_data': event.data
                }
            elif event.event_type == EventType.NODE_ERROR:
                # Send as node_error
                ws_message = {
                    'type': 'node_error',
                    'node_id': event.node_id,
                    'workflow_id': event.workflow_id,
                    'timestamp': event.timestamp.isoformat(),
                    'message': f"❌ ERROR: {event.data.get('error_message', 'Unknown error')}",
                    'error': event.data
                }
            elif event.event_type == EventType.STATUS_UPDATE:
                ws_message = {
                    'type': 'status_update',
                    'node_id': event.node_id,
                    'workflow_id': event.workflow_id,
                    'timestamp': event.timestamp.isoformat(),
                    'status': event.data
                }
            else:
                # Generic format for other events
                ws_message = {
                    'type': 'debug_message',
                    'node_id': event.node_id,
                    'workflow_id': event.workflow_id,
                    'timestamp': event.timestamp.isoformat(),
                    'message': f"📡 {event_type_str}: {event.data}",
                    'event_data': event.data
                }
            
            # Broadcast to all connected clients
            logger.info(f"📡 Broadcasting to WebSocket: type={ws_message.get('type')}, node_id={ws_message.get('node_id')}")
            await manager.broadcast(ws_message)
            logger.info(f"✅ Broadcast complete")
            
        except Exception as e:
            logger.error(f"❌ Could not broadcast to WebSocket: {e}", exc_info=True)
                
    def _update_node_status(self, event: WorkflowEvent):
        """Update internal node status based on event"""
        node_id = event.node_id
        
        if node_id not in self._node_status:
            self._node_status[node_id] = {
                'status': 'idle',
                'last_update': None,
                'error_count': 0,
                'metrics': {}
            }
            
        status = self._node_status[node_id]
        status['last_update'] = event.timestamp
        
        if event.event_type == EventType.NODE_STARTED:
            status['status'] = 'running'
            
        elif event.event_type == EventType.NODE_COMPLETED:
            status['status'] = 'idle'
            
        elif event.event_type == EventType.NODE_ERROR:
            status['status'] = 'error'
            status['error_count'] += 1
            status['last_error'] = event.data.get('error_message')
            
        elif event.event_type == EventType.STATUS_UPDATE:
            status['status'] = event.data.get('status', status['status'])
            
        elif event.event_type == EventType.METRICS_UPDATE:
            status['metrics'].update(event.data)
            
    def _is_recoverable(self, error: Exception) -> bool:
        """Determine if error is recoverable"""
        # Network errors are generally recoverable
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
            
        # Value errors might be recoverable
        if isinstance(error, ValueError):
            return True
            
        # Runtime errors are typically not recoverable
        if isinstance(error, RuntimeError):
            return False
            
        # Default to non-recoverable
        return False


# Global event bus instance
_event_bus: Optional[WorkflowEventBus] = None


def get_event_bus() -> WorkflowEventBus:
    """Get global event bus instance"""
    global _event_bus
    
    if _event_bus is None:
        _event_bus = WorkflowEventBus()
        
    return _event_bus


async def init_event_bus():
    """Initialize global event bus"""
    bus = get_event_bus()
    await bus.start()
    return bus


async def shutdown_event_bus():
    """Shutdown global event bus"""
    global _event_bus
    
    if _event_bus:
        await _event_bus.stop()
        _event_bus = None

