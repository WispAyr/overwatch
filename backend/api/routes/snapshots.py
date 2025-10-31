"""
Snapshot serving routes
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from core.config import settings


router = APIRouter()


@router.get("/{event_id}")
async def get_snapshot(event_id: str):
    """Get snapshot image for an event"""
    snapshot_dir = Path(settings.SNAPSHOT_DIR)
    
    # Find snapshot file matching event_id
    snapshots = list(snapshot_dir.glob(f"{event_id}_*.jpg"))
    
    if not snapshots:
        raise HTTPException(status_code=404, detail="Snapshot not found")
        
    return FileResponse(
        path=str(snapshots[0]),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"}
    )


