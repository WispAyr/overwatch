"""
UniFi Integration API Routes
Manage UniFi credentials and query UniFi data
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from core.database import get_db, UniFiCredential
from integrations.unifi.manager import UniFiCredentialManager

router = APIRouter()


class UniFiCredentialCreate(BaseModel):
    """UniFi credential creation model"""
    name: str
    credential_type: str  # 'local' or 'cloud'
    host: Optional[str] = None
    port: int = 443
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    unifi_site: str = "default"
    verify_ssl: bool = False
    organization_id: Optional[str] = None
    site_id: Optional[str] = None
    enabled: bool = True
    extra_data: Optional[dict] = None


class UniFiCredentialUpdate(BaseModel):
    """UniFi credential update model"""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    unifi_site: Optional[str] = None
    verify_ssl: Optional[bool] = None
    organization_id: Optional[str] = None
    site_id: Optional[str] = None
    enabled: Optional[bool] = None
    extra_data: Optional[dict] = None


# Credential Management

@router.get("/credentials")
async def list_credentials(
    organization_id: Optional[str] = None,
    site_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all UniFi credentials"""
    manager = UniFiCredentialManager(db)
    credentials = manager.get_credentials(
        organization_id=organization_id,
        site_id=site_id,
        enabled_only=False
    )
    
    # Redact passwords in response
    return {
        "credentials": [
            {
                "id": c.id,
                "name": c.name,
                "credential_type": c.credential_type,
                "host": c.host,
                "port": c.port,
                "username": c.username,
                "unifi_site": c.unifi_site,
                "organization_id": c.organization_id,
                "site_id": c.site_id,
                "enabled": bool(c.enabled),
                "last_test": c.last_test.isoformat() if c.last_test else None,
                "last_test_status": c.last_test_status,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in credentials
        ]
    }


@router.get("/credentials/{credential_id}")
async def get_credential(credential_id: str, db: Session = Depends(get_db)):
    """Get specific UniFi credential"""
    manager = UniFiCredentialManager(db)
    cred = manager.get_credential(credential_id)
    
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    return {
        "id": cred.id,
        "name": cred.name,
        "credential_type": cred.credential_type,
        "host": cred.host,
        "port": cred.port,
        "username": cred.username,
        "unifi_site": cred.unifi_site,
        "verify_ssl": bool(cred.verify_ssl),
        "organization_id": cred.organization_id,
        "site_id": cred.site_id,
        "enabled": bool(cred.enabled),
        "extra_data": cred.extra_data,
        "last_test": cred.last_test.isoformat() if cred.last_test else None,
        "last_test_status": cred.last_test_status,
        "created_at": cred.created_at.isoformat(),
        "updated_at": cred.updated_at.isoformat()
    }


@router.post("/credentials")
async def create_credential(credential: UniFiCredentialCreate, db: Session = Depends(get_db)):
    """Create new UniFi credential"""
    # Validate credential type
    if credential.credential_type not in ['local', 'cloud']:
        raise HTTPException(status_code=400, detail="Invalid credential_type")
    
    # Validate required fields
    if credential.credential_type == 'local':
        if not credential.host or not credential.username or not credential.password:
            raise HTTPException(
                status_code=400,
                detail="Local credentials require host, username, and password"
            )
    
    # Create credential
    new_cred = UniFiCredential(
        id=str(uuid.uuid4()),
        name=credential.name,
        credential_type=credential.credential_type,
        host=credential.host,
        port=credential.port,
        username=credential.username,
        password=credential.password,  # TODO: Encrypt in production
        api_key=credential.api_key,
        unifi_site=credential.unifi_site,
        verify_ssl=1 if credential.verify_ssl else 0,
        organization_id=credential.organization_id,
        site_id=credential.site_id,
        enabled=1 if credential.enabled else 0,
        extra_data=credential.extra_data or {}
    )
    
    db.add(new_cred)
    db.commit()
    db.refresh(new_cred)
    
    return {
        "message": "UniFi credential created",
        "credential": {
            "id": new_cred.id,
            "name": new_cred.name,
            "credential_type": new_cred.credential_type
        }
    }


@router.put("/credentials/{credential_id}")
async def update_credential(
    credential_id: str,
    credential: UniFiCredentialUpdate,
    db: Session = Depends(get_db)
):
    """Update UniFi credential"""
    existing = db.query(UniFiCredential).filter(UniFiCredential.id == credential_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Update fields
    update_data = credential.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == 'enabled':
            setattr(existing, field, 1 if value else 0)
        elif field == 'verify_ssl':
            setattr(existing, field, 1 if value else 0)
        else:
            setattr(existing, field, value)
    
    existing.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(existing)
    
    # Clear cache for this credential
    manager = UniFiCredentialManager(db)
    manager.clear_cache(credential_id)
    
    return {
        "message": "UniFi credential updated",
        "credential": {
            "id": existing.id,
            "name": existing.name
        }
    }


@router.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str, db: Session = Depends(get_db)):
    """Delete UniFi credential"""
    existing = db.query(UniFiCredential).filter(UniFiCredential.id == credential_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    db.delete(existing)
    db.commit()
    
    # Clear cache
    manager = UniFiCredentialManager(db)
    manager.clear_cache(credential_id)
    
    return {"message": "UniFi credential deleted"}


@router.post("/credentials/{credential_id}/test")
async def test_credential(credential_id: str, db: Session = Depends(get_db)):
    """Test UniFi credential connection"""
    manager = UniFiCredentialManager(db)
    cred = manager.get_credential(credential_id)
    
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Test connection
    result = await manager.test_credential(credential_id)
    
    # Update test status
    cred.last_test = datetime.utcnow()
    cred.last_test_status = "success" if result.get('success') else "failed"
    db.commit()
    
    return result


# UniFi Data Queries

@router.get("/credentials/{credential_id}/cameras")
async def get_cameras(credential_id: str, db: Session = Depends(get_db)):
    """Get cameras from UniFi Protect"""
    manager = UniFiCredentialManager(db)
    
    protect_client = manager.get_protect_client(credential_id)
    if not protect_client:
        raise HTTPException(status_code=400, detail="Failed to create Protect client")
    
    try:
        async with protect_client:
            cameras = await protect_client.get_cameras()
            
            return {
                "cameras": [
                    {
                        "id": c.get('id'),
                        "name": c.get('name'),
                        "model": c.get('type'),
                        "mac": c.get('mac'),
                        "state": c.get('state'),
                        "is_recording": c.get('isRecording', False),
                        "is_connected": c.get('isConnected', False),
                        "channels": c.get('channels', []),
                        "host": c.get('host'),
                        # Generate RTSP URLs for each channel
                        "rtsp_urls": {
                            "high": protect_client.get_rtsp_url(c, 0),
                            "medium": protect_client.get_rtsp_url(c, 1),
                            "low": protect_client.get_rtsp_url(c, 2)
                        }
                    }
                    for c in cameras
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cameras: {str(e)}")


@router.get("/credentials/{credential_id}/devices")
async def get_devices(credential_id: str, db: Session = Depends(get_db)):
    """Get devices from UniFi controller"""
    manager = UniFiCredentialManager(db)
    
    client = manager.get_client(credential_id)
    if not client:
        raise HTTPException(status_code=400, detail="Failed to create controller client")
    
    try:
        async with client:
            devices = await client.get_devices()
            
            return {
                "devices": [
                    {
                        "mac": d.get('mac'),
                        "name": d.get('name'),
                        "model": d.get('model'),
                        "type": d.get('type'),
                        "state": d.get('state'),
                        "version": d.get('version'),
                        "ip": d.get('ip'),
                        "uptime": d.get('uptime')
                    }
                    for d in devices
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {str(e)}")


@router.get("/credentials/{credential_id}/events")
async def get_events(
    credential_id: str,
    limit: int = 100,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get events from UniFi Protect"""
    manager = UniFiCredentialManager(db)
    
    protect_client = manager.get_protect_client(credential_id)
    if not protect_client:
        raise HTTPException(status_code=400, detail="Failed to create Protect client")
    
    try:
        async with protect_client:
            if event_type == 'motion':
                events = await protect_client.get_motion_events(limit=limit)
            elif event_type == 'smart':
                events = await protect_client.get_smart_detections(limit=limit)
            else:
                events = await protect_client.get_events(limit=limit)
            
            return {
                "events": events
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@router.get("/credentials/{credential_id}/sites")
async def get_sites(credential_id: str, db: Session = Depends(get_db)):
    """Get UniFi sites from controller"""
    manager = UniFiCredentialManager(db)
    
    client = manager.get_client(credential_id)
    if not client:
        raise HTTPException(status_code=400, detail="Failed to create controller client")
    
    try:
        async with client:
            sites = await client.get_sites()
            
            return {
                "sites": [
                    {
                        "name": s.get('name'),
                        "desc": s.get('desc'),
                        "role": s.get('role')
                    }
                    for s in sites
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sites: {str(e)}")

