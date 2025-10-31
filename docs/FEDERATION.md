# Federation Guide

## Overview

Overwatch supports federation, allowing multiple servers to work together in a distributed architecture. This is ideal for edge processing scenarios where video processing happens locally, with results aggregated centrally.

## Architecture

### Deployment Models

#### 1. Central-Only (Default)
Single server deployment with all cameras and processing.

```
┌─────────────────┐
│  Central Server │
│   - Cameras     │
│   - Processing  │
│   - Storage     │
└─────────────────┘
```

#### 2. Central + Edge (Federated)
Central server with edge nodes for distributed processing.

```
┌─────────────────┐
│  Central Server │◄────┐
│   - Aggregation │     │
│   - Storage     │     │ Events
│   - Dashboard   │     │
└─────────────────┘     │
                        │
        ┌───────────────┴─────────────┐
        │                             │
┌───────▼──────┐              ┌──────▼───────┐
│  Edge Node 1 │              │ Edge Node 2  │
│  - Cameras   │              │  - Cameras   │
│  - AI Models │              │  - AI Models │
│  - Processing│              │  - Processing│
└──────────────┘              └──────────────┘
```

#### 3. Multi-Site Federation
Multiple sites with local edge processing.

```
                ┌──────────────────┐
                │  Central Server  │
                │   HQ Dashboard   │
                └────────┬─────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼───────┐
│   Site A     │  │   Site B    │  │  Mobile     │
│   Edge Node  │  │  Edge Node  │  │  Unit       │
│  - 8 Cameras │  │ - 12 Cameras│  │ - 4 Cameras │
└──────────────┘  └─────────────┘  └─────────────┘
```

## Configuration

### Central Server Setup

1. Configure as central node in `.env`:
```bash
ENABLE_FEDERATION=true
NODE_ID=central-hq
NODE_TYPE=central
NODE_URL=http://central-server.domain.com:8000
```

2. Start the server:
```bash
python backend/main.py
```

The central server will:
- Accept edge node registrations
- Receive events from edge nodes
- Aggregate data across all nodes
- Provide unified dashboard

### Edge Node Setup

1. Configure as edge node in `.env`:
```bash
ENABLE_FEDERATION=true
NODE_ID=edge-site-a
NODE_TYPE=edge
NODE_URL=http://edge-node-a.local:8000
CENTRAL_SERVER_URL=http://central-server.domain.com:8000
```

2. Configure local cameras in `config/hierarchy.yaml`:
```yaml
organizations:
  - id: org-001
    name: "My Organization"
    sites:
      - id: site-a
        name: "Site A"
        sublocations:
          - id: subloc-entrance
            name: "Entrance"
            cameras:
              - id: cam-001
                name: "Entrance Camera"
                rtsp_url: "rtsp://local-camera:554/stream"
                workflows:
                  - people_detection
```

3. Start the edge node:
```bash
python backend/main.py
```

The edge node will:
- Register with central server
- Process video locally
- Forward events to central
- Sync hierarchy from central
- Send periodic heartbeats

## Federation API

### Register Node
```http
POST /api/federation/register
Content-Type: application/json

{
  "node_id": "edge-site-a",
  "node_type": "edge",
  "url": "http://edge-node:8000",
  "metadata": {
    "location": "Site A",
    "capabilities": ["stream_processing", "ai_inference"]
  }
}
```

### Send Heartbeat
```http
POST /api/federation/heartbeat
Content-Type: application/json

{
  "node_id": "edge-site-a",
  "timestamp": "2025-10-30T10:00:00Z",
  "status": "online"
}
```

### Forward Event
```http
POST /api/federation/events
Content-Type: application/json

{
  "event_id": "evt-001",
  "source_node": "edge-site-a",
  "camera_id": "cam-001",
  "workflow_id": "people_detection",
  "timestamp": "2025-10-30T10:00:00Z",
  "severity": "info",
  "detections": [...]
}
```

### Get Cluster Status
```http
GET /api/federation/cluster/status
```

Response:
```json
{
  "local_node": {
    "id": "central-hq",
    "type": "central",
    "status": "online"
  },
  "federated_nodes": [
    {
      "id": "edge-site-a",
      "type": "edge",
      "url": "http://edge-node-a:8000",
      "status": "online",
      "last_seen": "2025-10-30T10:00:00Z"
    }
  ]
}
```

## Use Cases

### 1. Edge Processing at Remote Sites
Deploy edge nodes at remote locations with local cameras:
- Reduce bandwidth (only send events, not video)
- Lower latency (local AI processing)
- Continue operating if connection to central is lost
- Aggregate results centrally

### 2. Mobile Deployments
Deploy portable edge units for temporary events:
- Quick setup at event locations
- Autonomous operation
- Forward events to central when connected
- Store locally when offline

### 3. Multi-Tenant Deployments
Separate edge nodes per organization/client:
- Isolated processing per tenant
- Centralized monitoring
- Shared AI models
- Individual billing/reporting

### 4. Hybrid Cloud-Edge
Process light workloads on edge, heavy on cloud:
- Simple detection (people counting) on edge
- Complex analysis (behavior, activities) on cloud
- Smart routing based on detection triggers
- Cost optimization

## Event Flow

### Edge → Central
1. Edge node detects event
2. Stores event locally
3. Forwards event to central via `/api/federation/events`
4. Central server stores and broadcasts to dashboard

### Central → Edge
1. Central receives configuration update
2. Edge nodes sync hierarchy via `/api/federation/sync/hierarchy`
3. Edge nodes update local cameras/workflows
4. Continue processing with new config

## Network Requirements

### Bandwidth
- **Heartbeat**: ~1 KB every 30 seconds
- **Event**: ~5-50 KB per event (depends on detections)
- **Hierarchy Sync**: ~10-100 KB (occasional)

### Ports
- **8000**: API and federation endpoints
- **7001**: Dashboard (optional on edge)
- **9993**: ZeroTier UDP (if using ZeroTier)

### Firewall Rules

**With ZeroTier (Recommended - Auto-discovery & Fallback)**:
- **Outbound UDP**: Port 9993 (ZeroTier only)
- **No inbound rules needed!**
- All Overwatch traffic goes through encrypted ZeroTier tunnel
- **NEW**: Automatic mesh IP discovery from central server
- **NEW**: Health checks with fallback to public URL if mesh fails

**Without ZeroTier**:
Edge nodes must be able to:
- **Outbound HTTPS** to central server
- **Inbound** from local cameras (RTSP)

Central server must accept:
- **Inbound HTTPS** from edge nodes

## High Availability

### Edge Node Failure
- Central marks node as offline after missed heartbeats
- Dashboard shows node status
- Events from other nodes continue normally

### Central Server Failure
- Edge nodes continue local processing
- Events queued locally (TODO: implement queue)
- Automatic reconnection when central recovers

### Network Partition
- Edge nodes operate autonomously
- Reconnect and sync when connection restored

## Monitoring

### Check Federation Status
```bash
curl http://central-server:8000/api/federation/cluster/status
```

**NEW**: Response now includes overlay network status and mesh connectivity:
```json
{
  "local_node": {...},
  "federated_nodes": [...],
  "overlay": {
    "enabled": true,
    "provider": "zerotier",
    "online": true,
    "peer_count": 3,
    "member_count": 4
  },
  "mesh_connectivity": {
    "mesh_url": "http://10.147.0.1:8000",
    "public_url": "http://public-ip:8000",
    "using_mesh": true
  }
}
```

### System Metrics
```bash
curl http://central-server:8000/api/system/metrics
```

**NEW**: Now includes overlay network metrics:
- Peer count (active P2P connections)
- Member count (total authorized nodes)
- Health status

### View Federated Events
Events from edge nodes are marked in metadata:
```json
{
  "event_id": "evt-001",
  "metadata": {
    "source_node": "edge-site-a",
    "federated": true
  }
}
```

### Dashboard Monitoring (NEW)
- Federation tab shows ZeroTier status with health indicators
- Peer and member counts displayed
- Mesh connectivity status with automatic fallback indication
- Setup wizard for easy network configuration
- One-click member authorization

### Logs
```bash
# Central server
tail -f logs/overwatch.log | grep federation

# Edge node
tail -f logs/overwatch.log | grep federation

# Look for mesh transitions
tail -f logs/overwatch.log | grep "Switched to\|Fell back to"
```

## Security

### Authentication (Implemented)
- **NEW**: Authentication middleware for ZeroTier and federation routes
- Enable with `ENABLE_AUTH=true` in `.env`
- JWT tokens for federation API (placeholder - implement full JWT validation)
- API keys via `X-API-Key` header
- Admin role required for ZeroTier member management
- Service credentials required for federation register/heartbeat/events

### Encryption
- Use HTTPS for all federation traffic
- ZeroTier provides automatic AES-256 encryption for mesh traffic
- Encrypt events in transit
- Secure camera credentials
- **NEW**: Automatic secret redaction in logs

## Troubleshooting

### Edge Node Not Registering
1. Check `CENTRAL_SERVER_URL` is correct
2. Verify network connectivity: `curl http://central-server:8000/health`
3. Check firewall rules
4. Review logs for registration errors

### Events Not Forwarding
1. Check federation is enabled: `ENABLE_FEDERATION=true`
2. Verify central server is online
3. Check event manager logs
4. Test federation endpoint manually

### Heartbeat Failures
1. Check network stability
2. Verify central server is responsive
3. Review heartbeat interval (default: 30s)
4. Check for high latency

## Performance Tuning

### Edge Nodes
- Use smaller AI models (YOLOv8n) for faster processing
- Reduce processing FPS to lower CPU usage
- Enable frame skipping for static scenes
- Process only necessary workflows

### Central Server
- Scale horizontally with load balancer
- Use PostgreSQL instead of SQLite for production
- Enable event database indexing
- Archive old events regularly

## Example Deployment

### 3-Site Setup
```yaml
# Site A (Edge)
- 8 cameras
- YOLOv8n model
- People detection only
- Forwards to central

# Site B (Edge)
- 12 cameras
- YOLOv8s model
- People + vehicle detection
- Forwards to central

# Central (HQ)
- No cameras
- Receives all events
- Analytics dashboard
- Long-term storage
```

Benefits:
- **95% reduction** in bandwidth vs streaming video
- **<200ms** local detection latency
- **Centralized monitoring** across all sites
- **Autonomous operation** if WAN fails

