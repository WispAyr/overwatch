# UniFi Integration Guide

## Overview

Overwatch provides comprehensive integration with Ubiquiti's UniFi ecosystem, including UniFi Network Controllers and UniFi Protect camera systems. This integration enables:

- **Automatic camera discovery** from UniFi Protect
- **Event monitoring** for motion and smart detections
- **Device status monitoring** for network equipment
- **Client/device tracking** for presence detection
- **Automated camera provisioning** into Overwatch

## Architecture

The UniFi integration is modular and credential-based:

1. **Credentials**: Store UniFi controller/Protect credentials per organization or site
2. **API Clients**: Dedicated clients for UniFi Controller and Protect APIs
3. **Workflow Nodes**: Visual workflow nodes that use credentials to access UniFi data
4. **Data Scoping**: All data is scoped to the user's credential pool - no cross-contamination

### Security Model

- Credentials are stored in the database (encryption recommended for production)
- Each credential can be scoped to an organization, site, or global
- Workflow nodes must reference a valid credential ID
- API clients use credential isolation

---

## Getting Started

### 1. Add UniFi Credentials

Navigate to the Admin Panel or use the API to add UniFi credentials.

#### Via API:

```bash
curl -X POST http://localhost:7001/api/unifi/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Office UniFi",
    "credential_type": "local",
    "host": "192.168.1.1",
    "port": 443,
    "username": "admin",
    "password": "your-password",
    "unifi_site": "default",
    "verify_ssl": false,
    "organization_id": "org-main",
    "enabled": true
  }'
```

#### Credential Types:

- `local`: Local UniFi Controller or Protect NVR
- `cloud`: UniFi Cloud (coming soon)

#### Required Fields:

| Field | Type | Local | Cloud | Description |
|-------|------|-------|-------|-------------|
| name | string | ✓ | ✓ | User-friendly credential name |
| credential_type | string | ✓ | ✓ | "local" or "cloud" |
| host | string | ✓ | - | IP or hostname of controller |
| port | integer | ✓ | - | HTTPS port (usually 443) |
| username | string | ✓ | - | Admin username |
| password | string | ✓ | - | Admin password |
| api_key | string | - | ✓ | Cloud API key |
| unifi_site | string | ✓ | - | Site name (default: "default") |
| verify_ssl | boolean | ✓ | ✓ | Verify SSL certificates |

### 2. Test Connection

Test credentials before using them in workflows:

```bash
curl -X POST http://localhost:7001/api/unifi/credentials/{credential_id}/test
```

Response:
```json
{
  "success": true,
  "type": "protect",
  "camera_count": 12,
  "nvr_name": "Office NVR",
  "nvr_version": "2.8.14",
  "cameras": [...]
}
```

### 3. Discover Cameras

Query cameras from UniFi Protect:

```bash
curl http://localhost:7001/api/unifi/credentials/{credential_id}/cameras
```

Response includes camera details and RTSP URLs:
```json
{
  "cameras": [
    {
      "id": "camera-id-123",
      "name": "Front Entrance",
      "model": "UVC-G4-PRO",
      "state": 2,
      "is_recording": true,
      "is_connected": true,
      "rtsp_urls": {
        "high": "rtsp://user:pass@192.168.1.100:7447/camera-id-123_0",
        "medium": "rtsp://user:pass@192.168.1.100:7447/camera-id-123_1",
        "low": "rtsp://user:pass@192.168.1.100:7447/camera-id-123_2"
      }
    }
  ]
}
```

---

## Workflow Nodes

### UniFi Camera Discovery Node

Discovers cameras from UniFi Protect and outputs camera list.

**Node Type**: `unifiCameraDiscovery`

**Configuration**:
- `credentialId` (required): UniFi credential ID
- `filterState`: Filter by connection state
  - `all`: All cameras
  - `connected`: Only connected cameras
  - `disconnected`: Only disconnected cameras
- `filterRecording`: Filter by recording status
  - `true`: Only recording cameras
  - `false`: Only non-recording cameras
  - `null`: All cameras

**Outputs**:
- `cameras-output`: Array of camera objects with RTSP URLs

**Example Workflow**:
```json
{
  "nodes": [
    {
      "id": "discovery-1",
      "type": "unifiCameraDiscovery",
      "data": {
        "credentialId": "cred-abc123",
        "filterState": "connected",
        "filterRecording": true
      }
    },
    {
      "id": "preview-1",
      "type": "dataPreview",
      "data": {}
    }
  ],
  "edges": [
    {
      "source": "discovery-1",
      "target": "preview-1",
      "sourceHandle": "cameras-output",
      "targetHandle": "data-input"
    }
  ]
}
```

---

### UniFi Protect Event Node

Monitors UniFi Protect for motion and smart detection events.

**Node Type**: `unifiProtectEvent`

**Configuration**:
- `credentialId` (required): UniFi credential ID
- `eventTypes`: Array of event types to monitor
  - `motion`: Motion detection events
  - `smart`: Smart detection events
  - `ring`: Doorbell ring events
- `cameraFilter`: Array of camera IDs or names to monitor
- `detectionTypes`: Array of smart detection types
  - `person`, `vehicle`, `animal`
- `pollInterval`: Polling interval in seconds (default: 10)

**Outputs**:
- `events-output`: Array of detection events

**Example**:
```json
{
  "id": "protect-events-1",
  "type": "unifiProtectEvent",
  "data": {
    "credentialId": "cred-abc123",
    "eventTypes": ["smart"],
    "detectionTypes": ["person", "vehicle"],
    "pollInterval": 5
  }
}
```

**Use Cases**:
- Trigger alarms on person detection
- Send notifications on vehicle detection
- Start recording when motion detected
- Integrate Protect events with AI workflows

---

### UniFi Device Status Node

Monitors UniFi network devices (APs, switches, gateways).

**Node Type**: `unifiDeviceStatus`

**Configuration**:
- `credentialId` (required): UniFi credential ID
- `deviceTypes`: Array of device types to monitor
  - `uap`: Access points
  - `usw`: Switches
  - `ugw`: Gateways
  - `usg`: Security gateways
- `checkOffline`: Include offline device alerts

**Outputs**:
- `devices-output`: Device status information

**Example**:
```json
{
  "id": "device-status-1",
  "type": "unifiDeviceStatus",
  "data": {
    "credentialId": "cred-abc123",
    "deviceTypes": ["uap", "usw"],
    "checkOffline": true
  }
}
```

**Use Cases**:
- Alert on offline access points
- Monitor network health
- Track device uptime
- Integration with network automation

---

### UniFi Client Detection Node

Detects network clients for presence detection and device tracking.

**Node Type**: `unifiClientDetection`

**Configuration**:
- `credentialId` (required): UniFi credential ID
- `macFilter`: Array of MAC addresses to watch
- `hostnameFilter`: Array of hostnames to watch
- `activeOnly`: Only return currently connected clients

**Outputs**:
- `clients-output`: Array of client information

**Example**:
```json
{
  "id": "client-detection-1",
  "type": "unifiClientDetection",
  "data": {
    "credentialId": "cred-abc123",
    "hostnameFilter": ["iphone", "android"],
    "activeOnly": true
  }
}
```

**Use Cases**:
- Employee presence detection
- VIP device tracking
- Automated access control
- Security alerts for unknown devices

---

### UniFi Add Camera Node

Automatically provisions discovered cameras into Overwatch.

**Node Type**: `unifiAddCamera`

**Configuration**:
- `sublocationId` (required): Overwatch sublocation to add cameras
- `streamQuality`: RTSP stream quality
  - `high`, `medium`, `low`
- `autoEnable`: Automatically enable cameras

**Inputs**:
- `cameras-input`: Camera array from discovery node

**Outputs**:
- `result-output`: Addition results

**Example Workflow**:
```json
{
  "nodes": [
    {
      "id": "discovery-1",
      "type": "unifiCameraDiscovery",
      "data": {
        "credentialId": "cred-abc123",
        "filterState": "connected"
      }
    },
    {
      "id": "add-cameras-1",
      "type": "unifiAddCamera",
      "data": {
        "sublocationId": "subloc-entrance",
        "streamQuality": "medium",
        "autoEnable": true
      }
    }
  ],
  "edges": [
    {
      "source": "discovery-1",
      "target": "add-cameras-1",
      "sourceHandle": "cameras-output",
      "targetHandle": "cameras-input"
    }
  ]
}
```

---

## Complete Example Workflows

### 1. Auto-Discover and Provision Cameras

Automatically discover UniFi cameras and add them to Overwatch:

```yaml
name: "UniFi Camera Auto-Provision"
nodes:
  - id: discover
    type: unifiCameraDiscovery
    data:
      credentialId: "main-office-unifi"
      filterState: connected
      filterRecording: true
      
  - id: add-to-overwatch
    type: unifiAddCamera
    data:
      sublocationId: "main-entrance"
      streamQuality: medium
      autoEnable: true
      
  - id: notify
    type: action
    data:
      actionType: webhook
      url: "https://slack.webhook.url"
      
edges:
  - source: discover
    target: add-to-overwatch
    sourceHandle: cameras-output
    targetHandle: cameras-input
    
  - source: add-to-overwatch
    target: notify
    sourceHandle: result-output
    targetHandle: trigger-input
```

### 2. Protect Event Integration

Monitor Protect smart detections and trigger Overwatch actions:

```yaml
name: "Protect Smart Detection Alert"
nodes:
  - id: protect-events
    type: unifiProtectEvent
    data:
      credentialId: "main-office-unifi"
      eventTypes: [smart]
      detectionTypes: [person, vehicle]
      pollInterval: 5
      
  - id: send-alert
    type: action
    data:
      actionType: alert
      severity: warning
      notify: [email, sms]
      
edges:
  - source: protect-events
    target: send-alert
```

### 3. Network Presence Detection

Track specific devices on the network:

```yaml
name: "VIP Device Tracking"
nodes:
  - id: client-monitor
    type: unifiClientDetection
    data:
      credentialId: "main-office-unifi"
      hostnameFilter: ["ceo-iphone", "manager-laptop"]
      activeOnly: true
      
  - id: log-presence
    type: action
    data:
      actionType: webhook
      url: "https://presence.api/log"
      
edges:
  - source: client-monitor
    target: log-presence
```

### 4. Hybrid UniFi + AI Workflow

Combine UniFi events with AI processing:

```yaml
name: "UniFi + AI Detection"
nodes:
  - id: protect-motion
    type: unifiProtectEvent
    data:
      credentialId: "main-unifi"
      eventTypes: [motion]
      
  - id: camera-input
    type: camera
    data:
      cameraId: "unifi_camera_1"
      
  - id: ai-model
    type: model
    data:
      modelId: "weapon-detector"
      confidence: 0.8
      
  - id: alert
    type: action
    data:
      actionType: alert
      severity: critical
      
edges:
  - source: camera-input
    target: ai-model
  - source: ai-model
    target: alert
```

---

## API Reference

### Credentials Management

#### List Credentials
```http
GET /api/unifi/credentials
GET /api/unifi/credentials?organization_id=org-123
GET /api/unifi/credentials?site_id=site-456
```

#### Get Credential
```http
GET /api/unifi/credentials/{credential_id}
```

#### Create Credential
```http
POST /api/unifi/credentials
Content-Type: application/json

{
  "name": "Office UniFi",
  "credential_type": "local",
  "host": "192.168.1.1",
  "username": "admin",
  "password": "password"
}
```

#### Update Credential
```http
PUT /api/unifi/credentials/{credential_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "enabled": true
}
```

#### Delete Credential
```http
DELETE /api/unifi/credentials/{credential_id}
```

#### Test Credential
```http
POST /api/unifi/credentials/{credential_id}/test
```

### UniFi Data Queries

#### Get Cameras
```http
GET /api/unifi/credentials/{credential_id}/cameras
```

#### Get Devices
```http
GET /api/unifi/credentials/{credential_id}/devices
```

#### Get Events
```http
GET /api/unifi/credentials/{credential_id}/events?limit=100
GET /api/unifi/credentials/{credential_id}/events?event_type=motion
GET /api/unifi/credentials/{credential_id}/events?event_type=smart
```

#### Get Sites
```http
GET /api/unifi/credentials/{credential_id}/sites
```

---

## Best Practices

### 1. Credential Organization

- **Per-Site Credentials**: Create separate credentials for each UniFi site
- **Naming Convention**: Use descriptive names like "HQ-UniFi-Protect"
- **Organization Scoping**: Link credentials to organizations for proper isolation

### 2. Security

- **SSL Verification**: Enable `verify_ssl` in production with valid certificates
- **Least Privilege**: Create dedicated UniFi users with minimal permissions
- **Password Rotation**: Rotate credentials regularly
- **Encryption**: Enable database encryption for stored passwords

### 3. Performance

- **Poll Intervals**: Use appropriate poll intervals (5-30 seconds)
- **Camera Filters**: Filter cameras at discovery to reduce data transfer
- **Event Filtering**: Use event type and camera filters to reduce noise

### 4. Integration Patterns

- **Discovery First**: Always run discovery before provisioning
- **Error Handling**: Use Catch nodes to handle credential failures
- **Data Preview**: Use preview nodes during development
- **Modular Workflows**: Create reusable subflows for common patterns

---

## Troubleshooting

### Connection Issues

**Problem**: "Authentication failed"
- **Solution**: Verify username/password, check UniFi user permissions

**Problem**: "SSL certificate verification failed"
- **Solution**: Set `verify_ssl: false` for self-signed certificates

**Problem**: "Connection timeout"
- **Solution**: Verify network connectivity, check firewall rules

### Discovery Issues

**Problem**: "No cameras found"
- **Solution**: Check Protect is running, verify credential type

**Problem**: "RTSP URLs not working"
- **Solution**: Verify network access to camera hosts, check RTSP port (7447)

### Workflow Issues

**Problem**: "Credential not found"
- **Solution**: Ensure credential ID is correct and credential is enabled

**Problem**: "Events not triggering"
- **Solution**: Check poll interval, verify event types are correct

---

## Migration from Manual Configuration

If you're currently using manual camera configuration, migrate to UniFi integration:

1. **Add UniFi Credentials** for each site
2. **Run Discovery Workflow** to find cameras
3. **Use Add Camera Node** to automatically provision
4. **Update Existing Workflows** to reference new camera IDs
5. **Remove Old Manual Entries** after verification

---

## Advanced Topics

### Custom API Clients

Create custom UniFi API integrations:

```python
from integrations.unifi import UniFiProtectClient

async def custom_integration():
    async with UniFiProtectClient(
        host="192.168.1.1",
        username="admin",
        password="password"
    ) as client:
        # Get cameras
        cameras = await client.get_cameras()
        
        # Get events
        events = await client.get_events(limit=50)
        
        # Update camera settings
        await client.update_camera(
            camera_id="cam-123",
            settings={"recordingSettings": {"mode": "always"}}
        )
```

### Database Schema

UniFi credentials are stored in the `unifi_credentials` table:

```sql
CREATE TABLE unifi_credentials (
    id TEXT PRIMARY KEY,
    organization_id TEXT,
    site_id TEXT,
    name TEXT NOT NULL,
    credential_type TEXT NOT NULL,
    host TEXT,
    port INTEGER DEFAULT 443,
    username TEXT,
    password TEXT,  -- Encrypt in production
    api_key TEXT,
    unifi_site TEXT DEFAULT 'default',
    verify_ssl INTEGER DEFAULT 1,
    extra_data TEXT,
    enabled INTEGER DEFAULT 1,
    last_test DATETIME,
    last_test_status TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## Support

For issues or questions:
- Check logs: `backend/logs/backend.log`
- Enable debug logging for UniFi modules
- Consult API documentation at `/api/docs`

## Future Enhancements

- UniFi Cloud API support
- UniFi Talk integration
- Access point client events
- Network topology visualization
- Automated failover for multi-site deployments

