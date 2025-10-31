# Overwatch - AI-Powered Security Camera Monitoring System

Overwatch is a comprehensive security camera monitoring system that ingests RTSP camera feeds and processes them through AI/ML models to create intelligent workflows for various detection scenarios.

## Features

- **Visual Workflow Builder**: Node-RED style visual editor with React Flow (port 7003)
- **Multi-Modal AI**: 38+ AI models across vision and audio processing
- **Alarm Management**: State machine with SLA tracking, triage, and assignment
- **Rules Engine**: YAML DSL for automated responses and notifications
- **Federation Support**: Distributed architecture with central + edge nodes via ZeroTier
- **Organizational Hierarchy**: Multi-tenant structure supporting Organizations → Sites → Sublocations → Cameras
- **Mobile Site Support**: Deploy resources to temporary/mobile locations with full monitoring
- **Multi-Camera Support**: Ingest RTSP streams from various security camera systems (UniFi, ONVIF-compliant cameras)
- **AI-Powered Detection**: 
  - **Vision**: Object detection, pose estimation, segmentation, tracking
  - **Recognition**: Face identification, license plate reading (ALPR)
  - **Security**: Weapon detection, fire/smoke detection, PPE compliance
  - **Audio**: Speech transcription (99 languages), sound classification (521+ classes)
  - **Advanced**: Fall detection, activity recognition, threat assessment
  - Zone-based filtering and custom workflow creation
- **Real-Time Processing**: WebSocket-based live updates, frame buffering, and event streaming
- **Modern Dashboard**: Clean, professional dark mode interface (SpaceX-inspired aesthetic)
- **Admin Panel**: Full CRUD for organizations, sites, sublocations, and cameras
- **Notifications**: Email, SMS (Twilio), PagerDuty, Webhooks
- **Chrome Extension**: Direct browser access to debug console with real-time WebSocket feed (see `chrome-extension/`)

## Architecture

### Backend (Python/FastAPI - Port 8000)
- **Stream Manager**: RTSP feed ingestion with audio extraction
- **Workflow Engine**: Visual + YAML workflow execution
- **AI Model Registry**: 38+ models including:
  - YOLOv8 (detection, pose, segmentation, tracking)
  - Face Recognition (DeepFace), License Plates (EasyOCR)
  - Weapon Detection, Fire/Smoke Detection, PPE Compliance
  - Whisper (speech), YAMNet, PANNs (audio events)
- **Event System**: Canonical event schema with enrichment
- **Alarm Manager**: State machine with SLA tracking
- **Rules Engine**: YAML DSL with conditions and actions
- **API Server**: RESTful + WebSocket API
- **Federation Manager**: ZeroTier-based node peering

### Frontend (HTML/CSS/JavaScript - Port 7002)
- **Modern UI**: Clean, dark mode interface with Tailwind CSS
- **Live Dashboard**: Real-time system monitoring via WebSocket
- **Camera Grid**: Multi-camera MJPEG streams with quality control
- **Event Timeline**: Real-time detection events with snapshots
- **Alarm Board**: Kanban-style alarm triage and management
- **Federation Monitor**: Distributed node status
- **Organization Tree**: Hierarchical camera organization
- **Admin Panel**: Full entity management (CRUD)
- **Workflow Monitor**: Active workflows with metrics

### Workflow Builder (React/Vite - Port 7003)
- **Visual Editor**: Node-RED style with React Flow
- **Multi-Tab Editing**: Work on multiple workflows simultaneously
- **Auto-Save**: Never lose work (2s debounce + 30s periodic)
- **Config Nodes**: Reusable model/action configurations
- **Examples Library**: Pre-built workflow templates
- **Debug Console**: Real-time message inspection
- **Site Organization**: Site-specific + master templates

## Project Structure

```
overwatch/
├── backend/
│   ├── api/              # FastAPI server + WebSocket
│   ├── alarms/           # Alarm state machine + storage
│   ├── core/             # Core system (config, DB, hierarchy, metrics)
│   ├── events/           # Event manager + storage
│   ├── federation/       # Node peering + ZeroTier
│   ├── integrations/     # Notifications + device control
│   ├── models/           # AI model wrappers (YOLO, Whisper, YAMNet)
│   ├── rules/            # Rules engine + DSL parser
│   ├── stream/           # RTSP ingestion + audio extraction
│   └── workflows/        # Visual + YAML workflow engine
├── frontend/             # Dashboard (port 7002)
│   ├── components/       # Reusable HTML components
│   ├── css/              # Tailwind CSS
│   ├── js/               # JavaScript modules
│   ├── views/            # Admin panel
│   └── index.html        # Main dashboard
├── workflow-builder/     # Visual builder (port 7003)
│   └── src/
│       ├── components/   # React components
│       ├── nodes/        # Custom node types
│       └── edges/        # Custom edge types
├── config/               # YAML configuration files
├── data/                 # SQLite DB, snapshots, recordings
├── docs/                 # Comprehensive documentation
├── models/               # Downloaded AI models
└── tests/                # Test suite
```

## Quick Start

### Prerequisites
- Python 3.9+ (3.10+ recommended)
- FFmpeg (for RTSP streaming and audio extraction)
- Node.js 18+ (for Tailwind CSS and workflow builder)
- CUDA (optional, for GPU acceleration)

### Installation

**Option 1: Automated Install (Recommended)**
```bash
cd /Users/ewanrichardson/Development/overwatch
./install.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Build frontend CSS
- Download YOLOv8 model
- Create data directories

**Option 2: Manual Install**
```bash
# 1. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Install Node dependencies
npm install

# 3. Build frontend CSS
npm run build:css

# 4. Create directories
mkdir -p logs data/snapshots data/recordings models config

# 5. Download AI model (optional - auto-downloads on first run)
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Starting Overwatch

**Terminal 1: Backend API**
```bash
./run.sh
# Or manually:
# source venv/bin/activate && python backend/main.py
```

**Terminal 2: Dashboard (Optional - can use Chrome Extension instead)**
```bash
./scripts/start_dashboard.sh
# Or manually:
# python3 -m http.server 7002 --directory frontend
```

**Terminal 3 (Optional): Workflow Builder**
```bash
cd workflow-builder
npm install
npm run dev
# Opens on http://localhost:7003
```

### Access Points

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:7002
- **Workflow Builder**: http://localhost:7003
- **Chrome Extension**: Load `chrome-extension/` folder in Chrome (see `chrome-extension/QUICKSTART.md`)

## AI Models

Overwatch includes **38+ AI model variants** for comprehensive security monitoring:

### Vision Models
- **YOLOv8 Detection** (5 variants): General object detection - 80 COCO classes
- **YOLOv8-Pose** (5 variants): Human pose estimation with fall detection
- **YOLOv8-Seg** (5 variants): Instance segmentation with pixel-perfect masks
- **Object Tracking** (5 variants): Persistent IDs, movement paths, dwell time
- **Face Recognition**: DeepFace with age/gender/emotion analysis
- **License Plate Recognition (ALPR)**: Vehicle detection + OCR
- **Weapon Detection**: Guns, knives, weapons with threat assessment
- **Fire & Smoke Detection**: ML + color-based early warning system
- **PPE Detection**: Safety compliance (hard hats, vests, masks, gloves)

### Audio Models
- **Whisper** (5 variants): Speech-to-text in 99 languages
- **YAMNet**: General sound classification (521 classes)
- **PANNs**: Security audio events (gunshots, glass breaking, alarms)

### Quick Reference
```bash
# See all available models
cat MODELS_QUICK_REFERENCE.md

# Complete documentation
cat NEW_MODELS_SUMMARY.md

# Configuration examples
cat config/model_examples.yaml
```

### Install Additional Models
```bash
# Install all AI model dependencies
./scripts/install_models.sh
```

## Configuration

### Hierarchy Configuration
Define your organizational structure in `config/hierarchy.yaml`:

```yaml
organizations:
  - id: org-001
    name: "My Organization"
    sites:
      - id: site-hq
        name: "Headquarters"
        site_type: fixed  # or mobile
        sublocations:
          - id: subloc-entrance
            name: "Main Entrance"
            cameras:
              - id: cam-001
                name: "Front Entrance"
                rtsp_url: "rtsp://username:password@camera-ip:554/stream"
                workflows:
                  - people_detection
```

### Workflow Configuration
Create custom workflows in `config/workflows.yaml`:

```yaml
workflows:
  people_detection:
    model: ultralytics-yolov8
    confidence: 0.7
    classes: [0]  # person class
    alerts:
      - type: webhook
        url: https://your-webhook-url
```

## System Status

- [x] Project structure and documentation
- [x] Backend API server (FastAPI on port 8000)
- [x] RTSP stream ingestion (UniFi, ONVIF, generic)
- [x] Visual workflow engine with builder (port 7003)
- [x] AI Models (38+ variants):
  - [x] YOLOv8 Detection (5 variants)
  - [x] YOLOv8-Pose (5 variants)
  - [x] YOLOv8-Seg (5 variants)
  - [x] Object Tracking (5 variants)
  - [x] Face Recognition (DeepFace)
  - [x] License Plate Recognition (ALPR)
  - [x] Weapon Detection
  - [x] Fire & Smoke Detection
  - [x] PPE Detection
  - [x] Whisper Speech-to-Text (5 variants)
  - [x] YAMNet Audio Classification
  - [x] PANNs Audio Event Detection
- [x] Frontend dashboard (port 7002)
- [x] Event system and real-time alerting
- [x] Alarm management system
- [x] Rules engine (YAML DSL)
- [x] Admin panel (Organizations/Sites/Cameras)
- [x] Federation support (ZeroTier)
- [x] WebSocket live updates
- [x] Testing suite
- [x] Chrome Extension (debug console)
- [ ] Production deployment (authentication needed)

## License

MIT

## Documentation

**📚 [Complete Documentation Index](DOCUMENTATION_INDEX.md)** - Full documentation catalog organized by topic

### Quick Links

**Getting Started**
- [Quick Start](QUICKSTART.md) - Get running in 5 minutes
- [Start Here](START_HERE.md) - Detailed setup guide with troubleshooting
- [System Status](STATUS.md) - Current deployment status

**Core Guides**
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [API Reference](docs/API.md) - REST and WebSocket API documentation
- [Capabilities Matrix](CAPABILITIES.md) - Feature implementation status

**Workflows**
- [Workflow Builder](docs/WORKFLOW_BUILDER.md) - Visual workflow editor guide
- [Workflow Configuration](docs/WORKFLOWS.md) - YAML workflow syntax
- [Config Nodes](docs/CONFIG_NODE_GUIDE.md) - Reusable configurations

**Features**
- [Alarm Management](docs/alarm.md) - Alarm state machine and rules engine
- [Audio Processing](docs/AUDIO_PROCESSING_GUIDE.md) - Whisper and YAMNet integration
- [Federation](docs/FEDERATION.md) - Distributed deployments
- [ZeroTier Networking](docs/ZEROTIER.md) - Overlay networking setup

**Administration**
- [Admin Panel](ADMIN_PANEL_READY.md) - Organization/site/camera management
- [Live Monitoring](docs/LIVE_WORKFLOW_MONITOR.md) - Production monitoring guide
- [Performance Tuning](docs/PERFORMANCE.md) - Optimization tips

**Reference**
- [Complete System Summary](COMPLETE_SYSTEM_SUMMARY.md) - Full feature list and metrics
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and extending Overwatch

