# Device Management and Federation Guide

## Overview

This guide covers the new Device Management and Federation features added to Overwatch. These features enable:

1. **Device Management**: Update devices from GitHub, configure device-specific settings, and manage autostart
2. **Local Network Discovery**: Automatically discover other Overwatch devices on the local network using mDNS
3. **Federation Enhancement**: Improved federation with bidirectional sync of workflows, cameras, and configurations
4. **Multi-Branch Support**: Automatic branch selection (main for servers, ras-pi for Raspberry Pi devices)

## Architecture

### Components

#### 1. Device Configuration (`backend/models/device_config.py`)
- Stores device-specific configuration and settings
- Automatically detects device type (server, raspberry-pi, edge)
- Manages persistent configuration in `config/device.json`

**Key Features:**
- Device information (ID, name, type, platform)
- Settings (autostart, auto-update, sync, performance limits)
- Automatic branch mapping for device types

#### 2. Device Manager (`backend/core/device_manager.py`)
- Handles device updates from GitHub
- Manages system configuration and autostart
- Provides system information and status

**Key Features:**
- Check for updates from appropriate branch
- Apply updates with automatic dependency installation
- Enable/disable autostart (systemd or cron)
- System restart scheduling

#### 3. Discovery Service (`backend/federation/discovery.py`)
- Uses mDNS/Zeroconf for local network discovery
- Announces this device to the network
- Discovers other Overwatch devices

**Key Features:**
- Service type: `_overwatch._tcp.local.`
- Automatic device registration with federation
- Real-time device add/remove notifications
- Callback system for discovery events

#### 4. Sync Service (`backend/federation/sync.py`)
- Bidirectional synchronization between nodes
- Syncs workflows, cameras, and configurations
- Conflict resolution and merge strategies

**Key Features:**
- Periodic sync loop
- Edge nodes sync FROM central
- Central node syncs WITH edge nodes
- Resource hash tracking for change detection

### API Endpoints

#### Device Management (`/api/device`)

```
GET  /api/device/info                    - Get comprehensive device information
GET  /api/device/config                  - Get device configuration
PATCH /api/device/config                 - Update device configuration
GET  /api/device/updates/check           - Check for available updates
POST /api/device/updates/apply           - Apply updates (optional restart)
GET  /api/device/branch                  - Get current and recommended branch
POST /api/device/branch/switch           - Switch to different branch
POST /api/device/autostart/enable        - Enable autostart on boot
POST /api/device/autostart/disable       - Disable autostart
POST /api/device/restart                 - Restart the system
GET  /api/device/discovery/devices       - Get discovered devices
GET  /api/device/discovery/status        - Get discovery service status
POST /api/device/discovery/scan          - Trigger manual scan
```

#### Federation (Enhanced)

```
GET  /api/federation/cluster/status      - Get cluster status
GET  /api/federation/cluster/nodes       - List all federated nodes
POST /api/federation/register            - Register a node
POST /api/federation/unregister          - Unregister a node
POST /api/federation/heartbeat           - Send heartbeat
POST /api/federation/events              - Forward event
POST /api/federation/sync/hierarchy      - Sync hierarchy
```

## Configuration

### Device Configuration (`config/device.json`)

```json
{
  "info": {
    "device_id": "overwatch-server-1",
    "device_name": "main-server",
    "device_type": "server",
    "hostname": "main-server",
    "platform": "Linux-5.15.0",
    "architecture": "x86_64",
    "python_version": "3.11.0",
    "git_branch": "main",
    "git_commit": "abc123..."
  },
  "settings": {
    "autostart_enabled": false,
    "auto_update_enabled": false,
    "update_channel": "stable",
    "update_check_interval": 3600,
    "enable_discovery": true,
    "discovery_interval": 60,
    "auto_sync_enabled": true,
    "sync_workflows": true,
    "sync_cameras": true,
    "sync_rules": true,
    "max_cpu_percent": 80,
    "max_memory_percent": 80,
    "enable_gpu": true,
    "max_recording_days": 7,
    "max_snapshot_days": 30,
    "auto_cleanup_enabled": true
  }
}
```

### Environment Variables

```bash
# Device Configuration
DEVICE_TYPE=server              # server, raspberry-pi, edge
NODE_ID=overwatch-node-1        # Unique device ID

# Federation (existing)
ENABLE_FEDERATION=true
NODE_TYPE=central               # central or edge
NODE_URL=http://localhost:8000
CENTRAL_SERVER_URL=http://central.example.com:8000

# Discovery
ENABLE_DISCOVERY=true           # Enable mDNS discovery
```

## Usage

### 1. Device Management UI

Access the device management interface at:
```
http://localhost:8000/device-management.html
```

**Features:**
- View local device information
- Check for updates
- Apply updates (with automatic restart)
- Configure autostart
- Manage device settings
- View discovered devices
- Monitor federated nodes

### 2. Updating a Device

**Manual Update:**
```bash
# Check for updates
curl http://localhost:8000/api/device/updates/check

# Apply update without restart
curl -X POST http://localhost:8000/api/device/updates/apply

# Apply update with restart
curl -X POST "http://localhost:8000/api/device/updates/apply?restart=true"
```

**Automatic Updates:**
```bash
# Enable auto-update in configuration
curl -X PATCH http://localhost:8000/api/device/config \
  -H "Content-Type: application/json" \
  -d '{"auto_update_enabled": true}'
```

### 3. Network Discovery

**Enable Discovery:**
```bash
curl -X PATCH http://localhost:8000/api/device/config \
  -H "Content-Type: application/json" \
  -d '{"enable_discovery": true}'
```

**Scan Network:**
```bash
curl -X POST http://localhost:8000/api/device/discovery/scan
```

**View Discovered Devices:**
```bash
curl http://localhost:8000/api/device/discovery/devices
```

### 4. Federation Setup

#### Central Server Setup:
```bash
# .env
ENABLE_FEDERATION=true
NODE_TYPE=central
NODE_ID=overwatch-central
NODE_URL=http://central.example.com:8000
ENABLE_DISCOVERY=true
```

#### Edge Node Setup:
```bash
# .env
ENABLE_FEDERATION=true
NODE_TYPE=edge
NODE_ID=overwatch-edge-1
NODE_URL=http://edge1.example.com:8000
CENTRAL_SERVER_URL=http://central.example.com:8000
ENABLE_DISCOVERY=true
```

### 5. Autostart Configuration

**Enable Autostart (systemd):**
```bash
curl -X POST http://localhost:8000/api/device/autostart/enable
```

This creates a systemd service:
```ini
[Unit]
Description=Overwatch Surveillance System
After=network.target

[Service]
Type=simple
User=overwatch
WorkingDirectory=/path/to/overwatch
ExecStart=/path/to/overwatch/run.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable Autostart (cron):**
```bash
# On systems without systemd
# Adds to crontab:
@reboot cd /path/to/overwatch && ./run.sh
```

## Branch Management

### Device Type to Branch Mapping

| Device Type    | Git Branch | Description                    |
|---------------|------------|--------------------------------|
| server        | main       | Full-featured server deployment|
| raspberry-pi  | ras-pi     | Optimized for Raspberry Pi     |
| edge          | main       | Edge computing devices         |

### Switching Branches

**Check Current Branch:**
```bash
curl http://localhost:8000/api/device/branch
```

**Switch Branch:**
```bash
curl -X POST http://localhost:8000/api/device/branch/switch \
  -H "Content-Type: application/json" \
  -d '{"branch": "ras-pi"}'
```

## Synchronization

### Workflow Sync

When enabled, workflows are automatically synchronized:
- **Edge → Central**: Edge nodes can contribute workflows
- **Central → Edge**: Central distributes workflows to edges

### Camera Sync

Camera configurations (metadata only, not credentials) sync across nodes.

### Hierarchy Sync

Organizational hierarchy syncs from central to edge nodes.

### Manual Sync

```bash
# Trigger manual sync (edge node)
curl -X POST http://localhost:8000/api/federation/sync/hierarchy
```

## Discovery Service Details

### mDNS Service Advertisement

**Service Type:** `_overwatch._tcp.local.`

**Service Properties:**
```
device_id: overwatch-node-1
device_type: server
node_type: central
version: 1.0.0
api_port: 8000
hostname: server1
```

### Auto-Registration

When a device is discovered:
1. Discovery service detects new device via mDNS
2. Device information is extracted
3. Node is automatically registered with federation manager
4. Bidirectional sync begins (if enabled)

## Deployment Scenarios

### Scenario 1: Single Server

```bash
# .env
DEVICE_TYPE=server
ENABLE_FEDERATION=false
ENABLE_DISCOVERY=false
```

### Scenario 2: Central + Edge Nodes

**Central:**
```bash
DEVICE_TYPE=server
ENABLE_FEDERATION=true
NODE_TYPE=central
ENABLE_DISCOVERY=true
```

**Edge (Raspberry Pi):**
```bash
DEVICE_TYPE=raspberry-pi
ENABLE_FEDERATION=true
NODE_TYPE=edge
CENTRAL_SERVER_URL=http://central:8000
ENABLE_DISCOVERY=true
```

### Scenario 3: Distributed Mesh

All nodes with discovery enabled will automatically find and connect to each other.

## Troubleshooting

### Updates Not Working

1. Check git configuration:
```bash
cd /path/to/overwatch
git status
git remote -v
```

2. Check for uncommitted changes:
```bash
git stash
git pull origin main
```

3. Check API logs:
```bash
tail -f logs/overwatch.log | grep device
```

### Discovery Not Finding Devices

1. Check if zeroconf is installed:
```bash
pip install zeroconf>=0.132.0
```

2. Check firewall rules (allow mDNS port 5353):
```bash
sudo ufw allow 5353/udp
```

3. Verify discovery service is running:
```bash
curl http://localhost:8000/api/device/discovery/status
```

### Autostart Not Working

**systemd:**
```bash
sudo systemctl status overwatch
sudo systemctl enable overwatch
sudo systemctl start overwatch
```

**cron:**
```bash
crontab -l  # Check if entry exists
crontab -e  # Edit if needed
```

## Security Considerations

1. **Update Authentication**: Updates require git credentials for private repos
2. **Federation Auth**: Use API keys or JWT tokens for production
3. **mDNS Security**: Discovery is local network only
4. **Credential Sync**: Camera credentials are NOT synced by default

## Best Practices

1. **Use Stable Channel**: Set `update_channel: "stable"` for production
2. **Enable Auto-Sync**: Keep nodes synchronized automatically
3. **Monitor Updates**: Check update status regularly
4. **Test Before Deploy**: Test updates on edge nodes first
5. **Backup Config**: Backup `config/device.json` before major updates

## Integration with Existing Features

### Workflows
- Workflows sync automatically between nodes
- Edge nodes can create workflows
- Central distributes workflows to all edges

### Cameras
- Camera metadata syncs (not credentials)
- Stream processing can be distributed

### Events
- Events forward from edge to central
- Central can aggregate from all edges

### Alarms
- Alarms sync across federation
- Central can manage all alarms

## Future Enhancements

- [ ] Encrypted sync channels
- [ ] Conflict resolution UI
- [ ] Rollback capability
- [ ] Update scheduling
- [ ] Bandwidth throttling for updates
- [ ] Selective sync (choose what to sync)
- [ ] Multi-central federation
- [ ] P2P discovery without central server

## Support

For issues or questions:
1. Check logs: `logs/overwatch.log`
2. Check API documentation: `http://localhost:8000/docs`
3. Review federation status: `http://localhost:8000/api/federation/cluster/status`

