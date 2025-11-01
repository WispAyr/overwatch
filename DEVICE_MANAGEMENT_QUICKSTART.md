# Device Management & Federation Quick Start

## 🚀 What's New

You now have powerful device management and federation capabilities that allow you to:

1. **Update devices from GitHub** - Pull latest changes for your device type automatically
2. **Auto-discover devices** - Find other Overwatch instances on your network
3. **Sync configurations** - Keep workflows and settings synchronized across devices
4. **Manage autostart** - Configure devices to start on boot
5. **Multi-branch support** - Automatic branch selection (main/ras-pi)

## ⚡ Quick Start (5 Minutes)

### 1. Install New Dependency

```bash
cd /Users/ewanrichardson/Development/overwatch
pip install zeroconf>=0.132.0
```

### 2. Enable Features

Add to your `.env` file or export:

```bash
# Enable discovery (find other devices on network)
ENABLE_DISCOVERY=true

# Enable federation (if connecting to other nodes)
ENABLE_FEDERATION=true

# Set device type (auto-detected by default)
DEVICE_TYPE=server  # or raspberry-pi
```

### 3. Restart Overwatch

```bash
./restart-all.sh
```

### 4. Access Device Management

Open in your browser:
```
http://localhost:8000/device-management.html
```

Or via the Admin panel → Device Management tab

## 🎯 Common Tasks

### Check for Updates

**Via UI:**
1. Open http://localhost:8000/device-management.html
2. Click "Check for Updates"
3. Click "Apply Update" if available

**Via API:**
```bash
# Check
curl http://localhost:8000/api/device/updates/check

# Apply
curl -X POST "http://localhost:8000/api/device/updates/apply?restart=true"
```

### Enable Autostart

**Via UI:**
1. Open device management page
2. Click "Toggle Autostart"

**Via API:**
```bash
curl -X POST http://localhost:8000/api/device/autostart/enable
```

### Discover Network Devices

**Via UI:**
1. Open device management page
2. Click "Scan Network"
3. View discovered devices list

**Via API:**
```bash
curl -X POST http://localhost:8000/api/device/discovery/scan
```

### View Federated Nodes

**Via UI:**
1. Open device management page
2. Scroll to "Federated Nodes" section
3. See all connected nodes with status

**Via API:**
```bash
curl http://localhost:8000/api/federation/cluster/status
```

### Configure Sync Settings

**Via UI:**
1. Open device management page
2. Edit checkboxes in "Device Configuration" section:
   - Enable Automatic Sync
   - Sync Workflows
   - Sync Cameras
3. Click "Save Configuration"

**Via API:**
```bash
curl -X PATCH http://localhost:8000/api/device/config \
  -H "Content-Type: application/json" \
  -d '{
    "auto_sync_enabled": true,
    "sync_workflows": true,
    "sync_cameras": true
  }'
```

## 🔧 Configuration Examples

### Single Server Setup

```bash
# .env
DEVICE_TYPE=server
ENABLE_DISCOVERY=false
ENABLE_FEDERATION=false
```

No additional config needed - just run as before!

### Central + Edge Nodes

**Central Server:**
```bash
# .env
DEVICE_TYPE=server
NODE_TYPE=central
NODE_ID=overwatch-central
ENABLE_FEDERATION=true
ENABLE_DISCOVERY=true
```

**Edge Node (Raspberry Pi):**
```bash
# .env
DEVICE_TYPE=raspberry-pi
NODE_TYPE=edge
NODE_ID=overwatch-pi-1
CENTRAL_SERVER_URL=http://192.168.1.100:8000
ENABLE_FEDERATION=true
ENABLE_DISCOVERY=true
```

### Automatic Network Discovery

Just enable discovery on all devices:

```bash
# .env (all devices)
ENABLE_DISCOVERY=true
ENABLE_FEDERATION=true
```

Devices will automatically find each other!

## 📱 UI Features

### Device Management Page

Access at: `http://localhost:8000/device-management.html`

**Sections:**
1. **Local Device** - Your device info and update controls
2. **Device Configuration** - Settings and sync options
3. **Discovered Devices** - Other Overwatch instances on network
4. **Federated Nodes** - Connected nodes with status

**Features:**
- ✅ Real-time status updates
- ✅ One-click updates
- ✅ Visual device cards
- ✅ Live federation monitoring
- ✅ Configuration management
- ✅ System restart controls

## 🌐 Branch Strategy

### Automatic Branch Selection

The system automatically uses the correct branch:

| Device Type    | Branch Used | When to Use           |
|---------------|-------------|-----------------------|
| `server`      | `main`      | Full servers          |
| `raspberry-pi`| `ras-pi`    | Raspberry Pi devices  |
| `edge`        | `main`      | Edge compute devices  |

### Check Your Branch

```bash
curl http://localhost:8000/api/device/branch
```

Response:
```json
{
  "current_branch": "main",
  "recommended_branch": "main",
  "is_recommended": true
}
```

### Switch Branches

```bash
curl -X POST http://localhost:8000/api/device/branch/switch \
  -H "Content-Type: application/json" \
  -d '{"branch": "ras-pi"}'
```

## 🔍 Troubleshooting

### Discovery Not Working

1. Check zeroconf is installed:
   ```bash
   pip show zeroconf
   ```

2. Allow mDNS through firewall:
   ```bash
   sudo ufw allow 5353/udp
   ```

3. Verify discovery is enabled:
   ```bash
   curl http://localhost:8000/api/device/discovery/status
   ```

### Updates Failing

1. Check git status:
   ```bash
   cd /Users/ewanrichardson/Development/overwatch
   git status
   ```

2. Stash uncommitted changes:
   ```bash
   git stash
   ```

3. Try update again

### Autostart Not Working

**Check systemd:**
```bash
sudo systemctl status overwatch
sudo systemctl enable overwatch
```

**Check cron:**
```bash
crontab -l
```

## 📊 Monitoring

### Check System Status

```bash
curl http://localhost:8000/api/device/info
```

### Monitor Federation

```bash
curl http://localhost:8000/api/federation/cluster/status
```

### View Logs

```bash
tail -f logs/overwatch.log | grep -E 'device|federation|discovery'
```

## 🎓 Learn More

- **Full Guide**: `DEVICE_FEDERATION_GUIDE.md`
- **Branch Strategy**: `BRANCH_DEPLOYMENT_STRATEGY.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY_DEVICE_FEDERATION.md`
- **API Docs**: `http://localhost:8000/docs`

## 💡 Pro Tips

1. **Enable Auto-Sync** - Keeps all nodes in sync automatically
2. **Use Discovery** - Simplifies network management
3. **Monitor Updates** - Check weekly for new features
4. **Test on Edge First** - Apply updates to edge nodes before central
5. **Backup Config** - Save `config/device.json` before major updates

## 🚨 Important Notes

- **Updates restart the system** - Schedule during low-usage times
- **Credentials don't sync** - Camera passwords stay local
- **Discovery is local network only** - Uses mDNS
- **Branch switching requires restart** - Plan accordingly

## ✅ Checklist

First-time setup:
- [ ] Install zeroconf: `pip install zeroconf>=0.132.0`
- [ ] Set DEVICE_TYPE in .env
- [ ] Enable ENABLE_DISCOVERY if using network discovery
- [ ] Enable ENABLE_FEDERATION if using federation
- [ ] Restart Overwatch
- [ ] Access device management UI
- [ ] Check for updates
- [ ] Configure sync settings
- [ ] Scan for network devices (if applicable)

## 🆘 Support

If you encounter issues:

1. Check logs: `logs/overwatch.log`
2. Verify config: `curl http://localhost:8000/api/device/config`
3. Test connectivity: `curl http://localhost:8000/api/device/info`
4. Review documentation files listed above

---

**You're all set!** The device management system is now integrated and ready to use. 🎉

