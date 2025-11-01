# Branch Deployment Strategy: Main & Raspberry Pi

## Overview

This document explains how the device management and federation features work seamlessly across both the `main` and `ras-pi` branches.

## Branch Architecture

### Main Branch
- **Target**: Full-featured servers (x86_64, high-resource systems)
- **Features**: All Overwatch features enabled
- **Dependencies**: Full ML/AI stack, GPU support
- **Use Cases**: Central servers, high-performance edge nodes

### Ras-Pi Branch
- **Target**: Raspberry Pi devices (ARM architecture, resource-constrained)
- **Features**: Optimized subset, lighter dependencies
- **Dependencies**: Reduced ML models, CPU-optimized
- **Use Cases**: Remote sensors, edge cameras, distributed monitoring

## How It Works Across Branches

### 1. Automatic Branch Detection

The device manager automatically detects the appropriate branch:

```python
def get_branch_for_device(self) -> str:
    """Get the appropriate git branch for this device type"""
    if not self.info:
        return "main"
    
    branch_mapping = {
        "raspberry-pi": "ras-pi",
        "server": "main",
        "edge": "main"
    }
    
    return branch_mapping.get(self.info.device_type, "main")
```

**Detection Methods:**
1. Environment variable: `DEVICE_TYPE=raspberry-pi`
2. Platform detection: ARM architecture → raspberry-pi
3. Hostname patterns: `pi-*` → raspberry-pi
4. Manual configuration in `config/device.json`

### 2. Device Type Detection

Automatic detection at startup:

```python
# Detect device type from environment or platform
device_type = os.getenv('DEVICE_TYPE', 'server')
if 'raspberry' in platform.platform().lower() or 'arm' in platform.machine().lower():
    device_type = 'raspberry-pi'
```

### 3. Update Flow

#### For Server (Main Branch)
```bash
# Device detects it's a server
# Checks for updates from 'main' branch
curl http://localhost:8000/api/device/branch
# Returns: {"current_branch": "main", "recommended_branch": "main"}

# Updates pull from main
git pull origin main
```

#### For Raspberry Pi (Ras-Pi Branch)
```bash
# Device detects it's a Raspberry Pi
# Checks for updates from 'ras-pi' branch
curl http://localhost:8000/api/device/branch
# Returns: {"current_branch": "ras-pi", "recommended_branch": "ras-pi"}

# Updates pull from ras-pi
git pull origin ras-pi
```

## Syncing Changes Between Branches

### Strategy 1: Cherry-Pick Common Changes

For features that work on both branches:

```bash
# On main branch
git commit -m "Add device management feature"
git push origin main

# Switch to ras-pi branch
git checkout ras-pi
git cherry-pick <commit-hash>
git push origin ras-pi
```

### Strategy 2: Merge with Selective Integration

For larger updates:

```bash
# On ras-pi branch
git checkout ras-pi
git merge main --no-commit

# Review changes, exclude incompatible features
git reset HEAD heavy-ml-dependency.py

# Commit compatible changes
git commit -m "Merge device management from main"
git push origin ras-pi
```

### Strategy 3: Branch-Specific Configuration

Use environment-based feature flags:

```python
# In code
if settings.DEVICE_TYPE == "raspberry-pi":
    # Use lightweight model
    model = load_lite_model()
else:
    # Use full model
    model = load_full_model()
```

## Deployment Scenarios

### Scenario 1: Central Server + Raspberry Pi Edges

**Central Server (Main Branch):**
```bash
# .env
DEVICE_TYPE=server
NODE_TYPE=central
ENABLE_FEDERATION=true
ENABLE_DISCOVERY=true
```

**Raspberry Pi Edges (Ras-Pi Branch):**
```bash
# .env
DEVICE_TYPE=raspberry-pi
NODE_TYPE=edge
CENTRAL_SERVER_URL=http://central-server:8000
ENABLE_FEDERATION=true
ENABLE_DISCOVERY=true
```

**How They Sync:**
1. Discovery service finds devices on network
2. Devices auto-register with federation
3. Central distributes workflows (Pi-compatible only)
4. Pi edges process streams locally
5. Pi edges send events to central
6. Both branches use same API contracts

### Scenario 2: All Raspberry Pi Mesh

All devices on ras-pi branch:

```bash
# Each Pi
DEVICE_TYPE=raspberry-pi
NODE_TYPE=edge  # or central for one
ENABLE_FEDERATION=true
ENABLE_DISCOVERY=true
```

### Scenario 3: Mixed Server Environment

Mix of servers and edge devices:

```bash
# High-power server (main)
DEVICE_TYPE=server
NODE_TYPE=central

# Mid-range server (main)
DEVICE_TYPE=edge
NODE_TYPE=edge

# Raspberry Pi (ras-pi)
DEVICE_TYPE=raspberry-pi
NODE_TYPE=edge
```

## Feature Compatibility Matrix

| Feature                    | Main Branch | Ras-Pi Branch | Notes                          |
|---------------------------|-------------|---------------|--------------------------------|
| Device Management         | ✅          | ✅            | Identical implementation       |
| Network Discovery         | ✅          | ✅            | mDNS works on both            |
| Federation                | ✅          | ✅            | Same protocol                 |
| Auto-Update               | ✅          | ✅            | Branch-aware                  |
| Workflow Sync             | ✅          | ✅            | Filter by compatibility       |
| Heavy ML Models           | ✅          | ❌            | Use lite models on Pi         |
| GPU Acceleration          | ✅          | ❌            | CPU-only on Pi                |
| 4K Video Processing       | ✅          | ⚠️            | Limited on Pi                 |
| WebRTC Streaming          | ✅          | ✅            | H.264 hardware accel on Pi    |

## Code That Works on Both Branches

### Device Management (100% Compatible)
- Device configuration
- Update checking
- Autostart management
- System information
- Network discovery
- Federation registration

### API Routes (100% Compatible)
- `/api/device/*` - All endpoints
- `/api/federation/*` - All endpoints
- `/api/discovery/*` - All endpoints

### UI (100% Compatible)
- `device-management.html` - Works on both
- Admin panel integration - Works on both

## Branch-Specific Optimizations

### Main Branch Only
```python
# Heavy ML models
if can_use_gpu():
    model = torch.load('yolov8-large.pt').cuda()
```

### Ras-Pi Branch
```python
# Lightweight alternatives
model = torch.load('yolov8-nano.pt')  # Smaller model
```

### Conditional Features
```python
from core.config import settings

if settings.DEVICE_TYPE == "raspberry-pi":
    # Use efficient processing
    process_every_nth_frame(3)
else:
    # Process every frame
    process_every_nth_frame(1)
```

## Update Workflow

### Updating Main Branch Devices

```bash
# On main branch device
curl -X POST http://localhost:8000/api/device/updates/apply?restart=true

# Device:
# 1. Checks for updates on 'main' branch
# 2. Pulls latest from origin/main
# 3. Installs dependencies
# 4. Restarts system
```

### Updating Ras-Pi Branch Devices

```bash
# On ras-pi branch device
curl -X POST http://localhost:8000/api/device/updates/apply?restart=true

# Device:
# 1. Checks for updates on 'ras-pi' branch
# 2. Pulls latest from origin/ras-pi
# 3. Installs dependencies (lighter set)
# 4. Restarts system
```

### Manual Branch Switch

If you need to move a device between branches:

```bash
# Switch Raspberry Pi to main (not recommended)
curl -X POST http://localhost:8000/api/device/branch/switch \
  -d '{"branch": "main"}'

# Or vice versa
curl -X POST http://localhost:8000/api/device/branch/switch \
  -d '{"branch": "ras-pi"}'
```

## Testing Both Branches

### Local Testing Setup

```bash
# Test main branch
git checkout main
DEVICE_TYPE=server python backend/main.py

# Test ras-pi branch
git checkout ras-pi
DEVICE_TYPE=raspberry-pi python backend/main.py
```

### Docker Testing

```dockerfile
# Dockerfile.main
FROM python:3.11
RUN git clone -b main https://github.com/your/repo.git
...

# Dockerfile.raspi
FROM arm32v7/python:3.11
RUN git clone -b ras-pi https://github.com/your/repo.git
...
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Both Branches

on: [push, pull_request]

jobs:
  test-main:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          ref: main
      - name: Test main branch
        run: |
          pip install -r requirements.txt
          pytest

  test-raspi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          ref: ras-pi
      - name: Test ras-pi branch
        run: |
          pip install -r requirements.txt
          pytest
```

## Merging Strategy

### When to Merge Main → Ras-Pi

✅ **Do Merge:**
- Bug fixes in common code
- API improvements
- UI enhancements
- Device management features
- Federation improvements
- Security patches

❌ **Don't Merge:**
- Heavy ML model additions
- GPU-specific optimizations
- High-resource features
- Desktop-only dependencies

### Example Merge Process

```bash
# 1. Start on main, make changes
git checkout main
# ... make changes ...
git commit -m "Add device management"
git push origin main

# 2. Merge to ras-pi
git checkout ras-pi
git merge main

# 3. Handle conflicts (if any)
# Edit files with <<<< markers
git add .
git commit -m "Merge device management from main"

# 4. Test on Raspberry Pi
# ... test ...

# 5. Push to ras-pi
git push origin ras-pi
```

## Best Practices

### 1. Use Feature Flags
```python
ENABLE_HEAVY_ML = os.getenv('ENABLE_HEAVY_ML', 'false') == 'true'

if ENABLE_HEAVY_ML:
    from models.advanced import AdvancedDetector
```

### 2. Conditional Imports
```python
try:
    import tensorflow as tf
    HAS_TF = True
except ImportError:
    HAS_TF = False
```

### 3. Requirements Files
```
requirements.txt          # Common dependencies
requirements-main.txt     # Main branch extras
requirements-raspi.txt    # Ras-pi specific
```

### 4. Configuration Profiles
```yaml
# config/profiles/server.yaml
ml_model: yolov8-large
processing: full
gpu_enabled: true

# config/profiles/raspi.yaml
ml_model: yolov8-nano
processing: lite
gpu_enabled: false
```

## Troubleshooting

### Device on Wrong Branch

```bash
# Check current branch
curl http://localhost:8000/api/device/branch

# Switch to correct branch
curl -X POST http://localhost:8000/api/device/branch/switch \
  -d '{"branch": "ras-pi"}'
```

### Update Conflicts

```bash
# Stash local changes
git stash

# Pull update
git pull origin ras-pi

# Reapply changes
git stash pop
```

### Incompatible Dependencies

```bash
# On Raspberry Pi, if main branch deps fail:
git checkout ras-pi
pip install -r requirements.txt  # Uses ras-pi deps
```

## Summary

The device management system is **branch-agnostic** - it works identically on both branches. The key differences are:

1. **Main Branch**: Full features, heavy ML, GPU support
2. **Ras-Pi Branch**: Optimized features, lite ML, CPU-only

Both branches:
- ✅ Share same device management code
- ✅ Use same API endpoints
- ✅ Support same federation features
- ✅ Auto-detect correct branch for updates
- ✅ Can discover each other on network
- ✅ Sync compatible workflows/configs

This allows seamless operation of mixed environments with automatic, branch-aware updates.

