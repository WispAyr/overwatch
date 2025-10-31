# GitHub Deployment Guide

## Pre-Push Checklist

### ✅ Ready to Push

This project is ready to be pushed to GitHub. Here's what's in place:

- ✅ **LICENSE file** - MIT License
- ✅ **Comprehensive README** - Full documentation
- ✅ **`.gitignore`** - Prevents sensitive files from being committed
- ✅ **Example configs** - All sensitive configs use `.example` suffix
- ✅ **Documentation** - Complete docs in `/docs` directory
- ✅ **Installation script** - `install.sh` for easy setup
- ✅ **Dependencies documented** - `requirements.txt` and `package.json`
- ✅ **No hardcoded secrets** - All credentials use environment variables or config files

### ⚠️ Before Pushing

1. **Remove any local database files** (already in `.gitignore`):
   ```bash
   # These are automatically ignored, but verify:
   ls -la *.db
   ls -la data/
   ```

2. **Remove any log files with sensitive info** (already in `.gitignore`):
   ```bash
   # These are automatically ignored:
   ls -la logs/
   ```

3. **Verify no API keys in code**:
   ```bash
   # Search for potential secrets
   grep -r "password\|api_key\|secret" config/*.yaml
   # Should only find .example files
   ```

## Initial GitHub Setup

### 1. Create GitHub Repository

Go to https://github.com/new and create a new repository:

```
Repository name: overwatch
Description: AI-Powered Security Camera Monitoring System with Visual Workflows
Visibility: Public or Private (your choice)
⬜ Initialize with README (we already have one)
⬜ Add .gitignore (we already have one)
⬜ Add license (we already have one)
```

### 2. Initialize Git (if not already done)

```bash
cd /Users/ewanrichardson/Development/overwatch

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Overwatch AI security camera monitoring system

- 38+ AI models (YOLOv8, Face Recognition, ALPR, Audio)
- Visual workflow builder with React Flow
- Federation support for distributed deployments
- Alarm management with SLA tracking
- Rules engine with YAML DSL
- Admin panel for organization/site/camera management
- Real-time WebSocket updates
- Raspberry Pi 5 compatible
"
```

### 3. Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/overwatch.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 4. Set Up GitHub Actions (Optional)

Create `.github/workflows/tests.yml` for automated testing:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

## Deployment Strategies

### Strategy 1: Git Clone on Raspberry Pi

**Best for**: Testing and edge nodes

```bash
# On Raspberry Pi
cd ~
git clone https://github.com/YOUR_USERNAME/overwatch.git
cd overwatch
./install.sh
```

**Pros**:
- Simple and straightforward
- Easy to update with `git pull`
- Full control over configuration

**Cons**:
- Manual setup on each node
- Requires git on target device

### Strategy 2: GitHub Releases with Docker (Future)

**Best for**: Production deployments

Create Dockerfile (future enhancement):

```dockerfile
# Future: Docker deployment
FROM python:3.10-slim
# ... (not implemented yet, manual deployment recommended)
```

### Strategy 3: Federation with Central GitHub Repo

**Best for**: Multiple test nodes

**Architecture**:
```
GitHub Repo (Source of Truth)
    ↓
Central Node (pulls from GitHub)
    ↓ (Federation)
Edge Nodes (Raspberry Pi) - pull from Central or GitHub
```

**Setup**:

1. **Central Node** (your main server):
   ```bash
   git clone https://github.com/YOUR_USERNAME/overwatch.git
   cd overwatch
   ./install.sh
   
   # Configure as central node
   cat > config/federation.yaml << EOF
   node:
     id: "central-001"
     name: "Central Control"
     role: "central"
     zerotier_network: "YOUR_NETWORK_ID"
   EOF
   ```

2. **Edge Nodes** (Raspberry Pi):
   ```bash
   git clone https://github.com/YOUR_USERNAME/overwatch.git
   cd overwatch
   ./install.sh
   
   # Configure as edge node
   cat > config/federation.yaml << EOF
   node:
     id: "edge-pi-001"
     name: "Test Node Pi 1"
     role: "edge"
     central_server: "http://CENTRAL_IP:8000"
     zerotier_network: "YOUR_NETWORK_ID"
   EOF
   ```

## Configuration Management

### Environment-Specific Configs

**Don't commit**:
- `config/cameras.yaml`
- `config/workflows.yaml`
- `config/hierarchy.yaml`
- `config/federation.yaml`

**Do commit**:
- `config/cameras.example.yaml`
- `config/workflows.example.yaml`
- `config/hierarchy.example.yaml`
- `config/federation.example.yaml`

### Setup Per-Node Configuration

On each deployment node:

```bash
# Copy examples
cp config/hierarchy.example.yaml config/hierarchy.yaml
cp config/cameras.example.yaml config/cameras.yaml
cp config/workflows.example.yaml config/workflows.yaml

# Edit for your environment
nano config/hierarchy.yaml
nano config/cameras.yaml
```

### Environment Variables

Create `.env` file (not committed):

```bash
cat > .env << EOF
# Device
DEVICE=cpu  # or 'cuda' for GPU nodes

# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=$(openssl rand -hex 32)

# Performance
MAX_CONCURRENT_STREAMS=2  # Adjust per node capability
LOG_LEVEL=INFO

# Alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=alerts@example.com
EOF
```

## Testing Federation Between Nodes

### Setup ZeroTier Network

1. **Create ZeroTier Network**:
   - Go to https://my.zerotier.com
   - Create new network
   - Note the Network ID: `a1b2c3d4e5f6g7h8`

2. **Install ZeroTier on all nodes**:
   ```bash
   # On each node (Pi and central)
   curl -s https://install.zerotier.com | sudo bash
   sudo zerotier-cli join a1b2c3d4e5f6g7h8
   ```

3. **Authorize nodes** in ZeroTier web console

4. **Update federation configs**:
   ```yaml
   # config/federation.yaml on all nodes
   node:
     zerotier_network: "a1b2c3d4e5f6g7h8"
   ```

### Test Federation

1. **Start Central Node**:
   ```bash
   # On central server
   ./run.sh
   ```

2. **Start Edge Nodes**:
   ```bash
   # On each Raspberry Pi
   ./run.sh
   ```

3. **Verify Connection**:
   ```bash
   # From any node, check federation status
   curl http://localhost:8000/api/federation/nodes
   ```

4. **Check Dashboard**:
   - Open: http://localhost:7002
   - Navigate to "Federation" panel
   - Should see all connected nodes

## Update Workflow

### Updating Deployed Nodes

```bash
# SSH into each node
ssh pi@raspberry-pi.local

# Pull updates
cd ~/overwatch
git pull

# Restart service
sudo systemctl restart overwatch

# Or manual restart
pkill -f "python backend/main.py"
./run.sh
```

### Automated Updates (Advanced)

Create update script on each node:

```bash
cat > ~/update_overwatch.sh << 'EOF'
#!/bin/bash
cd ~/overwatch
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart overwatch
echo "Update complete"
EOF

chmod +x ~/update_overwatch.sh

# Run updates
./update_overwatch.sh
```

## Branch Strategy

### Recommended Branches

```
main       - Stable production code
develop    - Active development
feature/*  - New features
hotfix/*   - Critical fixes
pi/*       - Pi-specific optimizations
```

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-detection-model

# Make changes
git add .
git commit -m "Add smoke detection model"

# Push to GitHub
git push origin feature/new-detection-model

# Create Pull Request on GitHub
# Merge after testing
```

## CI/CD Pipeline (Future)

### GitHub Actions for Testing

```yaml
# .github/workflows/deploy-to-pi.yml
name: Deploy to Raspberry Pi

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Pi Nodes
        run: |
          # SSH into each Pi and update
          ssh pi@pi-node-1 'cd overwatch && git pull && systemctl restart overwatch'
          ssh pi@pi-node-2 'cd overwatch && git pull && systemctl restart overwatch'
```

## Monitoring Deployments

### Health Checks

```bash
# Check all nodes
for node in pi-1 pi-2 central; do
  echo "Checking $node..."
  curl http://$node:8000/health
done
```

### Log Aggregation

Use Grafana Loki or similar for centralized logging:

```bash
# Future: Send logs to central server
# Currently: SSH to each node and check logs
ssh pi@node-1 'tail -f overwatch/logs/overwatch.log'
```

## Security Best Practices

### 1. API Security

```bash
# Generate strong secret
export API_SECRET_KEY=$(openssl rand -hex 32)

# Add to .env
echo "API_SECRET_KEY=$API_SECRET_KEY" >> .env
```

### 2. Network Security

```bash
# Use ZeroTier for private network
# Don't expose ports directly to internet

# If exposing API, use reverse proxy with HTTPS
sudo apt install nginx certbot
# Configure Nginx with SSL
```

### 3. GitHub Secrets

For GitHub Actions:
- Settings → Secrets → Add:
  - `PI_SSH_KEY` - SSH private key for Pi access
  - `PI_HOSTS` - List of Pi IP addresses

## Troubleshooting

### Port Already in Use

The system automatically frees ports on startup (port 8000), but verify:

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill if needed (automatic in backend/main.py)
```

### Git Push Errors

```bash
# If repository too large
git gc --aggressive --prune=now

# If files ignored but still tracked
git rm --cached logs/*.log
git rm --cached data/*.db
```

### Merge Conflicts

```bash
# Pull latest
git pull origin main

# If conflicts, resolve manually
git status
# Edit conflicting files
git add .
git commit -m "Resolve merge conflicts"
git push
```

## Repository Structure

```
overwatch/
├── .github/               # GitHub Actions (optional)
├── .gitignore            # ✅ Prevent committing sensitive files
├── LICENSE               # ✅ MIT License
├── README.md             # ✅ Main documentation
├── RASPBERRY_PI_DEPLOYMENT.md  # ✅ Pi-specific guide
├── GITHUB_DEPLOYMENT.md  # ✅ This file
├── requirements.txt      # ✅ Python dependencies
├── install.sh           # ✅ Installation script
├── run.sh               # ✅ Start script
├── backend/             # Python FastAPI backend
├── frontend/            # HTML/CSS/JS dashboard
├── workflow-builder/    # React workflow editor
├── config/*.example.yaml # ✅ Config templates
├── docs/                # ✅ Comprehensive documentation
└── tests/               # Test suite
```

## Next Steps After Pushing

1. **Add Topics** on GitHub:
   - ai
   - computer-vision
   - security-camera
   - yolov8
   - workflow-engine
   - raspberry-pi
   - rtsp
   - surveillance

2. **Create Releases**:
   - Tag stable versions: `git tag v1.0.0`
   - Push tags: `git push --tags`

3. **Write CONTRIBUTING.md** (future):
   - Guidelines for contributors
   - Code style
   - Testing requirements

4. **Add Badges to README**:
   ```markdown
   ![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
   ![License](https://img.shields.io/badge/license-MIT-green.svg)
   ![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20raspberry--pi-lightgrey.svg)
   ```

## Support and Community

After pushing to GitHub:

- Enable **Issues** for bug reports
- Enable **Discussions** for Q&A
- Add **Wiki** for advanced guides
- Consider Discord/Slack for community

## Summary

✅ **Ready to Push**: YES

**Command to Push**:
```bash
cd /Users/ewanrichardson/Development/overwatch

# If not already initialized
git init
git add .
git commit -m "Initial commit: Overwatch AI security monitoring system"

# Add your GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/overwatch.git

# Push
git branch -M main
git push -u origin main
```

**Federation Testing**:
```bash
# Clone to multiple Pi nodes
ssh pi@node-1 'git clone https://github.com/YOUR_USERNAME/overwatch.git'
ssh pi@node-2 'git clone https://github.com/YOUR_USERNAME/overwatch.git'

# Configure each as edge node
# Start all nodes
# Test federation via API and dashboard
```

**Project is production-ready for:**
- ✅ GitHub hosting
- ✅ Raspberry Pi 5 deployment
- ✅ Federation testing
- ✅ Multi-node deployments
- ✅ Edge computing scenarios

**Time to Deploy**: 1-2 hours per node (including OS setup)

