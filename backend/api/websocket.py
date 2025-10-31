"""
WebSocket server for real-time updates
Enhanced with topic subscriptions and backpressure
"""
import asyncio
import logging
import json
from typing import Set, Dict, List
from collections import deque
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


logger = logging.getLogger('overwatch.websocket')
websocket_router = APIRouter()


class Connection:
    """Enhanced WebSocket connection with topic subscriptions and buffering"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.topics: Set[str] = {
            'events', 'alarms', 'streams',  # Legacy topics
            'debug_message', 'detection_data', 'status_update', 'metrics_update',  # Workflow messages
            'node_error', 'node_started', 'node_processing', 'node_completed',  # Event bus events
            'frame_received', 'detections_emitted', 'action_triggered',
            'drone_detections', 'drone_detection'  # Drone detection topics
        }  # Default subscriptions - accept all message types
        self.filters: Dict[str, any] = {}
        self.buffer = deque(maxlen=100)  # Bounded buffer
        self.last_activity = asyncio.get_event_loop().time()
        self.drone_filters: Dict[str, any] = {}  # Drone-specific filters (geofence_id, drone_id)
        self.last_sent_per_drone: Dict[str, float] = {}  # Rate limiting per drone ID
        
    async def send(self, message: dict):
        """Send message with backpressure handling"""
        try:
            if len(self.buffer) >= 90:  # Near capacity
                logger.warning("Connection buffer near capacity, dropping old messages")
                
            self.buffer.append(message)
            await self.websocket.send_text(json.dumps(message))
            self.last_activity = asyncio.get_event_loop().time()
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
            
    def matches_filters(self, message: dict) -> bool:
        """Check if message matches connection filters"""
        # Check topic subscription
        topic = message.get('type', '').replace('.', '_')
        if topic and topic not in self.topics:
            return False
            
        # Apply general filters
        if 'tenant' in self.filters:
            if message.get('tenant') != self.filters['tenant']:
                return False
                
        if 'site' in self.filters:
            if message.get('site') != self.filters['site']:
                return False
                
        if 'camera_id' in self.filters:
            if message.get('camera_id') != self.filters['camera_id']:
                return False
        
        # Apply drone-specific filters
        if topic in ('drone_detection', 'drone_detections'):
            if 'drone_id' in self.drone_filters:
                drone_data = message.get('data', {})
                if drone_data.get('remote_id') != self.drone_filters['drone_id']:
                    return False
            
            if 'geofence_id' in self.drone_filters:
                drone_data = message.get('data', {})
                violations = drone_data.get('geofence_violations', [])
                if self.drone_filters['geofence_id'] not in violations:
                    return False
                
        return True


class ConnectionManager:
    """Manage WebSocket connections with topic-based routing"""
    
    def __init__(self):
        self.connections: Set[Connection] = set()
        self.drone_detection_rate_limit = 2.0  # Hz - max 2 updates per second per drone
        self.drone_detection_min_interval = 1.0 / self.drone_detection_rate_limit
        
    async def connect(self, websocket: WebSocket):
        """Accept a new connection"""
        await websocket.accept()
        conn = Connection(websocket)
        self.connections.add(conn)
        logger.info(f"Client connected. Total: {len(self.connections)}")
        return conn
        
    def disconnect(self, connection: Connection):
        """Remove a connection"""
        self.connections.discard(connection)
        logger.info(f"Client disconnected. Total: {len(self.connections)}")
        
    async def broadcast(self, message: dict, topic: str = None):
        """Broadcast message to subscribed clients with optional rate limiting"""
        if not self.connections:
            logger.warning(f"No WebSocket connections to broadcast to. Message type: {message.get('type')}")
            return
            
        if topic:
            message['type'] = topic
        
        logger.info(f"📤 Broadcasting: type={message.get('type')}, node_id={message.get('node_id')}, clients={len(self.connections)}")
        
        # Apply rate limiting for drone detection topics
        is_drone_topic = topic in ('drone_detection', 'drone_detections')
        current_time = asyncio.get_event_loop().time()
            
        dead_connections = set()
        
        sent_count = 0
        filtered_count = 0
        
        for connection in self.connections:
            try:
                if connection.matches_filters(message):
                    # Apply rate limiting for drone detections
                    if is_drone_topic:
                        drone_id = message.get('data', {}).get('remote_id')
                        if drone_id:
                            last_sent = connection.last_sent_per_drone.get(drone_id, 0)
                            time_since_last = current_time - last_sent
                            
                            # Skip if sent too recently
                            if time_since_last < self.drone_detection_min_interval:
                                continue
                            
                            # Update last sent time
                            connection.last_sent_per_drone[drone_id] = current_time
                            
                            # Cleanup old entries (keep last 1000)
                            if len(connection.last_sent_per_drone) > 1000:
                                sorted_items = sorted(
                                    connection.last_sent_per_drone.items(),
                                    key=lambda x: x[1]
                                )
                                connection.last_sent_per_drone = dict(sorted_items[-1000:])
                    
                    await connection.send(message)
                    sent_count += 1
                else:
                    filtered_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                dead_connections.add(connection)
                
        # Remove dead connections
        for connection in dead_connections:
            self.disconnect(connection)
        
        logger.info(f"✅ Broadcast complete: sent={sent_count}, filtered={filtered_count}")
            
    async def cleanup_idle_connections(self, timeout: int = 300):
        """Cleanup idle connections (default 5 min timeout)"""
        current_time = asyncio.get_event_loop().time()
        dead_connections = set()
        
        for connection in self.connections:
            if current_time - connection.last_activity > timeout:
                logger.info("Closing idle connection")
                dead_connections.add(connection)
                
        for connection in dead_connections:
            try:
                await connection.websocket.close()
            except:
                pass
            self.disconnect(connection)


manager = ConnectionManager()


@websocket_router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with topic subscriptions"""
    logger.info(f"🔌 WebSocket connection attempt from {websocket.client}")
    connection = await manager.connect(websocket)
    logger.info(f"✅ WebSocket connected! Total clients: {len(manager.connections)}")
    logger.info(f"   Connection topics: {connection.topics}")
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get('type')
                
                if msg_type == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong'}))
                    
                elif msg_type == 'subscribe':
                    # Update subscriptions
                    topics = message.get('topics', [])
                    if topics:
                        connection.topics = set(topics)
                        logger.info(f"Client subscribed to: {topics}")
                        
                    # Update filters
                    filters = message.get('filters', {})
                    if filters:
                        connection.filters.update(filters)
                        logger.info(f"Client filters updated: {filters}")
                    
                    # Update drone filters
                    drone_filters = message.get('drone_filters', {})
                    if drone_filters:
                        connection.drone_filters.update(drone_filters)
                        logger.info(f"Client drone filters updated: {drone_filters}")
                        
                    await websocket.send_text(json.dumps({
                        'type': 'subscribed',
                        'topics': list(connection.topics),
                        'filters': connection.filters,
                        'drone_filters': connection.drone_filters
                    }))
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                
    except WebSocketDisconnect:
        manager.disconnect(connection)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(connection)


async def broadcast_event(event: dict):
    """Broadcast an event to subscribed clients"""
    await manager.broadcast(event, topic='events')
    

async def broadcast_alarm(alarm: dict, action: str):
    """Broadcast alarm update to subscribed clients"""
    await manager.broadcast({
        'action': action,
        **alarm
    }, topic='alarms')
    

async def broadcast_stream_status(camera_id: str, status: dict):
    """Broadcast stream status update"""
    await manager.broadcast({
        'camera_id': camera_id,
        **status
    }, topic='streams')


async def broadcast_drone_detection(detection_event: dict):
    """
    Broadcast drone detection to subscribed clients
    Supports filtering by drone ID and geofence violations
    """
    await manager.broadcast(detection_event, topic='drone_detection')

