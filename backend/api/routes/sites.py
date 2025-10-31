"""
Site management API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db, Site, Organization


router = APIRouter()


class SiteCreate(BaseModel):
    """Site creation model"""
    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    site_type: str = "fixed"  # fixed or mobile
    location: Optional[dict] = None
    metadata: Optional[dict] = None
    

class SiteUpdate(BaseModel):
    """Site update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    site_type: Optional[str] = None
    location: Optional[dict] = None
    metadata: Optional[dict] = None
    

@router.get("/")
async def list_sites(
    organization_id: Optional[str] = None,
    site_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all sites with optional filtering"""
    query = db.query(Site)
    
    if organization_id:
        query = query.filter(Site.organization_id == organization_id)
        
    if site_type:
        query = query.filter(Site.site_type == site_type)
        
    sites = query.all()
    
    return {"sites": [
        {
            "id": site.id,
            "organization_id": site.organization_id,
            "name": site.name,
            "description": site.description,
            "site_type": site.site_type,
            "location": site.location,
            "metadata": site.metadata,
            "created_at": site.created_at.isoformat(),
            "updated_at": site.updated_at.isoformat()
        }
        for site in sites
    ]}
    

@router.get("/{site_id}")
async def get_site(site_id: str, db: Session = Depends(get_db)):
    """Get site details"""
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    return {
        "id": site.id,
        "organization_id": site.organization_id,
        "name": site.name,
        "description": site.description,
        "site_type": site.site_type,
        "location": site.location,
        "metadata": site.metadata,
        "created_at": site.created_at.isoformat(),
        "updated_at": site.updated_at.isoformat()
    }
    

@router.post("/")
async def create_site(site: SiteCreate, db: Session = Depends(get_db)):
    """Create a new site"""
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == site.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    existing = db.query(Site).filter(Site.id == site.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Site already exists")
        
    new_site = Site(
        id=site.id,
        organization_id=site.organization_id,
        name=site.name,
        description=site.description,
        site_type=site.site_type,
        location=site.location or {},
        metadata=site.metadata or {}
    )
    
    db.add(new_site)
    db.commit()
    db.refresh(new_site)
    
    return {"message": "Site created", "site": {
        "id": new_site.id,
        "name": new_site.name,
        "site_type": new_site.site_type
    }}
    

@router.put("/{site_id}")
async def update_site(site_id: str, site: SiteUpdate, db: Session = Depends(get_db)):
    """Update site"""
    existing = db.query(Site).filter(Site.id == site_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Site not found")
        
    update_data = site.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
        
    db.commit()
    
    return {"message": "Site updated"}
    

@router.delete("/{site_id}")
async def delete_site(site_id: str, db: Session = Depends(get_db)):
    """Delete site"""
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    db.delete(site)
    db.commit()
    
    return {"message": "Site deleted"}

