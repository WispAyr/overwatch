# Enhanced Workflow Nodes - Complete Feature Exposure

## ✅ All Nodes Enhanced

Every workflow node now exposes **complete configuration** through the UI - no external config needed!

---

## 📹 Input Nodes

### CameraNode
**New Features**:
- ⚡ **Processing FPS** slider (1-30 fps)
- 🎬 **Stream Quality** selector (high/medium/low)
- 🎞️ **Skip Similar Frames** toggle
- 💾 **Pre-event Buffer** with duration slider (0-60s)
- 📊 **Live Preview** with MJPEG/snapshot fallback
- 🟢 **Status Indicators** (LIVE/OFFLINE)

**Access**: Click ⚙️ button on camera node

### VideoInputNode
**New Features**:
- 📁 **File Upload** with drag-drop support
- ▶️ **Playback Controls** (play/pause/seek)
- 🔁 **Loop Toggle**
- ⚡ **Processing FPS** slider (1-60 fps)
- 🎥 **Playback Speed** (0.25x - 2.0x)
- 🎞️ **Skip Similar Frames** toggle
- 📊 **Video Progress Bar** (clickable seek)
- ⏱️ **Duration Display**

**Access**: Built-in "Change File" button + ⚙️ for advanced

### YouTubeNode  
**New Features**:
- 🔗 **URL Validation** with live feedback
- 🎬 **Quality Selection** (best/1080p/720p/480p/360p/worst)
- ⚡ **Processing FPS** slider (1-30 fps)
- 🎵 **Extract Audio** toggle
- 🖼️ **Thumbnail Preview**
- ✅ **Live/Video Detection**
- 📊 **Configuration Summary**

**Access**: Click ⚙️ button

---

## 🤖 AI Model Node

### ModelNode (All YOLO/Detection Models)
**New Features**:
- 🎯 **Class Selection System**:
  - Multi-select checkboxes for 80 COCO classes
  - 🔍 Search filter
  - 📂 Categorized display (People, Vehicles, Animals, etc.)
  - ⚡ Quick Presets:
    - 👥 People Only
    - 🚗 All Vehicles
    - 🚶🚗 People & Vehicles
    - 🐕 Animals
    - 🎒 Bags & Luggage
    - 🌐 All Classes (80 total)
- 🎯 **Confidence Threshold** slider (0-100%)
- ⚡ **Processing FPS** (1-30 fps)
- 📦 **Batch Size** selector (1/2/4/8/16)
- 🔄 **IOU Threshold** for NMS (0.1-0.9)
- **Advanced Options** (collapsible):
  - 🔢 Max Detections per frame
  - 🎭 Class-agnostic NMS toggle
  - ⚡ Half Precision (FP16) toggle
- 📊 **Live Detection Preview**
- 📈 **Configuration Summary**

**Access**: Click ⚙️ button → "Select" for classes

---

## 📍 Processing Nodes

### ZoneNode
**New Features**:
- 🏷️ **Zone Label** custom naming
- 📐 **Zone Type** selector:
  - Polygon (multi-point)
  - Rectangle (simple box)
  - Line Crossing (directional)
- 🔁 **Filter Type**: Include/Exclude
- 📐 **Polygon Editor** with JSON input
- ⚡ **Quick Presets**:
  - Rectangle
  - Diamond
  - Pentagon
- ⏱️ **Cooldown** slider (0-300s)
- ⏲️ **Min Dwell Time** (object must stay X seconds)
- 👁️ **Visual Preview** with color-coded zones
- 📊 **Configuration Summary**

**Access**: Click ⚙️ button

### ParkingViolationNode
**Advanced Features** (Already Implemented):
- 📐 **Interactive Zone Drawing** on camera frame
- 🎨 **Canvas-based Zone Editor**:
  - Click to add polygon points
  - Visual zone preview with colors
  - Multiple zones support
  - Delete/edit zones
- 🚗 **Restriction Types**:
  - 🟡 Double Yellow Lines
  - 🚫 No Parking Zone
  - ⚠️ Restricted Zone
  - 📦 Loading Bay Only
  - ♿ Disabled Parking Only
  - ⏰ Time Restricted
- ⏱️ **Dwell Time Threshold** slider (5-300s)
- 🔢 **License Plate Recognition** toggle
- ⏰ **Time Restrictions** with hour range
- 📊 **Violation Counter**
- 📝 **Recent Violations** display

**Access**: Click "📐 Zones" button for editor

### DayNightDetectorNode
**Features** (Already Implemented):
- 🌓 **Detection Modes**:
  - Day/Night/IR detection
  - Day only
  - Night only
  - IR only
- 🎚️ **Sensitivity** slider
- 🌙 **IR Threshold** adjustment
- ☀️ **Brightness Threshold** control
- ⏱️ **Check Interval** (1-60s)
- 📊 **Live Preview** with:
  - Real-time brightness gauge
  - Current state (Day/Night/IR)
  - Visual indicators
- 📈 **WebSocket Integration** for live data

**Access**: Click ⚙️ button

---

## 🎵 Audio Nodes

### AudioExtractorNode
**Features** (Already Implemented):
- 🎚️ **Sample Rate** selector (8000/16000/22050/44100/48000 Hz)
- 📻 **Channels**: Mono/Stereo
- 📝 **Audio Format**: WAV/MP3/FLAC/PCM
- ⏱️ **Buffer Duration** (1-60s)
- 📊 **Output Status** display

**Access**: Built-in config always visible

### AudioAINode  
**Features** (Already Implemented):
- 🎤 **Model Selection**:
  - 🎙️ Transcription (Whisper Tiny/Base/Small/Medium/Large)
  - 🔊 Sound Classification (YAMNet/AST/PANNs)
- 🌍 **Language Selection** (10+ languages)
- 🔑 **Trigger Keywords** with tag system:
  - Add/remove keywords
  - Visual keyword chips
  - Enter to add
- 🎯 **Detection Confidence** slider
- ⏱️ **Buffer Duration** control
- 📋 **Sound Classes** display
- 📊 **Live Status**

**Access**: Model dropdown + keyword editor always visible

### AudioVUNode
**Extensive Features** (Already Implemented):
- 📊 **Display Modes**:
  - VU Meter
  - Spectrum Analyzer
  - Waveform
  - Combined
- 🎚️ **Sensitivity** slider
- 📻 **Frequency Bands** selector (4/8/16/32)
- 📌 **Peak Hold** toggle
- 🎨 **Color Schemes**:
  - Gradient (Green→Yellow→Red)
  - Classic VU
  - Neon
  - Monochrome
- 🎯 **Threshold Triggers**:
  - Enable/disable
  - Level slider (0-100%)
  - Trigger modes (continuous/rising_edge/falling_edge)
  - Hysteresis (prevents flickering)
- 📊 **Live Visualization**:
  - Real-time frequency spectrum
  - Animated VU meters
  - Peak indicators
  - Trigger status
- 🔌 **WebSocket Integration** for live audio

**Access**: All controls visible by default

---

## ⚡ Action Nodes

### ActionNode
**New Complete Configuration**:
- 🎯 **Action Type Selector** with 7 types:
  - 📧 **Email**:
    - To address (required)
    - CC addresses
    - Subject line
    - Include snapshot checkbox
    - Include detections checkbox
  - 🔗 **Webhook**:
    - URL (required)
    - Method (POST/PUT)
    - Timeout (1-60s)
    - Retries slider (0-5)
  - 🎥 **Record Video**:
    - Duration slider (10-300s)
    - Pre-buffer slider (0-60s)
    - Post-buffer slider (0-60s)
    - Format (MP4/MKV)
    - Quality (High/Medium/Low)
    - Total clip duration display
  - 📸 **Snapshot**:
    - Draw bounding boxes toggle
    - Draw zones toggle
    - Format (JPEG/PNG)
    - Quality slider (50-100)
  - 🚨 **Alert**:
    - Severity (Info/Warning/Critical)
    - Custom message textarea
    - Notify channels (multi-select):
      - Email
      - SMS
      - PagerDuty
      - Webhook
  - 📱 **SMS**:
    - Phone number
    - Message (160 char limit with counter)
  - 📟 **PagerDuty**

- 📊 **Activity Monitor** (toggle to see trigger count)
- 📝 **Smart Summary** shows key config when collapsed

**Access**: Click ⚙️ → Select action type → Configure

---

## 🔗 UniFi Nodes

### UniFiCameraDiscoveryNode
**Features** (Already Implemented):
- 🔑 **Credential Selector** dropdown
- 📡 **Filter State**: all/connected/disconnected
- 🎥 **Filter Recording**: all/recording/not recording
- ✓ **Live Credential Validation**

### UniFiProtectEventNode
**Features** (Already Implemented):
- 🔑 **Credential Selector**
- 📋 **Event Types** (multi-select):
  - Motion
  - Smart Detection
  - Doorbell Ring
- 🧠 **Smart Detection Types**:
  - Person
  - Vehicle
  - Animal
- ⏱️ **Poll Interval** slider (5-60s)
- 🎯 **Camera Filter** (specific cameras only)

### UniFiAddCameraNode
**Features** (Already Implemented):
- 📍 **Sublocation Selector**
- 🎬 **Stream Quality**: high/medium/low
- ✅ **Auto-enable** toggle

---

## 🛸 Drone Nodes

All drone nodes already have comprehensive configuration:
- **DroneInputNode**: Meshtastic receiver settings
- **DroneFilterNode**: Altitude/speed/geofence filters
- **DroneMapNode**: Map visualization settings
- **DroneActionNode**: Multiple action types
- **DroneAnalyticsNode**: Statistical analysis config

---

## 🔧 Utility Nodes

### DataPreviewNode
**Features** (Already Implemented):
- 📊 Live data display
- 🔄 Auto-refresh
- 📋 JSON formatting
- 📈 Detection counters

### DebugNode
**Extensive Features** (Already Implemented):
- 🔍 **Filter Modes**: Connected nodes only / All nodes
- 📊 **Message Limit** slider (10-100)
- 🔔 **System Messages** toggle
- 📝 **Message Types**:
  - Debug messages
  - Detection data
  - Status updates
  - Errors
- 🎨 **Color-coded** messages
- ⏱️ **Timestamps**
- 📈 **Message Counter**
- 🔌 **WebSocket Connection** indicator

### ConfigNode
**Features** (Already Implemented):
- 🏷️ **Config Name** editor
- 📝 **JSON Editor** with validation
- 📋 **Template Library**:
  - YOLO Person Detection
  - YOLO Vehicle Detection
  - Webhook POST
  - Recording Standard
  - Email Alert
- ✅ **Validation** with error messages
- 📦 **Reusable Configurations**

### CatchNode
**Features** (Already Implemented):
- 🎯 **Error Scope**: all/specific nodes
- 📋 **Node ID List** for specific catching
- 🔔 **Error Handling** logic

### LinkIn/Out/CallNodes
**Features** (Already Implemented):
- 🏷️ **Link Name** configuration
- 📝 **Description** field
- 📦 **Parameters** (for LinkCall)
- 🔗 **Subflow Integration**

---

## 📊 Feature Summary by Node

| Node | Total Features | Config Options | Live Preview | Advanced Options |
|------|----------------|----------------|--------------|------------------|
| **ModelNode** | 15+ | ✅ | ✅ | ✅ |
| **CameraNode** | 8 | ✅ | ✅ | ✅ |
| **VideoInputNode** | 10+ | ✅ | ✅ | ✅ |
| **YouTubeNode** | 7 | ✅ | ✅ | ✅ |
| **ZoneNode** | 10+ | ✅ | ✅ | ✅ |
| **ActionNode** | 30+ | ✅ | ✅ | ✅ |
| **AudioExtractorNode** | 5 | ✅ | ❌ | ❌ |
| **AudioAINode** | 8+ | ✅ | ✅ | ✅ |
| **AudioVUNode** | 15+ | ✅ | ✅ | ✅ |
| **DayNightNode** | 10+ | ✅ | ✅ | ✅ |
| **ParkingNode** | 20+ | ✅ | ✅ | ✅ |
| **UniFi Nodes** | 8+ each | ✅ | ❌ | ✅ |
| **Drone Nodes** | 10+ each | ✅ | ✅ | ✅ |
| **DebugNode** | 10+ | ✅ | ✅ | ✅ |

**Total: 200+ configurable parameters across all nodes!**

---

## 🎨 UI/UX Enhancements

### Common Patterns

1. **⚙️ Settings Button** - Standard across all nodes
2. **Collapsible Panels** - Clean interface, expandable details
3. **Live Previews** - Real-time data visualization
4. **Smart Defaults** - Sensible starting values
5. **Validation** - Real-time feedback on invalid config
6. **Tooltips** - Helpful descriptions on hover
7. **Summaries** - Key config visible when collapsed
8. **Color Coding** - Visual type identification

### Feature Categories

#### Core Configuration
- All nodes expose their primary parameters
- No need for external YAML/JSON editing
- Save happens automatically

#### Advanced Options
- Collapsible "Advanced" sections
- Power user features hidden by default
- Expert-level tuning available

#### Live Monitoring
- Real-time status indicators
- Connection status (WebSocket)
- Performance metrics
- Activity counters

#### Visual Feedback
- Color-coded borders per node type
- Status badges (✓/✗/⚠️)
- Progress bars and meters
- Live preview panels

---

## 🚀 Usage Examples

### 1. Configure AI Model to Detect Only People and Cars

```
1. Drag "Model" node (e.g., YOLOv8n)
2. Click ⚙️ to expand
3. Click "Select" next to "Detect Classes"
4. Click "👥 People Only" preset
5. Also check "car" checkbox
6. Adjust confidence to 75%
7. Set FPS to 15
8. Done! All configured visually
```

### 2. Set Up Parking Violation Detection

```
1. Drag "Parking Violation" node
2. Click "📐 Zones" button
3. Click on camera preview to draw polygon
4. Click 3+ points to define no-parking zone
5. Click "✓ Finish Zone"
6. Set dwell time to 30s
7. Enable license plate check
8. Done!
```

### 3. Configure Email Alerts

```
1. Drag "Action" node
2. Click ⚙️
3. Select "📧 Email" from dropdown
4. Enter: security@company.com
5. Set subject: "Security Alert"
6. Check "Include snapshot"
7. Check "Include detections"
8. Done!
```

### 4. YouTube Stream Analysis

```
1. Drag "YouTube" node
2. Paste URL: https://youtube.com/watch?v=xxxxx
3. Click ⚙️
4. Select quality: 720p
5. Set FPS: 10
6. Enable "Extract audio" if needed
7. Done! Thumbnail previews automatically
```

---

## 💡 Key Benefits

### For Users
- ✅ **Zero External Config** - Everything in the UI
- ✅ **Visual Feedback** - See what you're configuring
- ✅ **No Code Required** - Point and click
- ✅ **Live Validation** - Errors shown immediately
- ✅ **Smart Presets** - Common scenarios one-click
- ✅ **Documentation Built-In** - Tooltips and hints

### For Power Users
- ✅ **Advanced Options** - Full control when needed
- ✅ **Batch Configuration** - Config nodes for reuse
- ✅ **Performance Tuning** - FPS, batch size, IOU, etc.
- ✅ **Expert Features** - FP16, NMS, thresholds

### For Developers
- ✅ **Modular Design** - Easy to extend
- ✅ **Consistent Patterns** - Similar UI across nodes
- ✅ **State Management** - React hooks pattern
- ✅ **Backend Integration** - Auto-sync with API

---

## 🎯 Design Philosophy

### 1. Progressive Disclosure
- Basic options visible by default
- Advanced options hidden in collapsible sections
- Expert features in "Advanced" panels

### 2. Sensible Defaults
- Every parameter has a smart default
- Works out-of-box without configuration
- Tune only what you need

### 3. Visual Feedback
- Live previews show real data
- Status indicators show connection state
- Validation shows errors immediately

### 4. Self-Documenting
- Tooltips explain every option
- Help text shows units and ranges
- Examples provided inline

---

## 📚 Complete Configuration Matrix

### Input Parameters Matrix

| Node | FPS | Quality | Loop | Audio | Buffer | Other |
|------|-----|---------|------|-------|--------|-------|
| Camera | ✅ | ✅ | ❌ | ❌ | ✅ | Skip Similar |
| Video | ✅ | ❌ | ✅ | ❌ | ❌ | Speed Control |
| YouTube | ✅ | ✅ | ❌ | ✅ | ❌ | Auto-detect |
| Model | ✅ | ❌ | ❌ | ❌ | ❌ | Classes, IOU, Batch |
| Zone | ❌ | ❌ | ❌ | ❌ | ❌ | Polygon, Cooldown |
| Action | ❌ | ❌ | ❌ | ❌ | ✅ | Type-specific |

### Detection Parameters Matrix

| Model Feature | ModelNode | ParkingNode | DayNightNode |
|---------------|-----------|-------------|--------------|
| Confidence | ✅ | ❌ | ❌ |
| Classes | ✅ | ❌ | ❌ |
| Zones | ❌ | ✅ | ❌ |
| Thresholds | ✅ (IOU) | ✅ (Dwell) | ✅ (Brightness) |
| Time-based | ❌ | ✅ | ✅ |

---

## 🔮 Future Enhancements

While comprehensive, potential additions:
1. **Visual Zone Editor** for ZoneNode (like ParkingNode canvas)
2. **Drag-and-Drop** polygon point editing
3. **Class Filtering** in ZoneNode (per-zone classes)
4. **Custom Color Schemes** user-configurable
5. **Template Save/Load** for node configurations
6. **Batch Operations** (apply config to multiple nodes)
7. **Configuration Presets** library per node type
8. **Export/Import** node configurations

---

## ✅ Status

**Implementation**: 100% Complete
**Documentation**: ✅ Complete  
**Testing**: Ready
**Production**: Ready

All workflow nodes now expose **complete functionality** through the UI. Users can configure everything visually without touching YAML or JSON files (unless they want to via ConfigNode).

---

## 🎓 Quick Start Guide

### New User Path

1. **Drag Input Node** (Camera/Video/YouTube)
   - Configure source (URL, file, camera ID)
   - Set FPS and quality

2. **Drag Model Node**
   - Click ⚙️
   - Click "Select" for classes
   - Choose preset or individual classes
   - Adjust confidence

3. **Drag Zone Node** (optional)
   - Define area of interest
   - Set filter type (include/exclude)

4. **Drag Action Node**
   - Click ⚙️
   - Select action type
   - Configure destination (email/webhook/etc)

5. **Connect with Edges** - Visual flow

6. **Save & Start** - Workflow runs with all UI config!

No external configuration files needed! 🎉

