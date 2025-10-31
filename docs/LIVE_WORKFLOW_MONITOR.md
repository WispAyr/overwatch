# Live Workflow Monitor - Production Operations Guide

## 🎯 Overview

The **Live Workflow Monitor** is a comprehensive production monitoring UI for managing and observing workflows in real-time. It provides operators with full visibility into workflow health, errors, performance metrics, and control capabilities.

## 📊 Features

### 1. **Real-Time Status Dashboard**
- ✅ **Running Workflows** - Live count of active workflows
- ✅ **Health Status** - Number of healthy workflows (no errors)
- ✅ **Warnings** - Count of workflows with warnings
- ✅ **Errors** - Critical error count across all workflows
- ✅ **Detections/min** - Total detection rate across system

### 2. **Workflow Cards**
Each workflow displays:
- **Status Indicator** - ● Green (running), ⚠️ Red (error), ○ Gray (stopped)
- **Site Assignment** - Shows which site the workflow belongs to
- **Master Badge** - ★ Purple badge for master templates
- **Real-Time Metrics**:
  - Current state (running/stopped/error)
  - Uptime (how long running)
  - FPS (frames per second processing)
  - Total detections since start
  - Error count
- **Latest Error Display** - Shows most recent error with timestamp
- **Control Buttons**:
  - ▶️ **Start** - Start stopped workflow
  - ⏹️ **Stop** - Stop running workflow
  - 📊 **Details** - Open detailed view
  - ✏️ **Edit** - Open in workflow builder

### 3. **Filters & Search**
- **Status Filter** - All / Running Only / Errors Only / Stopped
- **Site Filter** - Filter by specific site
- **Search** - Find workflows by name
- **Auto-refresh Toggle** - Enable/disable live updates (5s interval)

### 4. **Error Log Viewer**
- **Real-Time Log Stream** - Live error and warning messages
- **Timestamps** - Precise time for each entry
- **Color-Coded Levels**:
  - 🔴 Red = Error
  - 🟡 Yellow = Warning
  - 🔵 Blue = Info
- **Export** - Download error log as .log file
- **Clear** - Reset error log

### 5. **System Health Metrics**
Three real-time graphs showing last 10 samples:
- **CPU Usage** - System CPU percentage
- **Memory Usage** - RAM utilization
- **Frame Processing** - Average FPS across all workflows

Color-coded bars:
- 🟢 Green = < 50% (healthy)
- 🟡 Yellow = 50-80% (warning)
- 🔴 Red = > 80% (critical)

### 6. **Detailed Workflow View (Modal)**
Click **📊 Details** on any workflow to see:

**Status Section:**
- Current state
- Uptime (hours/minutes)
- FPS
- Total detections

**Live Logs:**
- Real-time log streaming from workflow
- Shows initialization, processing, errors
- Auto-scrolls to latest

**Node Performance:**
- Per-node metrics
- Processing time
- Frame counts
- Error rates per node

**Control Actions:**
- 🔄 **Restart** - Stop and restart workflow
- ⏹️ **Stop** - Stop workflow

---

## 🚀 How to Use

### Accessing the Monitor

1. Open Dashboard: **http://localhost:7002**
2. Click **"Workflows"** in navigation
3. Monitor loads automatically

### Monitoring Running Workflows

1. **View Overview** - Check stats at top (Running, Healthy, Errors, etc.)
2. **Scan Workflow Cards** - Look for status indicators:
   - ● Green = Healthy
   - ⚠️ Red = Has errors
   - ○ Gray = Stopped
3. **Check Metrics** - Review FPS, detections, uptime on each card

### Starting a Workflow

1. Find stopped workflow (gray ○ indicator)
2. Click **▶️ Start** button
3. Watch status change to ● green
4. Monitor metrics start updating

### Stopping a Workflow

1. Find running workflow (green ● indicator)
2. Click **⏹️ Stop** button
3. Confirm if needed
4. Status changes to ○ gray

### Investigating Errors

1. **Error Counter** - Check red stat at top
2. **Workflow Cards** - Look for ⚠️ red indicator
3. **Latest Error** - Read error message on card
4. **Detailed View**:
   - Click **📊 Details**
   - Review live logs
   - Check node metrics
   - Identify failing node

### Using Filters

**Status Filter:**
```
All Workflows    → See everything
Running Only     → Focus on active workflows
Errors Only      → Troubleshoot problems
Stopped          → See inactive workflows
```

**Site Filter:**
```
All Sites        → System-wide view
Specific Site    → Focus on one location
```

**Search:**
```
Type workflow name → Instant filter
```

### Reviewing Error Log

1. Scroll to **"Recent Errors & Warnings"** section
2. Review timestamped entries
3. Color indicates severity:
   - Red = Error
   - Yellow = Warning
   - Blue = Info
4. **Export** to save for analysis
5. **Clear** to reset log

### Monitoring System Health

1. Check **CPU/Memory/FPS** graphs
2. Look for color patterns:
   - Mostly green = Healthy
   - Yellow bars = Under load
   - Red bars = Potential issue
3. Current values shown below each graph

---

## 🔔 WebSocket Live Updates

The monitor connects via WebSocket for real-time updates:

### Message Types Handled
- `workflow_status` - Workflow state changes
- `workflow_error` - New errors
- `detection_data` - Detection events
- `system_metrics` - CPU/Memory/FPS updates

### Connection Status
- **Connected** - Auto-refreshes every 5s
- **Disconnected** - Auto-reconnects after 5s
- **Error** - Logged to error viewer

---

## 📈 Metrics Explained

### Workflow Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Uptime** | How long workflow has been running | N/A |
| **FPS** | Frames processed per second | 5-30 FPS |
| **Detections** | Total detections since start | Varies |
| **Errors** | Error count | 0 |

### System Metrics

| Metric | Description | Healthy Range |
|--------|-------------|---------------|
| **CPU %** | System CPU usage | < 70% |
| **Memory %** | RAM utilization | < 80% |
| **FPS** | Average processing rate | > 5 FPS |

---

## 🚨 Common Issues & Solutions

### Workflow Won't Start
**Symptoms:** Click Start, but workflow stays stopped

**Solutions:**
1. Check error log for initialization errors
2. Verify camera stream is available
3. Confirm AI model is loaded
4. Check site assignment if using site-specific cameras

### Low FPS
**Symptoms:** FPS < 5, processing slow

**Solutions:**
1. Check CPU usage (should be < 80%)
2. Reduce number of running workflows
3. Lower detection confidence threshold
4. Use lighter AI model (n vs. m vs. l)

### Frequent Errors
**Symptoms:** Error count keeps increasing

**Solutions:**
1. Open Details → Review live logs
2. Identify failing node
3. Common causes:
   - Camera stream disconnected
   - Model configuration invalid
   - Zone polygon malformed
   - Action endpoint unreachable

### Workflow Stuck
**Symptoms:** Running but no detections, FPS = 0

**Solutions:**
1. Click 🔄 **Restart** in Details modal
2. Check camera stream status
3. Verify workflow has required nodes connected

---

## 🎬 Production Workflows

### Daily Operations Checklist

**Morning Startup:**
1. ☐ Check "Healthy" count = "Running" count
2. ☐ Review error log for overnight issues
3. ☐ Verify all critical workflows running
4. ☐ Check system metrics (CPU/Memory)

**During Day:**
1. ☐ Monitor error counter every hour
2. ☐ Investigate any new errors immediately
3. ☐ Watch detection rates for anomalies

**Evening Shutdown:**
1. ☐ Export error log for analysis
2. ☐ Stop non-essential workflows
3. ☐ Note any recurring issues

### Alert Thresholds

Set up monitoring alerts for:
- **Errors > 0** - Immediate investigation
- **CPU > 80%** - Performance degradation
- **Memory > 85%** - System instability risk
- **FPS < 3** - Processing too slow
- **Workflow stopped unexpectedly** - Critical issue

---

## 🔧 Advanced Features

### Workflow Restart Strategy

**When to Restart:**
- Errors accumulating
- FPS degrading over time
- Memory leak suspected
- Configuration changes applied

**How to Restart:**
```
Option 1: Details Modal
  Click 📊 Details → 🔄 Restart

Option 2: Stop/Start
  Click ⏹️ Stop → Wait 2s → Click ▶️ Start
```

### Error Log Analysis

**Export and Analyze:**
```bash
# Export log
Click Export → Save workflow-errors-{timestamp}.log

# Analyze patterns
grep "ERROR" workflow-errors-*.log | sort | uniq -c
```

**Common Error Patterns:**
```
Camera disconnected      → Check network
Model timeout            → Reduce FPS or use lighter model
Zone validation failed   → Fix polygon coordinates
Action endpoint 500      → Check external service
```

### Performance Tuning

**High CPU Usage:**
1. Reduce concurrent workflows
2. Lower FPS (10 → 5)
3. Use YOLOv8n instead of m/l
4. Increase frame skip

**High Memory:**
1. Restart long-running workflows
2. Reduce max detections per frame
3. Check for memory leaks in custom actions

**Low FPS:**
1. Check CPU usage
2. Verify stream quality setting
3. Review node complexity
4. Consider GPU acceleration

---

## 📱 Mobile/Remote Access

The monitor is responsive and works on:
- **Desktop** - Full feature set
- **Tablet** - Optimized layout
- **Mobile** - Essential controls

**Remote Access:**
```
http://your-server-ip:7002
```

Ensure firewall allows port 7002.

---

## 🔐 Security Considerations

### Access Control (Planned v2.1)
- Role-based permissions
- Audit logging
- Session management

### Current Setup
- Dashboard is publicly accessible on local network
- Implement reverse proxy with authentication for production
- Use HTTPS for remote access

---

## 🎯 Quick Reference

### Keyboard Shortcuts
- `F5` - Refresh monitor
- `Ctrl/Cmd + F` - Focus search
- `Esc` - Close detail modal

### Color Legend
- 🟢 Green - Healthy/Running
- 🟡 Yellow - Warning
- 🔴 Red - Error/Critical
- ⚪ Gray - Stopped/Inactive
- 🟣 Purple - Master Template

### Status Icons
- ● - Running
- ○ - Stopped
- ⚠️ - Error
- ★ - Master

---

## 📊 API Endpoints Used

```
GET  /api/workflow-builder              - List workflows
GET  /api/workflow-builder/{id}/status  - Get workflow status
POST /api/workflow-builder/execute      - Start workflow
POST /api/workflow-builder/{id}/stop    - Stop workflow
GET  /api/system/metrics                - System metrics
WS   /api/ws                            - WebSocket live updates
```

---

## 🎉 Summary

The Live Workflow Monitor provides:
- ✅ Complete visibility into production workflows
- ✅ Real-time status and metrics
- ✅ Error tracking and logging
- ✅ Start/Stop/Restart controls
- ✅ System health monitoring
- ✅ Detailed per-workflow analysis
- ✅ WebSocket live updates

**Perfect for:**
- Production operations
- Troubleshooting
- Performance monitoring
- Capacity planning
- SLA compliance

---

*Last updated: October 30, 2025*  
*Version: 1.0.0*  
*For: Overwatch Live Monitoring Dashboard*


