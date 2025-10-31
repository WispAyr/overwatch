# Visual Workflow Builder Guide

## Overview

The Overwatch Workflow Builder is a Node-RED style visual editor built with [React Flow](https://reactflow.dev/) that lets you create complex AI detection workflows by dragging and connecting components.

## Access

**URL**: http://localhost:7003  
**Start**: `./scripts/start_workflow_builder.sh`

## Features

### ✅ **Auto-Discovery**

Everything updates automatically:
- **Cameras**: Loaded from database (refreshes on page load)
- **AI Models**: Auto-detected from `MODEL_REGISTRY`
- **Actions**: All available action types
- **Filters**: Detection zones, confidence filters, etc.

### ✅ **Live Integration**

- Camera status shows live (Online/Offline, FPS)
- Models show speed/accuracy ratings
- Changes in backend appear immediately
- No manual configuration needed

## Components

### 📹 Camera Nodes (Blue)

**Draggable from sidebar**:
- Shows camera name
- Live status (🟢 Online / 🔴 Offline)
- Current FPS
- Active quality (LOW/MED/HIGH)
- Resolution

**Outputs**: Video frames → Connect to AI Models

### 🤖 AI Model Nodes (Green)

**Available Models** (auto-discovered):
- YOLOv8 Nano (fast)
- YOLOv8 Small (medium speed)
- YOLOv8 Medium (slower, more accurate)
- YOLOv8 Large (slow, very accurate)
- YOLOv8 X-Large (slowest, best accuracy)

**Configuration** (click ⚙️):
- Confidence threshold (slider: 0-100%)
- Detection classes (person, car, truck, etc.)

**Inputs**: Video from cameras  
**Outputs**: Detections → Connect to Zones or Actions

### 📐 Zone/Filter Nodes (Yellow)

**Types**:
1. **Detection Zone** - Polygon area
   - Define coordinates
   - Only detect objects in this area
   - Example: `[[100,100],[500,100],[500,400],[100,400]]`

2. **Confidence Filter**
   - Minimum confidence (e.g., 85%)
   - Remove low-confidence detections

3. **Class Filter**
   - Specific object types
   - Example: Only "person", not "car"

4. **Temporal Filter**
   - Dwell time (must be present for N seconds)
   - Cooldown (wait between alerts)

**Inputs**: Detections from models  
**Outputs**: Filtered detections → Connect to Actions

### ⚡ Action Nodes (Purple/Red/Orange)

**Available Actions** (auto-discovered):

1. **📝 Log Event** (Blue)
   - Store in event database
   - Set severity (info/warning/critical)

2. **🚨 Alert** (Red)
   - High-priority notification
   - Notify security team
   - Critical severity

3. **📧 Email Alert** (Purple)
   - Send email notification
   - Configure recipient
   - Include snapshot

4. **🔗 Webhook** (Purple)
   - HTTP POST to external service
   - Custom URL
   - JSON payload with detection data

5. **🎥 Record Video** (Orange)
   - Save video clip
   - Duration: 10-300 seconds
   - Pre-buffer: 0-30 seconds

6. **📸 Save Snapshot** (Pink)
   - Capture still image
   - Draw bounding boxes
   - Save with detection data

**Inputs**: Detections (from models or zones)

## Example Workflows

### Example 1: Simple People Detection with Email
```
📹 NOC Camera → 🤖 YOLOv8 Nano → 📧 Email Alert
                  (confidence: 70%)   (to: security@company.com)
```

**What it does**:
- Processes camera feed with YOLOv8
- Detects people with 70%+ confidence
- Sends email on each detection

### Example 2: Zoned Detection with Multiple Actions
```
📹 Entrance Cam → 🤖 YOLOv8 Medium → 📐 Entrance Zone → 🚨 Alarm
                    (person only)      (polygon area)    → 📧 Email
                                                         → 🎥 Record (30s)
                                                         → 📸 Snapshot
```

**What it does**:
- Detects people in entrance zone only
- Triggers alarm
- Sends email
- Records 30-second clip
- Captures snapshot

### Example 3: Parking Violation Detection
```
📹 Parking Cam → 🤖 YOLOv8 Small → 📐 No-Parking Zone → 🎯 High Confidence → 📧 Email
                  (car, truck)       (yellow line area)    (85%+)           → 📸 Snapshot
```

**What it does**:
- Detects vehicles in no-parking zone
- Only high-confidence (85%+) detections
- Emails parking enforcement
- Captures evidence photo

### Example 4: Weapon Detection with Critical Response
```
📹 Main Entrance → 🤖 Weapon Detector → 🎯 Very High (95%) → 🚨 Alarm (Critical)
                                                             → 📧 Email (Security)
                                                             → 🎥 Record (60s)
                                                             → 🔗 Webhook (Police API)
```

**What it does**:
- Scans for weapons
- Only 95%+ confidence
- Triggers critical alarm
- Emails security team
- Records 60 seconds
- Notifies police via webhook

## Building a Workflow

### Step-by-Step

1. **Add Camera**
   - Drag "NOC Outdoor Camera 1" from sidebar
   - Drop onto canvas
   - Shows live status

2. **Add AI Model**
   - Drag "YOLOv8 Nano" (or any model)
   - Drop onto canvas
   - Click ⚙️ to configure:
     - Confidence: 70% (adjust slider)
     - Classes: "person" (or "person, car")

3. **Connect Camera → Model**
   - Click and drag from camera's **right handle**
   - Drop on model's **left handle**
   - Edge appears showing connection

4. **(Optional) Add Zone**
   - Drag "Detection Zone"
   - Click ⚙️ to configure polygon:
     ```json
     [[100,100],[500,100],[500,400],[100,400]]
     ```
   - Connect: Model → Zone

5. **Add Actions**
   - Drag "Email Alert"
   - Click ⚙️ to configure:
     - Email: `security@company.com`
   - Connect: Model (or Zone) → Email

6. **Add More Actions** (optional)
   - Drag "Save Snapshot"
   - Connect: Same source → Snapshot
   - One detection can trigger multiple actions!

7. **Save Workflow**
   - Click "💾 Save Workflow"
   - Downloads JSON file
   - Can reload later

## Deploying Workflows

### Method 1: Save and Apply Manually

1. Click "💾 Save Workflow"
2. Downloads `workflow-xxx.json`
3. Use API to deploy:
   ```bash
   curl -X POST http://localhost:8000/api/workflow-builder/ \
     -H "Content-Type: application/json" \
     -d @workflow-xxx.json
   ```

### Method 2: Deploy from Builder (Coming Soon)

1. Build workflow visually
2. Click "🚀 Deploy"
3. Converts to YAML automatically
4. Activates immediately

## Auto-Discovery System

### When You Add a New Model

**Backend** (`backend/models/custom_model.py`):
```python
class MyCustomModel(BaseModel):
    # Your model implementation
    pass

# Register it
MODEL_REGISTRY['my-custom-model'] = MyCustomModel
```

**Result**:
- Appears in workflow builder sidebar
- Can be dragged onto canvas
- Fully integrated

### When You Add a New Camera

**Config** (`config/hierarchy.yaml`):
```yaml
cameras:
  - id: new-camera-01
    name: "New Camera"
    rtsp_url: "rtsp://..."
```

**Result**:
- Refresh workflow builder
- New camera appears in sidebar
- Shows live status
- Ready to use

### When You Add a New Action

**Backend** (`backend/api/routes/workflow_components.py`):
```python
{
    "id": "sms_alert",
    "name": "SMS Alert",
    "icon": "📱",
    "description": "Send SMS notification",
    "color": "green",
    "config": {
        "phone": {"type": "tel", "placeholder": "+1234567890"}
    }
}
```

**Result**:
- Appears in Actions section
- Draggable onto canvas
- Configurable

## Generated Configuration

The visual workflow generates executable YAML:

### Visual Workflow:
```
📹 Camera → 🤖 YOLOv8n → 📐 Zone → 📧 Email
```

### Generated YAML:
```yaml
workflows:
  - camera_id: noc-outdoor-cam-01
    enabled: true
    model: ultralytics-yolov8n
    detection:
      confidence: 0.7
      classes: [0]  # person
    zones:
      - name: zone
        polygon: [[100,100],[500,100],[500,400],[100,400]]
    actions:
      - type: email
        to: security@company.com
        include_snapshot: true
```

## API Endpoints

### Get Available Components
```bash
# Models
GET /api/workflow-components/models

# Actions
GET /api/workflow-components/actions

# Filters
GET /api/workflow-components/filters

# Object Classes
GET /api/workflow-components/classes
```

### Save Workflow
```bash
POST /api/workflow-builder/
Body: {workflow JSON}
```

### Load Workflow
```bash
GET /api/workflow-builder/{workflow_id}
```

### Deploy Workflow
```bash
POST /api/workflow-builder/{workflow_id}/deploy
```

### Preview YAML
```bash
POST /api/workflow-builder/{workflow_id}/preview
```

## Keyboard Shortcuts

- **Delete**: Remove selected node/edge
- **Ctrl/Cmd + C**: Copy (coming soon)
- **Ctrl/Cmd + V**: Paste (coming soon)
- **Ctrl/Cmd + Z**: Undo (coming soon)
- **Ctrl/Cmd + S**: Save workflow

## Tips & Best Practices

1. **Start Simple**
   - Begin with Camera → Model → Action
   - Add complexity gradually

2. **Use Zones**
   - Reduce false positives
   - Focus on areas of interest
   - Improve performance

3. **Multiple Actions**
   - One detection can trigger many actions
   - Connect model to multiple action nodes
   - Example: Email + Record + Snapshot

4. **Test Before Deploy**
   - Use "Preview" to see generated YAML
   - Verify configuration is correct
   - Test with one camera first

5. **Name Things Well**
   - Workflows saved with descriptive names
   - Easy to find and reload
   - Document purpose

## Adding Custom Components

### Custom AI Model
```python
# backend/models/my_model.py
from .base import BaseModel

class MyModel(BaseModel):
    async def detect(self, frame):
        # Your detection logic
        return detections

# backend/models/__init__.py
MODEL_REGISTRY['my-custom-model'] = MyModel
```

Restart backend → appears in workflow builder!

### Custom Action
```python
# backend/api/routes/workflow_components.py
{
    "id": "custom_action",
    "name": "My Custom Action",
    "icon": "⚡",
    "description": "Does something custom",
    "color": "cyan",
    "config": {
        "param1": {"type": "text"}
    }
}
```

Restart backend → appears in actions!

## Implementation Status & Roadmap

### ✅ **Completed Features (v1.0)**

#### Core Architecture
- [x] **Schema-based validation** - JSON Schema for all node types with strict contracts
- [x] **Graph validation** - Port compatibility, cycle detection, and referential integrity checks
- [x] **Workflow versioning** - Schema version tracking and migration support
- [x] **YAML diffing** - Preview changes before deployment with detailed diff
- [x] **Sensitive data redaction** - Automatic scrubbing of sensitive values in logs
- [x] **Event bus** - Centralized pub/sub system for node lifecycle and error handling

#### Visual Editor
- [x] **Drag-and-drop interface** - React Flow based visual editor
- [x] **Auto-discovery** - Dynamic loading of cameras, models, actions, and filters
- [x] **Node-RED inspired design** - Familiar workflow patterns
- [x] **Real-time preview** - Execute workflows without saving
- [x] **Environment configuration** - Config-driven API URLs and settings

#### Advanced Node Types
- [x] **Link Nodes** - LinkIn/LinkOut/LinkCall for cross-tab routing and reusable subgraphs
- [x] **Catch Nodes** - Error handling with routing to error handlers
- [x] **Template/Subflow System** - Reusable workflow components with parameters
- [x] **Polygon validation** - Strict zone coordinate validation

#### Stream Integration
- [x] **Stream Manager integration** - Frame retrieval from live RTSP streams
- [x] **Frame throttling** - FPS-based throttling per input node
- [x] **Metrics tracking** - Per-node performance metrics (fps, latency, queue)
- [x] **Event broadcasting** - Real-time status updates via WebSocket

#### Action System
- [x] **Schema-enforced actions** - Validated config for email, webhook, record, alert, snapshot
- [x] **Snapshot action** - Full implementation with SnapshotHandler integration
- [x] **Recording action** - Pre/post buffer support with stream buffer integration
- [x] **Secrets management** - Secret store references for webhooks/APIs

#### Testing & Documentation
- [x] **Unit tests** - Comprehensive tests for visual_executor and validator
- [x] **Integration tests** - Workflow parsing and validation test coverage
- [x] **API documentation** - Complete endpoint documentation
- [x] **Node-RED patterns** - Documented adoption strategy

### 🚧 **In Progress**

- [ ] **Authentication/Authorization** - JWT-based auth for workflow APIs with role checks
- [ ] **Component auto-discovery** - Full registry-based discovery from MODEL_REGISTRY
- [ ] **WebSocket status updates** - Remove simulated UI counters, use live metrics
- [ ] **Keyboard shortcuts** - Delete, copy/paste, undo/redo
- [ ] **Context menus** - Right-click actions on nodes and canvas

### 📋 **Roadmap (v1.1)**

#### Editor Enhancements
- [ ] **Visual error indicators** - Red outlines on invalid nodes/edges
- [ ] **Batch operations** - Multi-select and batch edit
- [ ] **Auto-layout** - Automatic node arrangement
- [ ] **Grid snapping** - Align nodes to grid
- [ ] **Connection hints** - Visual guides for valid connections
- [ ] **Search/filter** - Find nodes in large workflows

#### Workflow Management
- [ ] **Git integration** - Automatic versioning with commit on save/deploy
- [ ] **A/B testing** - Run multiple workflow versions simultaneously
- [ ] **Rollback** - Revert to previous workflow versions
- [ ] **Workflow templates library** - Pre-built common patterns
- [ ] **Import/export** - Share workflows across systems
- [ ] **Workflow scheduling** - Time-based activation

#### Debugging & Monitoring
- [ ] **Visual debugger** - Step-through execution with breakpoints
- [ ] **Performance profiling** - Per-node timing and bottleneck detection
- [ ] **Live data preview** - See actual frame/detection data in UI
- [ ] **Log viewer** - Integrated log streaming in builder
- [ ] **Metrics dashboard** - Real-time workflow performance metrics
- [ ] **Alerting** - Workflow failure notifications

#### Advanced Features
- [ ] **Batch processing** - N-frame batching for model inference
- [ ] **Multi-stream coordination** - Synchronize across cameras
- [ ] **State machines** - Complex temporal logic
- [ ] **ML model training** - Feedback loop for model improvement
- [ ] **Cloud deployment** - Export workflows to cloud platforms
- [ ] **Mobile app builder** - Generate mobile monitoring apps from workflows

### 🏗️ **Architecture Improvements**

#### Scalability
- [ ] **Distributed execution** - Multi-worker workflow execution
- [ ] **Queue-based processing** - Celery/Redis task queues
- [ ] **Horizontal scaling** - Load balancing across executors
- [ ] **Resource management** - CPU/GPU allocation per workflow

#### Security
- [ ] **RBAC** - Role-based access control for workflows
- [ ] **Audit logging** - Track all workflow changes
- [ ] **Encrypted secrets** - Vault integration for sensitive data
- [ ] **API rate limiting** - Prevent abuse of workflow execution

#### Data Management
- [ ] **Workflow analytics** - Detection statistics and trends
- [ ] **Data retention** - Automatic cleanup of old snapshots/recordings
- [ ] **Database optimization** - Indexing and query performance
- [ ] **Backup/restore** - Automated workflow backup

## Conclusion

The Workflow Builder provides a **production-ready, Node-RED style interface** for creating AI detection workflows with:
- **Strict validation** at every layer (UI, API, executor)
- **Live integration** with stream manager and event systems
- **Extensible architecture** supporting templates, link nodes, and error handling
- **Comprehensive testing** ensuring reliability

Everything auto-syncs with the backend - add models, cameras, or actions and they appear automatically!

**Open http://localhost:7003 and start building!** 🚀

---

## Node-RED Pattern Adoption

The Workflow Builder adopts the following Node-RED patterns:

### 1. **Subflows (Templates)**
- **Implementation**: `/api/workflow-templates/` endpoints
- **Features**: Parameterized, reusable workflow components
- **UI**: Drag templates from sidebar, configure parameters on instantiation
- **Storage**: Database-backed with versioning

### 2. **Link Nodes (In/Out/Call)**
- **LinkIn**: Entry point for subgraphs, named links
- **LinkOut**: Exit point, routes to named link
- **LinkCall**: Invoke a subgraph and return results
- **Use Case**: Avoid long wires, organize complex flows across tabs

### 3. **Error Handling (Catch)**
- **Catch Node**: Intercepts errors from connected nodes
- **Scope**: Can watch all nodes or specific nodes
- **Integration**: Event bus routes errors to catch nodes
- **Actions**: Log, alert, or recover from errors

### 4. **Status Events**
- **Event Bus**: Centralized pub/sub for node lifecycle
- **Events**: `node_started`, `node_error`, `status_update`, `metrics_update`
- **WebSocket**: Broadcast to UI for live status display
- **UI Integration**: Color-coded node outlines based on status

### 5. **Persistent Context**
- **Storage**: Redis/file-based context store (planned)
- **Use Cases**: Temporal filters, cooldowns, state machines
- **API**: `context.get()`, `context.set()` in node execution
- **Scopes**: Per-node, per-flow, global

### 6. **Environment Variables**
- **Frontend**: `config.ts` with `import.meta.env`
- **Backend**: Schema references to env vars instead of literals
- **Secrets**: Secret store integration for sensitive values
- **Configuration**: Centralized defaults with overrides

---

*Last updated: October 2025*

