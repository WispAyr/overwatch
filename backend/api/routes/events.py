"""
Event query API routes
"""
from typing import Optional
from fastapi import APIRouter, Request, Query
from datetime import datetime


router = APIRouter()


@router.get("")
@router.get("/")
async def list_events(
    request: Request,
    # Canonical filters
    tenant: Optional[str] = None,
    site: Optional[str] = None,
    source_type: Optional[str] = None,
    # Legacy filters
    camera_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    severity: Optional[str] = None,
    # Pagination
    limit: int = Query(100, le=1000),
    offset: int = 0,
    since_ts: Optional[str] = None,
    before_ts: Optional[str] = None
):
    """List events with filtering and cursor-based pagination"""
    event_manager = request.app.state.event_manager
    
    events = await event_manager.query_events(
        tenant=tenant,
        site=site,
        source_type=source_type,
        camera_id=camera_id,
        workflow_id=workflow_id,
        severity=severity,
        limit=limit,
        offset=offset,
        since_ts=since_ts,
        before_ts=before_ts
    )
    
    total = await event_manager.count_events(
        tenant=tenant,
        site=site,
        source_type=source_type,
        camera_id=camera_id,
        workflow_id=workflow_id,
        severity=severity
    )
    
    # Cursor pagination metadata
    next_cursor = None
    prev_cursor = None
    if events:
        next_cursor = events[-1]['observed']
        if offset > 0:
            prev_cursor = events[0]['observed']
    
    return {
        'events': events,
        'total': total,
        'limit': limit,
        'offset': offset,
        'next_cursor': next_cursor,
        'prev_cursor': prev_cursor
    }
    

@router.get("/{event_id}")
async def get_event(event_id: str, request: Request):
    """Get event details"""
    event_manager = request.app.state.event_manager
    
    event = await event_manager.get_event(event_id)
    
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
        
    return event

