# API Reference

## Base URL
```
http://localhost:8000/api
```

## WebSocket
```
ws://localhost:8000/ws
```

## Authentication

All API requests require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Cameras

#### List Cameras
```http
GET /api/cameras
```

Response:
```json
{
  "cameras": [
    {
      "id": "cam-001",
      "name": "Front Entrance",
      "rtsp_url": "rtsp://...",
      "status": "online",
      "workflows": ["people_detection"],
      "fps": 25,
      "resolution": "1920x1080"
    }
  ]
}
```

#### Get Camera
```http
GET /api/cameras/{camera_id}
```

#### Add Camera
```http
POST /api/cameras
Content-Type: application/json

{
  "name": "New Camera",
  "rtsp_url": "rtsp://username:password@ip:port/stream",
  "workflows": ["people_detection"]
}
```

#### Update Camera
```http
PUT /api/cameras/{camera_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "workflows": ["people_detection", "weapon_detection"]
}
```

#### Delete Camera
```http
DELETE /api/cameras/{camera_id}
```

### Streams

#### Get Stream Status
```http
GET /api/streams/{camera_id}/status
```

Response:
```json
{
  "camera_id": "cam-001",
  "status": "streaming",
  "fps": 24.5,
  "bitrate": "2.5 Mbps",
  "uptime": 3600,
  "last_frame": "2025-10-30T10:30:00Z"
}
```

#### Start Stream
```http
POST /api/streams/{camera_id}/start
```

#### Stop Stream
```http
POST /api/streams/{camera_id}/stop
```

#### Get Stream URL
```http
GET /api/streams/{camera_id}/url
```

Response:
```json
{
  "rtsp_url": "rtsp://localhost:8554/cam-001",
  "webrtc_url": "ws://localhost:8000/webrtc/cam-001"
}
```

### Workflows

#### List Workflows
```http
GET /api/workflows
```

Response:
```json
{
  "workflows": [
    {
      "id": "people_detection",
      "name": "People Detection",
      "model": "ultralytics-yolov8n",
      "active_cameras": 3,
      "total_detections": 150
    }
  ]
}
```

#### Get Workflow
```http
GET /api/workflows/{workflow_id}
```

#### Create Workflow
```http
POST /api/workflows
Content-Type: application/json

{
  "id": "custom_workflow",
  "name": "Custom Detection",
  "model": "ultralytics-yolov8s",
  "classes": [0, 1],
  "confidence": 0.7,
  "actions": [
    {
      "type": "event",
      "severity": "info"
    }
  ]
}
```

#### Update Workflow
```http
PUT /api/workflows/{workflow_id}
```

#### Delete Workflow
```http
DELETE /api/workflows/{workflow_id}
```

### Events

#### List Events
```http
GET /api/events?camera_id=cam-001&workflow_id=people_detection&limit=100&offset=0
```

Query Parameters:
- `camera_id` (optional): Filter by camera
- `workflow_id` (optional): Filter by workflow
- `severity` (optional): Filter by severity (info, warning, critical)
- `start_time` (optional): ISO timestamp
- `end_time` (optional): ISO timestamp
- `limit` (optional): Number of results (default: 100)
- `offset` (optional): Pagination offset

Response:
```json
{
  "events": [
    {
      "id": "evt-001",
      "camera_id": "cam-001",
      "workflow_id": "people_detection",
      "timestamp": "2025-10-30T10:30:00Z",
      "severity": "info",
      "detections": [
        {
          "class": "person",
          "confidence": 0.92,
          "bbox": [100, 150, 300, 500],
          "zone": "entrance"
        }
      ],
      "snapshot_url": "/api/events/evt-001/snapshot"
    }
  ],
  "total": 1500,
  "limit": 100,
  "offset": 0
}
```

#### Get Event
```http
GET /api/events/{event_id}
```

#### Get Event Snapshot
```http
GET /api/events/{event_id}/snapshot
```

Returns: JPEG image

### Models

#### List Available Models
```http
GET /api/models
```

Response:
```json
{
  "models": [
    {
      "id": "ultralytics-yolov8n",
      "name": "YOLOv8 Nano",
      "type": "object_detection",
      "classes": ["person", "car", "truck", ...],
      "performance": "fast",
      "accuracy": "medium"
    }
  ]
}
```

#### Get Model Info
```http
GET /api/models/{model_id}
```

### System

#### Get System Status
```http
GET /api/system/status
```

Response:
```json
{
  "status": "healthy",
  "uptime": 86400,
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "gpu_usage": 78.5,
  "active_streams": 8,
  "active_workflows": 12,
  "total_events": 5420
}
```

#### Get System Metrics
```http
GET /api/system/metrics
```

## WebSocket API

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Subscribe to Events
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['events', 'stream_status']
}));
```

### Event Messages

#### Detection Event
```json
{
  "type": "detection",
  "camera_id": "cam-001",
  "workflow_id": "people_detection",
  "timestamp": "2025-10-30T10:30:00Z",
  "detections": [...]
}
```

#### Stream Status Update
```json
{
  "type": "stream_status",
  "camera_id": "cam-001",
  "status": "online",
  "fps": 24.5
}
```

#### System Alert
```json
{
  "type": "alert",
  "severity": "warning",
  "message": "High CPU usage detected",
  "timestamp": "2025-10-30T10:30:00Z"
}
```

## Error Responses

All errors follow this format:
```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {}
}
```

### Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid token
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `500 Internal Server Error`: Server error

