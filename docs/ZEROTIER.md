# ZeroTier Integration Guide

## Overview

Overwatch integrates [ZeroTier](https://www.zerotier.com) to provide secure, encrypted P2P communication between federated nodes. This eliminates the need for complex VPN setups, port forwarding, or firewall configuration.

As described in the [ZeroTier SDK blog post](https://www.zerotier.com/blog/the-zerotier-sdk-p2p-apps-with-standard-protocols/), ZeroTier enables P2P applications to communicate using standard protocols (HTTP, WebSocket) while providing automatic encryption and NAT traversal.

## Benefits

- **Zero Configuration**: No VPN servers, port forwarding, or firewall rules
- **Automatic Encryption**: All traffic encrypted end-to-end
- **NAT Traversal**: Works across any network topology
- **Central Management**: Control network access from Overwatch central server
- **Low Latency**: Direct P2P connections (typically <50ms)
- **Secure by Default**: Private network with member authorization

## Architecture

```
┌──────────────────────────────────────────────┐
│         ZeroTier Network (10.147.0.0/16)     │
│                                              │
│  ┌─────────────┐         ┌─────────────┐    │
│  │  Central    │         │  Edge Node  │    │
│  │  10.147.0.1 │◄───────►│  10.147.0.2 │    │
│  └─────────────┘         └─────────────┘    │
│         ▲                                    │
│         │                                    │
│         │ Direct P2P                         │
│         ▼                                    │
│  ┌─────────────┐         ┌─────────────┐    │
│  │ Edge Node   │         │ Mobile Unit │    │
│  │ 10.147.0.3  │◄───────►│ 10.147.0.4  │    │
│  └─────────────┘         └─────────────┘    │
│                                              │
└──────────────────────────────────────────────┘
```

## Setup

### Prerequisites

1. **Install ZeroTier**
   - Download from: https://www.zerotier.com/download/
   - Available for Linux, macOS, Windows, iOS, Android
   
2. **Get API Token** (Central Server Only)
   - Sign up at: https://my.zerotier.com/
   - Go to Account → API Access Tokens
   - Generate new token

### Central Server Setup

1. **Install ZeroTier**
   ```bash
   # Ubuntu/Debian
   curl -s https://install.zerotier.com | sudo bash
   
   # macOS
   brew install zerotier-one
   
   # Start service
   sudo systemctl start zerotier-one
   ```

2. **Configure Overwatch**
   ```bash
   # .env
   ENABLE_FEDERATION=true
   ENABLE_ZEROTIER=true
   NODE_TYPE=central
   NODE_ID=central-hq
   
   # ZeroTier settings
   ZEROTIER_API_TOKEN=your-api-token-from-my.zerotier.com
   # Leave ZEROTIER_NETWORK_ID empty - will be auto-created
   
   # Optional: Customize IP range and network name
   ZEROTIER_IP_RANGE_START=10.147.0.1
   ZEROTIER_IP_RANGE_END=10.147.255.254
   ZEROTIER_ROUTE_TARGET=10.147.0.0/16
   ZEROTIER_NETWORK_NAME="Overwatch Federation"
   ```

3. **Start Overwatch**
   ```bash
   python backend/main.py
   ```
   
   The central server will:
   - Auto-create a new ZeroTier network
   - Configure network settings (private, IP range)
   - Join the network automatically (receives assigned IP)
   - Save network ID for edge nodes
   
   **Note**: If ZeroTier is not installed locally or permissions are denied, the system will operate in management-only mode (network creation via Central API only, no local join). Edge nodes always require local ZeroTier installation.

4. **Get Network ID**
   ```bash
   # Check logs
   grep "ZeroTier network" logs/overwatch.log
   
   # Or via API
   curl http://localhost:8000/api/zerotier/status
   ```

### Edge Node Setup

1. **Install ZeroTier**
   ```bash
   # Same as central server
   curl -s https://install.zerotier.com | sudo bash
   sudo systemctl start zerotier-one
   ```

2. **Configure Overwatch**
   ```bash
   # .env
   ENABLE_FEDERATION=true
   ENABLE_ZEROTIER=true
   NODE_TYPE=edge
   NODE_ID=edge-site-a
   CENTRAL_SERVER_URL=http://central-hq:8000
   
   # ZeroTier settings
   ZEROTIER_NETWORK_ID=<network-id-from-central>
   # API token not needed for edge nodes
   ```

3. **Start Overwatch**
   ```bash
   python backend/main.py
   ```
   
   The edge node will:
   - Join the ZeroTier network
   - Wait for authorization from central
   - Register with central server
   - Start receiving ZeroTier IP

### Authorization

Edge nodes need to be authorized by the central server:

**Option 1: Auto-authorization (NEW)**
When an edge node registers with federation and includes its ZeroTier node ID in the metadata, the central server automatically authorizes it in the network. This provides seamless onboarding.

**Option 2: Dashboard Wizard**
1. Go to Federation tab in Overwatch dashboard
2. Click "Setup Mesh Network"
3. View pending members in step 5
4. Click "Authorize" for each pending node

**Option 3: API**
```bash
# From central server
curl -X POST http://localhost:8000/api/zerotier/members/authorize \
  -H "Content-Type: application/json" \
  -d '{
    "zerotier_address": "a1b2c3d4e5",
    "node_name": "edge-site-a"
  }'
```

**Option 4: ZeroTier Central**
1. Go to https://my.zerotier.com/
2. Select your network
3. Find pending member
4. Check "Authorized"

## Management API

**Note**: ZeroTier and Federation management routes require authentication when `ENABLE_AUTH=true`. Include `Authorization: Bearer <token>` header for member operations.

### Get Network Status
```bash
GET /api/zerotier/status
```

Response:
```json
{
  "enabled": true,
  "provider": "zerotier",
  "online": true,
  "node_id": "a1b2c3d4e5",
  "network_id": "8056c2e21c000001",
  "assigned_addresses": ["10.147.0.1/16"],
  "peer_count": 3,
  "member_count": 4,
  "local_api_available": true,
  "last_error": null
}
```

### List Members
```bash
GET /api/zerotier/members
```

Response:
```json
{
  "members": [
    {
      "nodeId": "a1b2c3d4e5",
      "name": "central-hq",
      "authorized": true,
      "ipAssignments": ["10.147.0.1"],
      "online": true
    },
    {
      "nodeId": "f6e5d4c3b2",
      "name": "edge-site-a",
      "authorized": true,
      "ipAssignments": ["10.147.0.2"],
      "online": true
    }
  ]
}
```

### Authorize Member
```bash
POST /api/zerotier/members/authorize
Content-Type: application/json

{
  "zerotier_address": "f6e5d4c3b2",
  "node_name": "edge-site-a"
}
```

### Deauthorize Member
```bash
POST /api/zerotier/members/{zt_address}/deauthorize
```

### Get Member IP
```bash
GET /api/zerotier/members/{zt_address}/ip
```

### Get Network Config (NEW)
```bash
GET /api/zerotier/network-config
```

Returns network ID and join instructions for distributing to edge nodes:
```json
{
  "network_id": "8056c2e21c000001",
  "name": "Overwatch Federation",
  "join_command": "sudo zerotier-cli join 8056c2e21c000001",
  "instructions": "# Full setup instructions..."
}
```

### Create Network (NEW)
```bash
POST /api/zerotier/network/create
```

Creates a new ZeroTier network (central server only).

## Network Configuration

The central server automatically configures:

**IP Range**: `10.147.0.0/16`
- 65,534 available addresses
- Auto-assignment enabled

**Network Type**: Private
- Members must be authorized
- Controlled by central server

**Routing**: Full mesh
- Direct P2P between all nodes
- Automatic route optimization

**Encryption**: AES-256
- All traffic encrypted
- Perfect forward secrecy

## Communication Flow

1. **Node Registration (Auto-discovery)**
   ```
   Edge Node → ZeroTier Network (join, get assigned IP)
   Edge Node → Central /api/zerotier/status (discover central's ZT IP)
   Edge Node → Central /api/federation/register (includes ZT node ID)
   Central Server → ZeroTier API (auto-authorize)
   Edge Node → Test mesh connectivity, switch to mesh URL
   ```

2. **Event Forwarding (Mesh-preferred)**
   ```
   Edge processes video → Detection event
   Event → Central via mesh IP (http://10.147.0.1:8000) OR public fallback
   Encrypted P2P tunnel → Direct delivery
   ```

3. **Hierarchy Sync**
   ```
   Edge → Central /api/federation/sync/hierarchy
   Via ZeroTier network (encrypted) with automatic fallback
   ```

4. **Health Checks & Fallback (NEW)**
   ```
   Edge → Periodic health check (mesh URL + public URL)
   Prefer mesh when healthy, fall back to public on failure
   Log transitions for monitoring
   ```

## Firewall Configuration

**No inbound firewall rules needed!**

ZeroTier only requires:
- **Outbound UDP**: Port 9993 (ZeroTier protocol)
- Internet connectivity for initial setup

All Overwatch communication happens over the ZeroTier tunnel.

## Troubleshooting

### Check ZeroTier Status
```bash
# Linux/macOS
sudo zerotier-cli status
sudo zerotier-cli listnetworks

# Windows
zerotier-cli.bat status
zerotier-cli.bat listnetworks
```

### Check Network Membership
```bash
sudo zerotier-cli listpeers
```

### Test Connectivity
```bash
# From edge node, ping central
ping 10.147.0.1

# Test API
curl http://10.147.0.1:8000/health
```

### Common Issues

**"Network not found"**
- Check `ZEROTIER_NETWORK_ID` is correct
- Verify network exists: https://my.zerotier.com/

**"Not authorized"**
- Node needs authorization from central
- Check member list on my.zerotier.com
- Or use API: `POST /api/zerotier/members/authorize`

**"No IP assigned"**
- Network may be out of IPs (unlikely with /16)
- Check network IP pool configuration
- Restart ZeroTier: `sudo systemctl restart zerotier-one`

**"Can't reach central server"**
- Verify ZeroTier network is connected
- Check IP assignment: `zerotier-cli listnetworks`
- Ensure Overwatch is listening on ZeroTier interface

### Debug Logging
```bash
# Enable ZeroTier debug logging
sudo zerotier-cli set <network-id> allowDefault=1

# Watch logs
tail -f /var/log/syslog | grep zerotier  # Linux
log stream --predicate 'process == "zerotier-one"'  # macOS
```

## Performance

### Latency
- **Typical P2P**: 10-50ms
- **Via relay**: 100-200ms (when P2P not possible)

### Bandwidth
- **Per connection**: Up to 1 Gbps
- **Total network**: Unlimited (P2P mesh)

### Overhead
- **Encryption**: ~5% CPU
- **Memory**: ~50MB per node

## Security Best Practices

1. **Use API Tokens Securely**
   - Store in `.env` file (gitignored)
   - Never commit to version control
   - Rotate tokens periodically
   - **NEW**: Logs automatically redact API tokens and secrets

2. **Network Access Control**
   - Keep network private
   - Only authorize known nodes
   - Review member list regularly
   - **NEW**: Enable `ENABLE_AUTH=true` for API protection

3. **Monitor Activity**
   - Check member online status
   - Review connection logs
   - Alert on unauthorized joins
   - **NEW**: Dashboard shows peer count and health status

4. **Update Regularly**
   - Keep ZeroTier updated
   - Monitor security advisories
   - Test updates in staging first

5. **Don't Share Logs**
   - Even with redaction, avoid sharing logs publicly
   - Secrets may appear in exception traces

## Advanced Configuration

### Custom IP Ranges
Configure via environment variables (`.env`):
```bash
ZEROTIER_IP_RANGE_START=192.168.192.1
ZEROTIER_IP_RANGE_END=192.168.192.254
ZEROTIER_ROUTE_TARGET=192.168.192.0/24
ZEROTIER_NETWORK_NAME="My Custom Network"
```

Defaults:
- IP Range: `10.147.0.1` - `10.147.255.254`
- Route: `10.147.0.0/16`
- Name: `Overwatch Federation`

### Flow Rules
Add custom flow rules for advanced traffic control:
```python
"rules": [
    {
        "type": "ACTION_DROP",
        "not": True,
        "or": [
            {"type": "MATCH_ETHERTYPE", "etherType": 2048},  # IPv4
            {"type": "MATCH_ETHERTYPE", "etherType": 2054}   # ARP
        ]
    },
    {
        "type": "ACTION_ACCEPT"
    }
]
```

### Multi-Network Support
Deploy separate ZeroTier networks for:
- Production vs staging
- Different organizations
- Security zones (DMZ, internal)

## Migration from Traditional VPN

**Before (OpenVPN/WireGuard)**
- Configure VPN server
- Generate certificates
- Configure firewall rules
- Port forwarding
- Client configuration distribution

**After (ZeroTier)**
- Install ZeroTier
- Add `ZEROTIER_NETWORK_ID` to config
- Done!

## Cost

ZeroTier is **free** for up to 100 devices per network.

For larger deployments:
- Professional: $5/user/month
- Enterprise: Custom pricing

See: https://www.zerotier.com/pricing/

## References

- [ZeroTier Documentation](https://docs.zerotier.com/)
- [ZeroTier API Reference](https://docs.zerotier.com/central/v1/)
- [ZeroTier SDK Blog Post](https://www.zerotier.com/blog/the-zerotier-sdk-p2p-apps-with-standard-protocols/)
- [GitHub Repository](https://github.com/zerotier/ZeroTierOne)

