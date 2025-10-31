# Frame Routing Contract

## Overview

This document defines how video frames flow from cameras through the stream manager to workflows, and how different components subscribe to and process frames.

## Architecture

```
Camera (RTSP) → StreamManager → FrameBuffer → WorkflowEngine → Individual Workflows
                                      ↓
                                 Ring Buffer (configurable size)
```

## Components

### StreamManager (`backend/stream/manager.py`)

**Responsibilities:**
- Manage RTSP connections for all cameras
- Maintain per-camera frame buffers
- Route frames to subscribed workflows
- Handle stream health and reconnection

**Key Methods:**
```python
async def start_stream(camera_id: str, rtsp_url: str, workflows: List[str])
async def stop_stream(camera_id: str)
async def get_latest_frame(camera_id: str) -> Optional[np.ndarray]
```

**Frame Distribution:**
- Each camera maintains a `FrameBuffer` (ring buffer, default 300 frames ~30s at 10fps)
- Frames are distributed to workflows via `WorkflowEngine.process_frame()`
- Distribution is **broadcast** - all workflows assigned to a camera receive all frames

### FrameBuffer (`backend/stream/frame_buffer.py`)

**Bounded Ring Buffer:**
- Fixed size (default: 300 frames)
- Oldest frames dropped when full
- Thread-safe for concurrent reads
- Supports pre-event buffering for recordings

**Configuration:**
```python
buffer_size = settings.FRAME_BUFFER_SIZE  # Default: 300
```

### WorkflowEngine (`backend/workflows/engine.py`)

**Responsibilities:**
- Load workflow definitions from config
- Route frames to appropriate workflows
- Manage workflow lifecycle

**Routing Logic:**
```python
# StreamManager calls:
await workflow_engine.process_frame(
    camera_id=camera_id,
    frame=frame,
    timestamp=datetime.utcnow()
)

# WorkflowEngine distributes to workflows:
for workflow_id, workflow in self.workflows.items():
    if camera_id in workflow.camera_subscriptions:
        await workflow.process_frame(camera_id, frame, timestamp)
```

### Individual Workflows (`backend/workflows/workflow.py`)

**Per-Workflow Frame Processing:**
- Each workflow has independent FPS throttling
- Configurable via `processing.fps` in workflow config
- Frame skipping based on time delta

**Throttling Example:**
```python
target_fps = 10  # Process 10 fps max
# Will skip frames to maintain this rate per camera
```

## Subscription Model

### Static Subscriptions (Current)

Workflows subscribe to cameras via configuration:

```yaml
# config/workflows.yaml
workflows:
  - id: people_detection
    cameras:
      - camera_1
      - camera_2
    processing:
      fps: 10
```

**Implementation:**
```python
# In StreamManager.start_stream():
for workflow_id in workflows:
    # WorkflowEngine.process_frame() called for each frame
    pass
```

### Dynamic Subscriptions (Proposed)

For better decoupling and testing:

```python
# Proposed API
workflow_engine.subscribe(
    camera_id='camera_1',
    workflow_id='people_detection',
    fps_limit=10,
    drop_policy='skip'  # or 'queue'
)
```

## Frame Queue Policies

### Current Behavior: Direct Processing
- Frames processed synchronously in RTSP capture loop
- No per-workflow queues
- **Risk:** Slow workflows block frame capture

### Proposed: Per-Workflow Queues

```python
# Bounded queue per (camera, workflow) pair
max_queue_depth = 10  # configurable

if queue.full():
    if drop_policy == 'skip':
        drop_oldest_frame()
    elif drop_policy == 'drop_new':
        skip_this_frame()
```

**Metrics to Expose:**
- `frames_received{camera, workflow}` - Total frames offered
- `frames_processed{camera, workflow}` - Successfully processed
- `frames_dropped{camera, workflow}` - Dropped due to backpressure
- `queue_depth{camera, workflow}` - Current queue size

## Camera-to-Workflow Mapping

### Loading from Config

```python
# In WorkflowEngine.load_workflows():
for workflow_config in yaml_config['workflows']:
    workflow_id = workflow_config['id']
    camera_ids = workflow_config.get('cameras', [])
    
    workflow = Workflow(workflow_id, workflow_config, event_manager)
    await workflow.initialize()
    
    # Store subscription mapping
    for camera_id in camera_ids:
        self.subscriptions[camera_id].append(workflow_id)
```

### Runtime Updates

**Not Currently Supported** - requires restart

**Proposed:**
```python
POST /api/workflows/{workflow_id}/cameras
{
  "camera_id": "camera_3",
  "action": "add"  # or "remove"
}
```

## Performance Considerations

### Bottlenecks

1. **RTSP Decoding** - CPU-intensive
   - Mitigation: Use hardware decode where available
   - Future: Offload to dedicated decode service

2. **Model Inference** - GPU/CPU-intensive
   - Mitigation: Batch processing, model quantization
   - Current: FPS throttling per workflow

3. **Frame Distribution** - Memory bandwidth
   - Current: Frames shared via numpy array (zero-copy)
   - Risk: Workflows modifying shared frame

### Frame Copy Strategy

**Current:** Frames are **shared references**
```python
# Same numpy array passed to all workflows
await workflow.process_frame(camera_id, frame, timestamp)
```

**Risk:** Workflow modifies frame (e.g., drawing boxes)

**Mitigation Options:**
1. Document "read-only" contract (current)
2. Deep copy per workflow (memory cost)
3. Copy-on-write wrapper

## Testing Contract

### Mocking Streams

```python
# Test helper
async def inject_test_frame(camera_id: str, frame: np.ndarray):
    await workflow_engine.process_frame(camera_id, frame, datetime.utcnow())
```

### Frame Generators

```python
# For load testing
from backend.test.frame_generator import generate_test_frames

async for frame in generate_test_frames(fps=30, duration=60):
    await workflow_engine.process_frame('test_camera', frame, datetime.utcnow())
```

## Event Emission

Workflows emit events to `EventManager`:

```python
# In Workflow._action_event():
event = {
    'id': uuid.uuid4(),
    'camera_id': camera_id,
    'workflow_id': self.workflow_id,
    'timestamp': timestamp,
    'detections': detections
}

await self.event_manager.create_event(event)
```

**Event Manager** then:
1. Stores event in database
2. Broadcasts via WebSocket
3. Triggers alarm correlation (via subscriptions)
4. Triggers rules evaluation

## Configuration Reference

### StreamManager Settings

```python
# backend/core/config.py
RTSP_TIMEOUT = 30  # seconds
FRAME_BUFFER_SIZE = 300  # frames
RECONNECT_DELAY = 5  # seconds
```

### Workflow Settings

```yaml
# config/workflows.yaml
workflows:
  - id: my_workflow
    processing:
      fps: 10           # Max frames per second to process
      skip_similar: false  # Future: Skip similar consecutive frames
```

## Migration Path

### Phase 1: Document Current Behavior ✅
- This document

### Phase 2: Add Metrics
- Frame counters per workflow
- Queue depths
- Drop rates

### Phase 3: Implement Queues
- Bounded per-workflow queues
- Configurable drop policies
- Backpressure handling

### Phase 4: Dynamic Subscriptions
- Runtime camera assignment
- Hot-reload workflow config
- A/B testing workflows on same stream

## Related Documentation

- `docs/WORKFLOWS.md` - Workflow configuration guide
- `docs/ARCHITECTURE.md` - System architecture
- `docs/PERFORMANCE.md` - Performance tuning

---

**Last Updated:** 2025-10-30  
**Status:** Current behavior documented; queuing and metrics are proposed enhancements


