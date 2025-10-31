"""
Alarm API Routes
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/api/alarms", tags=["alarms"])


class AcknowledgeRequest(BaseModel):
    user: str


class AssignRequest(BaseModel):
    assignee: str
    user: str


class TransitionRequest(BaseModel):
    to_state: str
    user: Optional[str] = None
    note: Optional[str] = None


class NoteRequest(BaseModel):
    note: str
    user: Optional[str] = None


@router.get("")
async def list_alarms(
    request: Request,
    tenant: Optional[str] = None,
    site: Optional[str] = None,
    state: Optional[str] = None,
    severity: Optional[str] = None,
    assignee: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List alarms with filters"""
    alarm_manager = request.app.state.alarm_manager
    
    alarms = await alarm_manager.query_alarms(
        tenant=tenant,
        site=site,
        state=state,
        severity=severity,
        assignee=assignee,
        limit=limit,
        offset=offset
    )
    
    total = await alarm_manager.count_alarms(
        tenant=tenant,
        site=site,
        state=state,
        severity=severity
    )
    
    return {
        'alarms': alarms,
        'total': total,
        'limit': limit,
        'offset': offset
    }


@router.get("/{alarm_id}")
async def get_alarm(request: Request, alarm_id: str, include_history: bool = False):
    """Get alarm details"""
    alarm_manager = request.app.state.alarm_manager
    
    if include_history:
        alarm = await alarm_manager.get_alarm_with_history(alarm_id)
    else:
        alarm = await alarm_manager.get_alarm(alarm_id)
        
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
        
    return alarm


@router.post("/{alarm_id}/ack")
async def acknowledge_alarm(request: Request, alarm_id: str, data: AcknowledgeRequest):
    """Acknowledge an alarm"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.acknowledge_alarm(alarm_id, data.user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alarm_id}/assign")
async def assign_alarm(request: Request, alarm_id: str, data: AssignRequest):
    """Assign an alarm to an operator"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.assign_alarm(alarm_id, data.assignee, data.user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alarm_id}/transition")
async def transition_alarm(request: Request, alarm_id: str, data: TransitionRequest):
    """Transition alarm to new state"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.transition_alarm(
            alarm_id,
            data.to_state,
            user=data.user,
            note=data.note
        )
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alarm_id}/notes")
async def add_note(request: Request, alarm_id: str, data: NoteRequest):
    """Add a note to an alarm"""
    alarm_manager = request.app.state.alarm_manager
    
    await alarm_manager.add_note(alarm_id, data.note, data.user)
    
    return {"status": "ok"}


@router.get("/{alarm_id}/history")
async def get_alarm_history(request: Request, alarm_id: str):
    """Get alarm history"""
    alarm_manager = request.app.state.alarm_manager
    
    alarm = await alarm_manager.storage.get_alarm(alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
        
    history = await alarm_manager.storage.get_alarm_history(alarm_id)
    
    return {'history': history}


class SeverityRequest(BaseModel):
    severity: str
    user: Optional[str] = None


class RunbookRequest(BaseModel):
    runbook_id: Optional[str]
    user: Optional[str] = None


class EscalationRequest(BaseModel):
    escalation_policy: Optional[str]
    user: Optional[str] = None


class WatcherRequest(BaseModel):
    watcher: str
    user: Optional[str] = None


class WatcherDeleteRequest(BaseModel):
    user: Optional[str] = None


@router.post("/{alarm_id}/severity")
async def update_severity(request: Request, alarm_id: str, data: SeverityRequest):
    """Update alarm severity"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.update_severity(alarm_id, data.severity, data.user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alarm_id}/runbook")
async def update_runbook(request: Request, alarm_id: str, data: RunbookRequest):
    """Update alarm runbook"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.update_runbook(alarm_id, data.runbook_id, data.user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alarm_id}/escalation")
async def update_escalation_policy(request: Request, alarm_id: str, data: EscalationRequest):
    """Update alarm escalation policy"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.update_escalation_policy(alarm_id, data.escalation_policy, data.user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alarm_id}/watchers")
async def add_watcher(request: Request, alarm_id: str, data: WatcherRequest):
    """Add watcher to alarm"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        alarm = await alarm_manager.add_watcher(alarm_id, data.watcher, data.user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{alarm_id}/watchers/{watcher}")
async def remove_watcher(request: Request, alarm_id: str, watcher: str, data: WatcherDeleteRequest = None):
    """Remove watcher from alarm"""
    alarm_manager = request.app.state.alarm_manager
    
    try:
        user = data.user if data else None
        alarm = await alarm_manager.remove_watcher(alarm_id, watcher, user)
        return alarm
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

