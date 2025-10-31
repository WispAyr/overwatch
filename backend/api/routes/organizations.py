"""
Organization management API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db, Organization


router = APIRouter()


class OrganizationCreate(BaseModel):
    """Organization creation model"""
    id: str
    name: str
    description: Optional[str] = None
    organization_type: Optional[str] = None
    metadata: Optional[dict] = None
    

class OrganizationUpdate(BaseModel):
    """Organization update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    organization_type: Optional[str] = None
    metadata: Optional[dict] = None
    

@router.get("/")
async def list_organizations(db: Session = Depends(get_db)):
    """List all organizations"""
    orgs = db.query(Organization).all()
    return {"organizations": [
        {
            "id": org.id,
            "name": org.name,
            "description": org.description,
            "organization_type": (org.extra_data or {}).get("organization_type"),
            "metadata": org.extra_data,
            "created_at": org.created_at.isoformat(),
            "updated_at": org.updated_at.isoformat()
        }
        for org in orgs
    ]}
    

@router.get("/{org_id}")
async def get_organization(org_id: str, db: Session = Depends(get_db)):
    """Get organization details"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return {
        "id": org.id,
        "name": org.name,
        "description": org.description,
        "organization_type": (org.extra_data or {}).get("organization_type"),
        "metadata": org.extra_data,
        "created_at": org.created_at.isoformat(),
        "updated_at": org.updated_at.isoformat()
    }
    

@router.post("/")
async def create_organization(org: OrganizationCreate, db: Session = Depends(get_db)):
    """Create a new organization"""
    existing = db.query(Organization).filter(Organization.id == org.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Organization already exists")
    
    # Store organization_type in extra_data
    extra_data = org.metadata or {}
    if org.organization_type:
        extra_data["organization_type"] = org.organization_type
        
    new_org = Organization(
        id=org.id,
        name=org.name,
        description=org.description,
        extra_data=extra_data
    )
    
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    
    return {"message": "Organization created", "organization": {
        "id": new_org.id,
        "name": new_org.name,
        "description": new_org.description,
        "organization_type": org.organization_type
    }}
    

@router.put("/{org_id}")
async def update_organization(
    org_id: str,
    org: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization"""
    existing = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    update_data = org.dict(exclude_unset=True)
    
    # Handle organization_type in extra_data
    if "organization_type" in update_data:
        extra_data = existing.extra_data or {}
        extra_data["organization_type"] = update_data.pop("organization_type")
        existing.extra_data = extra_data
        
    # Handle metadata updates
    if "metadata" in update_data:
        existing.extra_data = update_data.pop("metadata")
    
    # Update remaining fields
    for key, value in update_data.items():
        setattr(existing, key, value)
        
    db.commit()
    
    return {"message": "Organization updated"}
    

@router.delete("/{org_id}")
async def delete_organization(org_id: str, db: Session = Depends(get_db)):
    """Delete organization"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    db.delete(org)
    db.commit()
    
    return {"message": "Organization deleted"}

