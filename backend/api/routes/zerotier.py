"""
ZeroTier Management API routes
"""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from core.config import settings


router = APIRouter()


class MemberAuthorization(BaseModel):
    """Member authorization model"""
    zerotier_address: str
    node_name: Optional[str] = None


class NetworkConfig(BaseModel):
    """Network configuration model"""
    network_id: str
    name: str
    instructions: str


# Simple auth dependency (Comment 4)
async def require_auth(request: Request):
    """Require authentication for protected endpoints"""
    if not settings.ENABLE_AUTH:
        return True
    
    # Check for Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Simple token check (in production, use JWT validation)
    if not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    # TODO: Implement proper JWT validation
    return True


async def require_admin(request: Request, auth=Depends(require_auth)):
    """Require admin role for management operations"""
    # TODO: Check user role from JWT
    # For now, just require auth
    return auth


@router.get("/status")
async def get_zerotier_status(request: Request):
    """Get ZeroTier network status (Comment 8, 9)"""
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    status = await federation_manager.overlay_provider.status()
    
    return status


@router.get("/members")
async def list_zerotier_members(
    request: Request,
    auth=Depends(require_admin)  # Comment 4
):
    """List all ZeroTier network members"""
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    members = await federation_manager.overlay_provider.list_members()
    
    return {"members": members}


@router.post("/members/authorize")
async def authorize_member(
    member: MemberAuthorization,
    request: Request,
    auth=Depends(require_admin)  # Comment 4
):
    """Authorize a member to join the ZeroTier network"""
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    success = await federation_manager.overlay_provider.authorize_member(
        member.zerotier_address,
        member.node_name or ""
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to authorize member")
    
    return {"message": "Member authorized", "address": member.zerotier_address}


@router.post("/members/{zt_address}/deauthorize")
async def deauthorize_member(
    zt_address: str,
    request: Request,
    auth=Depends(require_admin)  # Comment 4
):
    """Deauthorize a member from the ZeroTier network"""
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    # For now, just return not implemented
    # Deauthorization requires updating member config via Central API
    raise HTTPException(status_code=501, detail="Deauthorization not yet implemented")


@router.get("/members/{zt_address}/ip")
async def get_member_ip(
    zt_address: str,
    request: Request,
    auth=Depends(require_auth)  # Comment 4
):
    """Get ZeroTier IP address for a member"""
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    ip = await federation_manager.overlay_provider.get_member_ip(zt_address)
    
    if not ip:
        raise HTTPException(status_code=404, detail="Member not found or no IP assigned")
    
    return {"zerotier_address": zt_address, "ip": ip}


@router.get("/network-config")
async def get_network_config(
    request: Request,
    auth=Depends(require_auth)  # Comment 4
):
    """
    Get network configuration for distribution to edge nodes (Comment 9)
    Returns network ID and join instructions
    """
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    status = await federation_manager.overlay_provider.status()
    network_id = status.get('network_id')
    
    if not network_id:
        raise HTTPException(status_code=404, detail="No network configured")
    
    instructions = f"""
# ZeroTier Network Join Instructions

1. Install ZeroTier on the edge node:
   curl -s https://install.zerotier.com | sudo bash

2. Join the network:
   sudo zerotier-cli join {network_id}

3. Your node will appear in the pending members list.

4. Authorize the node from the central server dashboard or CLI:
   POST /api/zerotier/members/authorize
   {{ "zerotier_address": "<your-node-id>" }}

5. Configure your edge node:
   ENABLE_ZEROTIER=true
   ZEROTIER_NETWORK_ID={network_id}
   CENTRAL_SERVER_URL=<central-url>

6. Start your edge node.
"""
    
    return {
        "network_id": network_id,
        "name": settings.ZEROTIER_NETWORK_NAME,
        "instructions": instructions.strip(),
        "join_command": f"sudo zerotier-cli join {network_id}"
    }


@router.post("/network/create")
async def create_network(
    request: Request,
    auth=Depends(require_admin)  # Comment 4
):
    """Create a new ZeroTier network (central server only)"""
    if settings.NODE_TYPE != 'central':
        raise HTTPException(status_code=403, detail="Only central server can create networks")
    
    federation_manager = request.app.state.federation_manager
    
    if not federation_manager.overlay_provider:
        raise HTTPException(status_code=400, detail="Overlay network not enabled")
    
    success = await federation_manager.overlay_provider.ensure_network()
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create network")
    
    status = await federation_manager.overlay_provider.status()
    
    return {
        "message": "Network created",
        "network_id": status.get('network_id'),
        "node_id": status.get('node_id')
    }
