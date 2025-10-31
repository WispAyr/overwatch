"""
Sublocation management API routes
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db, Sublocation, Site


router = APIRouter()


class SublocationCreate(BaseModel):
    """Sublocation creation model"""
    id: str
    site_id: str
    name: str
    description: Optional[str] = None
    sublocation_type: Optional[str] = None
    metadata: Optional[dict] = None
    

class SublocationUpdate(BaseModel):
    """Sublocation update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    sublocation_type: Optional[str] = None
    metadata: Optional[dict] = None
    

@router.get("/")
async def list_sublocations(
    site_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all sublocations"""
    query = db.query(Sublocation)
    
    if site_id:
        query = query.filter(Sublocation.site_id == site_id)
        
    sublocations = query.all()
    
    return {"sublocations": [
        {
            "id": sl.id,
            "site_id": sl.site_id,
            "name": sl.name,
            "description": sl.description,
            "sublocation_type": sl.sublocation_type,
            "metadata": sl.metadata,
            "created_at": sl.created_at.isoformat(),
            "updated_at": sl.updated_at.isoformat()
        }
        for sl in sublocations
    ]}
    

@router.get("/{sublocation_id}")
async def get_sublocation(sublocation_id: str, db: Session = Depends(get_db)):
    """Get sublocation details"""
    sl = db.query(Sublocation).filter(Sublocation.id == sublocation_id).first()
    
    if not sl:
        raise HTTPException(status_code=404, detail="Sublocation not found")
        
    return {
        "id": sl.id,
        "site_id": sl.site_id,
        "name": sl.name,
        "description": sl.description,
        "sublocation_type": sl.sublocation_type,
        "metadata": sl.metadata,
        "created_at": sl.created_at.isoformat(),
        "updated_at": sl.updated_at.isoformat()
    }
    

@router.post("/")
async def create_sublocation(sl: SublocationCreate, db: Session = Depends(get_db)):
    """Create a new sublocation"""
    # Verify site exists
    site = db.query(Site).filter(Site.id == sl.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    existing = db.query(Sublocation).filter(Sublocation.id == sl.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Sublocation already exists")
        
    new_sl = Sublocation(
        id=sl.id,
        site_id=sl.site_id,
        name=sl.name,
        description=sl.description,
        sublocation_type=sl.sublocation_type,
        metadata=sl.metadata or {}
    )
    
    db.add(new_sl)
    db.commit()
    db.refresh(new_sl)
    
    return {"message": "Sublocation created", "sublocation": {
        "id": new_sl.id,
        "name": new_sl.name,
        "sublocation_type": new_sl.sublocation_type
    }}
    

@router.put("/{sublocation_id}")
async def update_sublocation(
    sublocation_id: str,
    sl: SublocationUpdate,
    db: Session = Depends(get_db)
):
    """Update sublocation"""
    existing = db.query(Sublocation).filter(Sublocation.id == sublocation_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Sublocation not found")
        
    update_data = sl.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
        
    db.commit()
    
    return {"message": "Sublocation updated"}
    

@router.delete("/{sublocation_id}")
async def delete_sublocation(sublocation_id: str, db: Session = Depends(get_db)):
    """Delete sublocation"""
    sl = db.query(Sublocation).filter(Sublocation.id == sublocation_id).first()
    
    if not sl:
        raise HTTPException(status_code=404, detail="Sublocation not found")
        
    db.delete(sl)
    db.commit()
    
    return {"message": "Sublocation deleted"}

