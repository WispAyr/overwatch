# Overwatch Workflow Builder

Visual workflow editor for creating AI detection pipelines using [React Flow](https://reactflow.dev/).

## Features

### 🎨 Node-RED Style Interface
- Drag and drop components
- Visual connections between nodes
- Real-time configuration
- Dark mode design

### 📦 Available Components

#### 📹 Camera Inputs
- Drag any configured camera onto canvas
- Shows live status (Online/Offline)
- Displays FPS
- Multiple quality options

#### 🤖 AI Models
- YOLOv8 (Nano, Small, Medium, Large)
- Custom models
- Configure inline:
  - Confidence threshold (slider)
  - Detection classes (text input)
  - Model parameters

#### 📐 Zones & Filters
- **Detection Zone**: Define polygon areas
- **Confidence Filter**: Minimum threshold
- **Class Filter**: Specific object types
- **Time Filter**: Active hours

#### ⚡ Actions / Outputs
- **🚨 Alarm Centre**: Send to monitoring
- **📧 Email Alert**: Send notifications
- **🔗 Webhook**: HTTP POST
- **🎥 Record Video**: Save clip (10-300s)
- **📸 Snapshot**: Capture still image

## Workflow Examples

### Example 1: Simple People Detection
```
📹 NOC Camera → 🤖 YOLOv8n → 📧 Email Alert
```

### Example 2: Zoned Detection with Recording
```
📹 Entrance Camera → 🤖 YOLOv8m → 📐 Zone Filter → 🎥 Record (30s)
                                                    → 🚨 Alarm Centre
```

### Example 3: Multi-Model Pipeline
```
📹 Parking Camera → 🤖 YOLOv8 (vehicles) → 📐 No-Parking Zone → 📧 Email
                                                               → 📸 Snapshot
```

### Example 4: Weapon Detection with Multiple Actions
```
📹 Main Entrance → 🤖 Weapon Detector → 🎯 High Confidence (95%) → 🚨 Alarm
                                                                   → 📧 Email
                                                                   → 🎥 Record (60s)
                                                                   → 📸 Snapshot
```

## Quick Start

### 1. Install Dependencies
```bash
cd workflow-builder
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

Opens at: **http://localhost:7003**

### 3. Build for Production
```bash
npm run build
```

Output: `frontend/workflow-builder/`

## Usage

### Creating a Workflow

1. **Add Camera**
   - Drag camera from sidebar
   - Camera shows current status

2. **Add AI Model**
   - Drag AI model (e.g., YOLOv8n)
   - Click ⚙️ to configure:
     - Confidence threshold
     - Classes to detect

3. **Connect Camera → Model**
   - Drag from camera's right handle
   - Drop on model's left handle

4. **Add Filters** (Optional)
   - Drag detection zone
   - Click ⚙️ to define polygon
   - Connect model → zone

5. **Add Actions**
   - Drag action (email, alarm, etc.)
   - Click ⚙️ to configure
   - Connect zone/model → action

6. **Save Workflow**
   - Click "💾 Save Workflow"
   - Downloads JSON file
   - Can reload later

### Configuring Nodes

Each node has a ⚙️ button:
- **Camera**: View stream info
- **Model**: Set confidence, classes
- **Zone**: Define polygon, filters
- **Action**: Set destinations, durations

### Example Configuration

**Detection Zone Polygon**:
```json
[[100, 100], [500, 100], [500, 400], [100, 400]]
```

**Model Classes**:
```
person, car, truck
```

**Webhook URL**:
```
https://your-server.com/api/alerts
```

## Keyboard Shortcuts

- **Delete**: Remove selected nodes/edges
- **Ctrl/Cmd + Z**: Undo (coming soon)
- **Ctrl/Cmd + S**: Save workflow
- **Escape**: Deselect

## Integration with Overwatch

The workflow builder generates configuration that maps to Overwatch's YAML workflows:

### Visual Workflow:
```
Camera → Model → Zone → Action
```

### Generated YAML:
```yaml
workflow:
  camera_id: noc-outdoor-cam-01
  model: ultralytics-yolov8n
  detection:
    confidence: 0.7
    classes: [0]  # person
  zones:
    - polygon: [[100,100], [500,400]]
  actions:
    - type: email
      to: security@company.com
```

## Future Enhancements

- [ ] Load/save workflows to backend
- [ ] Real-time preview of detections on canvas
- [ ] Template workflows
- [ ] Workflow validation
- [ ] Copy/paste workflows
- [ ] Multi-select and group
- [ ] Undo/redo
- [ ] Auto-layout
- [ ] Workflow testing mode
- [ ] Export to production config

## Tech Stack

- **React 18** - UI framework
- **React Flow 12** - Node-based editor ([reactflow.dev](https://reactflow.dev/))
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Overwatch API** - Backend integration

## Port

**Development**: http://localhost:7003  
**Production**: Integrated into main dashboard

## Links

- React Flow Docs: https://reactflow.dev/
- Examples: https://reactflow.dev/examples
- API Reference: https://reactflow.dev/api-reference


