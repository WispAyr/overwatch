# Raspberry Pi 5 Deployment Guide

## Overview

Overwatch can run on Raspberry Pi 5 with some performance considerations. The Pi 5 has sufficient CPU power for real-time video processing, though GPU acceleration is limited compared to NVIDIA CUDA systems.

## Hardware Requirements

### Raspberry Pi 5 Specifications
- **Recommended**: Raspberry Pi 5 (8GB RAM model)
- **Minimum**: Raspberry Pi 5 (4GB RAM)
- **Storage**: 64GB+ microSD card or SSD (recommended)
- **Cooling**: Active cooling (heatsink + fan) required for sustained workloads
- **Power**: Official 27W USB-C power supply

### Performance Expectations
- **Max Concurrent Streams**: 2-4 cameras (depending on resolution)
- **AI Models**: CPU-based inference (no CUDA)
- **Frame Rate**: 5-15 FPS per stream (YOLOv8n model)
- **Best Use Case**: Edge node in federation architecture

## Installation on Raspberry Pi 5

### 1. OS Setup

**Recommended OS**: Raspberry Pi OS (64-bit) Lite or Desktop

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libharfbuzz0b \
    libwebp7 \
    libjasper1 \
    libilmbase25 \
    libopenexr25 \
    libgstreamer1.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libgtk-3-dev
```

### 2. Install Node.js

```bash
# Install Node.js 18+ (required for workflow builder)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 3. Clone Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/overwatch.git
cd overwatch
```

### 4. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

**Note**: Initial installation will take 30-60 minutes on Pi 5 due to compiling Python packages.

### 5. Optimize for ARM64

Edit `requirements.txt` to use optimized packages:

```bash
# After running install.sh, install ARM-optimized packages
source venv/bin/activate

# Use lighter PyTorch build for ARM
pip install torch==2.0.0 torchvision==0.15.0 --index-url https://download.pytorch.org/whl/cpu

# Skip heavy optional dependencies (install only what you need)
# Skip tensorflow if not using YAMNet/audio models
```

## Configuration for Raspberry Pi

### 1. Environment Variables

Create `.env` file:

```bash
# Device Configuration
DEVICE=cpu  # Pi 5 doesn't support CUDA

# Performance Tuning
MAX_CONCURRENT_STREAMS=2  # Limit to 2-4 cameras
FRAME_BUFFER_SIZE=10  # Reduce buffer size
LOG_LEVEL=WARNING  # Reduce logging overhead

# Model Selection
ULTRALYTICS_MODEL_PATH=./models/yolov8n.pt  # Use smallest model
```

### 2. Workflow Configuration

Use lightweight models in `config/workflows.yaml`:

```yaml
workflows:
  people_detection:
    model: ultralytics-yolov8n  # Use 'n' (nano) variant, not 'x'
    confidence: 0.7
    classes: [0]
    skip_frames: 2  # Process every 3rd frame
```

### 3. System Optimization

```bash
# Increase swap space for model loading
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Enable performance governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Running Overwatch on Pi 5

### Manual Start

```bash
# Terminal 1: Backend
./run.sh

# Terminal 2: Dashboard (if running locally)
./scripts/start_dashboard.sh
```

### Systemd Service (Auto-start on boot)

Create `/etc/systemd/system/overwatch.service`:

```ini
[Unit]
Description=Overwatch Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/overwatch
ExecStart=/home/pi/overwatch/venv/bin/python /home/pi/overwatch/backend/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable overwatch
sudo systemctl start overwatch
sudo systemctl status overwatch
```

### Dashboard Service

Create `/etc/systemd/system/overwatch-dashboard.service`:

```ini
[Unit]
Description=Overwatch Dashboard
After=network.target overwatch.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/overwatch/frontend
ExecStart=/usr/bin/python3 -m http.server 7002
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable overwatch-dashboard
sudo systemctl start overwatch-dashboard
```

## Federation Deployment

Raspberry Pi 5 is ideal as an **edge node** in federation architecture:

```yaml
# config/federation.yaml
node:
  id: "edge-pi-001"
  name: "Warehouse Edge Node"
  role: "edge"  # Not 'central'
  
  # Connect to central server
  central_server: "https://central.example.com:8000"
  
  # ZeroTier network for secure communication
  zerotier_network: "YOUR_NETWORK_ID"
```

### Federation Benefits
- **Local Processing**: Process video locally, send events only
- **Bandwidth Efficient**: Don't stream video over network
- **Resilient**: Operates independently if network fails
- **Scalable**: Deploy multiple Pi nodes to different sites

## Performance Tuning

### Model Selection by Performance

| Model | FPS (Pi 5) | Accuracy | Use Case |
|-------|------------|----------|----------|
| YOLOv8n | 10-15 | Good | Edge deployment |
| YOLOv8s | 5-8 | Better | Single camera |
| YOLOv8m | 2-4 | Best | Accuracy critical |
| YOLOv8l/x | <2 | Excellent | Not recommended for Pi |

### Skip Frames

Process every Nth frame to improve throughput:

```python
# In workflow configuration
skip_frames: 2  # Process every 3rd frame (30fps → 10fps)
```

### Reduce Resolution

```yaml
cameras:
  - id: cam-001
    rtsp_url: "rtsp://camera/substream"  # Use lower resolution stream
```

### Disable Audio Processing

Audio models (Whisper, YAMNet) are CPU-intensive. Disable if not needed:

```bash
# Don't install optional audio dependencies
# pip install openai-whisper  # Skip this
# pip install tensorflow tensorflow-hub  # Skip this
```

## Monitoring

### Check System Resources

```bash
# CPU/Memory usage
htop

# Temperature (should stay < 80°C)
vcgencmd measure_temp

# Check Overwatch logs
tail -f ~/overwatch/logs/overwatch.log

# API health check
curl http://localhost:8000/health
```

### Performance Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics
```

## Troubleshooting

### Out of Memory Errors

```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Or limit concurrent streams
export MAX_CONCURRENT_STREAMS=1
```

### Thermal Throttling

```bash
# Check throttling status
vcgencmd get_throttled

# Install active cooling or reduce workload
```

### Slow Frame Processing

```bash
# Use nano model
export ULTRALYTICS_MODEL_PATH=./models/yolov8n.pt

# Skip frames
# Edit workflow: skip_frames: 3
```

## Network Setup (Headless Deployment)

### ZeroTier for Remote Access

```bash
# Install ZeroTier
curl -s https://install.zerotier.com | sudo bash

# Join network
sudo zerotier-cli join YOUR_NETWORK_ID

# Check status
sudo zerotier-cli listnetworks
```

Access dashboard remotely: `http://[ZEROTIER_IP]:7002`

### WiFi Configuration

```bash
sudo nmcli dev wifi connect "SSID" password "PASSWORD"
```

## Security Recommendations

### Firewall

```bash
sudo apt install ufw
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 8000/tcp # API (only if exposing)
sudo ufw enable
```

### Authentication (Production)

Enable authentication in production deployments:

```bash
# Add to .env
API_SECRET_KEY=your-long-random-secret-key
REQUIRE_AUTH=true
```

## Cost Analysis

**Total Cost for Pi 5 Edge Node:**
- Raspberry Pi 5 (8GB): $80
- 128GB SSD: $25
- Active Cooling: $10
- Power Supply: $12
- **Total**: ~$127 per edge node

**vs. Cloud Computing:**
- AWS EC2 t3.medium: ~$30/month = $360/year
- Pi 5 pays for itself in 5 months

## Limitations

**Not Recommended On Pi 5:**
- ❌ Large models (YOLOv8x, Whisper Large)
- ❌ Real-time audio processing with TensorFlow models
- ❌ More than 4 concurrent camera streams
- ❌ High-resolution (4K) video processing
- ❌ Training AI models

**Recommended Use Cases:**
- ✅ Edge video processing (2-4 cameras)
- ✅ Federated architecture edge nodes
- ✅ Local zone-based detection
- ✅ Remote site monitoring
- ✅ Mobile deployment units

## Example: Mobile Deployment

Deploy Pi 5 in vehicles, temporary sites, or mobile units:

```yaml
# config/hierarchy.yaml
organizations:
  - id: org-001
    sites:
      - id: mobile-unit-01
        name: "Mobile Surveillance Unit #1"
        site_type: mobile
        sublocations:
          - id: vehicle-cameras
            cameras:
              - id: front-cam
                rtsp_url: "rtsp://10.0.0.100:554/stream"
```

Pi 5 + Battery + 4G/LTE = Portable surveillance system

## Updates and Maintenance

```bash
# Update Overwatch
cd ~/overwatch
git pull
./install.sh

# Restart services
sudo systemctl restart overwatch
sudo systemctl restart overwatch-dashboard
```

## Support

For Pi-specific issues, check:
- System logs: `journalctl -u overwatch -f`
- Temperature: `vcgencmd measure_temp`
- Throttling: `vcgencmd get_throttled`
- Memory: `free -h`

## Summary

**Raspberry Pi 5 Readiness**: ✅ YES

- Fully compatible with ARM64 architecture
- Recommended for edge nodes (2-4 cameras)
- Best performance with YOLOv8n model
- Ideal for federated deployments
- Cost-effective alternative to cloud computing
- Requires active cooling and optimization
- Not suitable for central/master nodes with many cameras

**Deployment Time**: 1-2 hours (including OS setup and installation)

