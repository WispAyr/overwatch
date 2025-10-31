# Overwatch Architecture

## Overview

Overwatch follows a microservices-inspired architecture with clear separation between stream ingestion, AI processing, and presentation layers.

## System Components

### 1. Stream Manager
**Purpose**: Handle RTSP stream ingestion and management

**Responsibilities**:
- Connect to RTSP camera feeds
- Maintain persistent connections with auto-reconnect
- Frame extraction and buffering
- Stream health monitoring

**Technology**: 
- FFmpeg for RTSP decoding
- OpenCV for frame processing
- asyncio for concurrent stream handling

### 2. Workflow Engine
**Purpose**: Route video frames through AI processing pipelines

**Responsibilities**:
- Load and manage workflow configurations
- Coordinate model execution
- Handle frame batching and queuing
- Manage processing priorities

**Design Pattern**: Plugin architecture for model integration

### 3. Model Plugins
**Purpose**: Provide AI/ML inference capabilities

**Supported Models**:
- Ultralytics YOLOv8 (object detection)
- Custom PyTorch models
- TensorFlow models
- OpenCV classical vision algorithms

**Interface**:
```python
class ModelPlugin:
    def initialize(self, config: dict) -> None
    def process_frame(self, frame: np.ndarray) -> DetectionResult
    def cleanup(self) -> None
```

### 4. Event System
**Purpose**: Handle detection events and alerts

**Responsibilities**:
- Collect detection results
- Filter and aggregate events
- Trigger alerts (webhook, email, etc.)
- Store event history

**Storage**: SQLite for events, with optional PostgreSQL support

### 5. API Server
**Purpose**: Provide RESTful API for frontend

**Endpoints**:
- `/api/cameras` - Camera management
- `/api/streams` - Stream status and control
- `/api/workflows` - Workflow configuration
- `/api/events` - Detection events
- `/api/models` - Available AI models

**Technology**: FastAPI with WebSocket support for real-time updates

### 6. Frontend Dashboard
**Purpose**: Provide user interface for monitoring and configuration

**Components**:
- Video Grid: Multi-camera live view using Mediabunny
- Event Timeline: Real-time detection events
- Workflow Builder: Visual workflow configuration
- Analytics Dashboard: Detection statistics

**Technology**: 
- Pure HTML/CSS/JavaScript
- Mediabunny for video playback
- Tailwind CSS for styling
- Chart.js for analytics

## Data Flow

```
RTSP Cameras
    ↓
Stream Manager (frame extraction)
    ↓
Workflow Engine (routing)
    ↓
Model Plugins (AI inference)
    ↓
Event System (detection processing)
    ↓
API Server (WebSocket)
    ↓
Frontend Dashboard (visualization)
```

## Scalability Considerations

### Federation Architecture
- **Central + Edge**: Distributed processing with centralized aggregation
- **Edge nodes** process video locally, forward events only
- **Central server** aggregates events, provides unified dashboard
- **95% bandwidth reduction** vs streaming video to central

### Edge Processing
- Run Overwatch on edge devices near cameras
- Reduce bandwidth usage (forward events, not video)
- Lower latency (<200ms local processing)
- Autonomous operation if WAN fails

### Cloud Processing
- Offload heavy models to cloud GPUs
- Centralized event storage
- Multi-site deployments
- Horizontal scaling with load balancer

### Hybrid Approach
- Light models on edge (person detection - YOLOv8n)
- Heavy models on cloud (weapon detection, complex analysis - YOLOv8l)
- Smart routing based on detection triggers
- Cost optimization

## Security

- API authentication with JWT tokens
- HTTPS/WSS for all communications
- Camera credentials encrypted in config
- Role-based access control

## Performance Targets

- Stream Latency: < 500ms from camera to display
- Detection Latency: < 200ms per frame
- Concurrent Streams: 16+ cameras on standard hardware
- Frame Rate: 15-30 FPS per camera

