"""
Alarm Manager
Manages alarm lifecycle, correlation, and state transitions
"""
import logging
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from .storage import AlarmStorage
from .state_machine import AlarmStateMachine


logger = logging.getLogger('overwatch.alarms.manager')


class AlarmManager:
    """Manages alarms and correlation with events"""
    
    def __init__(self):
        self.storage = AlarmStorage()
        self.state_machine = AlarmStateMachine()
        self._callbacks = []
        
    async def initialize(self):
        """Initialize alarm manager"""
        logger.info("Initializing alarm manager...")
        await self.storage.initialize()
        
    def subscribe(self, callback):
        """Subscribe to alarm updates"""
        self._callbacks.append(callback)
        
    async def _notify_subscribers(self, alarm: Dict[str, Any], action: str):
        """Notify subscribers of alarm changes"""
        for callback in self._callbacks:
            try:
                await callback(alarm, action)
            except Exception as e:
                logger.error(f"Error in alarm callback: {e}")
                
    def compute_group_key(self, event: Dict[str, Any]) -> str:
        """
        Compute group key for event correlation
        
        Groups by: tenant:site:area:type
        """
        parts = []
        
        # Tenant and site
        parts.append(event.get('tenant', 'default'))
        parts.append(event.get('site', 'default'))
        
        # Area/location
        location = event.get('location', {})
        area = location.get('area_id') or location.get('floor', 'unknown')
        parts.append(str(area))
        
        # Event type
        source = event.get('source', {})
        event_type = source.get('subtype') or source.get('type', 'unknown')
        parts.append(event_type)
        
        return ':'.join(parts)
        
    async def process_event(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Process an event and create or update alarm
        
        Returns:
            alarm_id if alarm was created/updated, None otherwise
        """
        # Compute group key
        group_key = self.compute_group_key(event)
        
        # Check for existing open alarm with same group_key
        existing = await self.storage.get_alarm_by_group_key(group_key)
        
        if existing:
            # Update existing alarm
            alarm_id = existing['id']
            
            # Add event to alarm
            await self.storage.add_event_to_alarm(alarm_id, event['id'])
            
            # Update confidence (average)
            event_confidence = event.get('attributes', {}).get('confidence', 0.5)
            current_confidence = existing.get('confidence', 0.5)
            new_confidence = (current_confidence + event_confidence) / 2
            
            # Update alarm
            updates = {
                'confidence': new_confidence,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Auto-escalate severity if confidence is high
            if new_confidence > 0.85 and existing['severity'] != 'critical':
                new_severity = self.state_machine.get_escalation_severity(existing['severity'])
                if new_severity != existing['severity']:
                    updates['severity'] = new_severity
                    logger.info(f"Auto-escalated alarm {alarm_id} to {new_severity}")
                    
            await self.storage.update_alarm(alarm_id, updates)
            
            # Add history
            await self.storage.add_history_entry(
                alarm_id,
                action='event_correlated',
                note=f"Event {event['id']} correlated"
            )
            
            # Get updated alarm
            alarm = await self.storage.get_alarm(alarm_id)
            await self._notify_subscribers(alarm, 'updated')
            
            logger.info(f"Updated alarm {alarm_id} with event {event['id']}")
            return alarm_id
            
        else:
            # Create new alarm
            alarm_id = f"alm_{uuid.uuid4().hex[:12]}"
            
            # Determine severity from event
            severity = event.get('severity', 'info')
            
            # Create alarm
            created_at = datetime.utcnow().isoformat()
            alarm = {
                'id': alarm_id,
                'group_key': group_key,
                'tenant': event.get('tenant'),
                'site': event.get('site'),
                'severity': severity,
                'state': 'NEW',
                'created_at': created_at,
                'updated_at': created_at,
                'current_sla_deadline': self.state_machine.calculate_sla_deadline(
                    severity, 'triage', created_at
                ),
                'confidence': event.get('attributes', {}).get('confidence', 0.5),
                'assignee': None,
                'runbook_id': None,
                'escalation_policy': None,
                'watchers': [],
                'links': {
                    'map_view': f"/ui/map?alarm={alarm_id}",
                    'live_feeds': []
                },
                'attributes': {
                    'initial_event_id': event['id'],
                    'event_type': event.get('source', {}).get('subtype'),
                    'location': event.get('location', {})
                }
            }
            
            await self.storage.create_alarm(alarm)
            await self.storage.add_event_to_alarm(alarm_id, event['id'])
            
            # Add history
            await self.storage.add_history_entry(
                alarm_id,
                action='created',
                to_state='NEW',
                note=f"Created from event {event['id']}"
            )
            
            await self._notify_subscribers(alarm, 'created')
            
            logger.info(f"Created new alarm {alarm_id} from event {event['id']}")
            return alarm_id
            
    async def transition_alarm(
        self,
        alarm_id: str,
        to_state: str,
        user: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transition alarm to new state
        
        Returns:
            Updated alarm
        """
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        from_state = alarm['state']
        
        # Validate transition
        valid, error = self.state_machine.validate_transition(
            from_state, to_state, user, note
        )
        
        if not valid:
            raise ValueError(error)
            
        # Update alarm state
        updates = {
            'state': to_state,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update SLA deadline for new state
        new_deadline = self.state_machine.calculate_sla_deadline(
            alarm['severity'], to_state, alarm['created_at']
        )
        if new_deadline:
            updates['current_sla_deadline'] = new_deadline
            
        await self.storage.update_alarm(alarm_id, updates)
        
        # Add history
        await self.storage.add_history_entry(
            alarm_id,
            action='transition',
            from_state=from_state,
            to_state=to_state,
            user=user,
            note=note
        )
        
        # Get updated alarm
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'transitioned')
        
        logger.info(f"Transitioned alarm {alarm_id} from {from_state} to {to_state}")
        return alarm
        
    async def acknowledge_alarm(self, alarm_id: str, user: str) -> Dict[str, Any]:
        """Acknowledge an alarm (transition NEW -> TRIAGE)"""
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        if alarm['state'] == 'NEW':
            return await self.transition_alarm(
                alarm_id,
                'TRIAGE',
                user=user,
                note=f"Acknowledged by {user}"
            )
        return alarm
        
    async def assign_alarm(self, alarm_id: str, assignee: str, user: str) -> Dict[str, Any]:
        """Assign an alarm to an operator"""
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        await self.storage.update_alarm(alarm_id, {'assignee': assignee})
        
        await self.storage.add_history_entry(
            alarm_id,
            action='assigned',
            user=user,
            note=f"Assigned to {assignee}"
        )
        
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'assigned')
        
        logger.info(f"Assigned alarm {alarm_id} to {assignee}")
        return alarm
        
    async def add_note(
        self,
        alarm_id: str,
        note: str,
        user: Optional[str] = None
    ):
        """Add a note to an alarm"""
        await self.storage.add_history_entry(
            alarm_id,
            action='note_added',
            user=user,
            note=note
        )
        
    async def get_alarm(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """Get alarm by ID with correlated events"""
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            return None
            
        # Get correlated events
        event_ids = await self.storage.get_alarm_events(alarm_id)
        alarm['correlated_events'] = event_ids
        
        return alarm
        
    async def get_alarm_with_history(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """Get alarm with full history"""
        alarm = await self.get_alarm(alarm_id)
        if not alarm:
            return None
            
        history = await self.storage.get_alarm_history(alarm_id)
        alarm['history'] = history
        
        return alarm
        
    async def query_alarms(self, **filters) -> List[Dict[str, Any]]:
        """Query alarms with filters"""
        return await self.storage.query_alarms(**filters)
        
    async def count_alarms(self, **filters) -> int:
        """Count alarms with filters"""
        return await self.storage.count_alarms(**filters)
        
    async def update_severity(
        self,
        alarm_id: str,
        severity: str,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update alarm severity
        
        Args:
            alarm_id: Alarm ID
            severity: New severity (info, minor, major, critical)
            user: User making the change
            
        Returns:
            Updated alarm
        """
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        valid_severities = ['info', 'minor', 'major', 'critical']
        if severity not in valid_severities:
            raise ValueError(f"Invalid severity: {severity}. Must be one of {valid_severities}")
            
        old_severity = alarm['severity']
        
        await self.storage.update_alarm(alarm_id, {'severity': severity})
        
        await self.storage.add_history_entry(
            alarm_id,
            action='severity_changed',
            user=user,
            note=f"Severity changed from {old_severity} to {severity}"
        )
        
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'updated')
        
        logger.info(f"Updated alarm {alarm_id} severity from {old_severity} to {severity}")
        return alarm
        
    async def update_runbook(
        self,
        alarm_id: str,
        runbook_id: Optional[str],
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update alarm runbook reference
        
        Args:
            alarm_id: Alarm ID
            runbook_id: Runbook ID or None to clear
            user: User making the change
            
        Returns:
            Updated alarm
        """
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        old_runbook = alarm.get('runbook_id')
        
        await self.storage.update_alarm(alarm_id, {'runbook_id': runbook_id})
        
        if runbook_id:
            note = f"Runbook set to {runbook_id}"
            if old_runbook:
                note = f"Runbook changed from {old_runbook} to {runbook_id}"
        else:
            note = "Runbook cleared"
            
        await self.storage.add_history_entry(
            alarm_id,
            action='runbook_updated',
            user=user,
            note=note
        )
        
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'updated')
        
        logger.info(f"Updated alarm {alarm_id} runbook to {runbook_id}")
        return alarm
        
    async def update_escalation_policy(
        self,
        alarm_id: str,
        escalation_policy: Optional[str],
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update alarm escalation policy
        
        Args:
            alarm_id: Alarm ID
            escalation_policy: Escalation policy name or None to clear
            user: User making the change
            
        Returns:
            Updated alarm
        """
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        old_policy = alarm.get('escalation_policy')
        
        await self.storage.update_alarm(alarm_id, {'escalation_policy': escalation_policy})
        
        if escalation_policy:
            note = f"Escalation policy set to {escalation_policy}"
            if old_policy:
                note = f"Escalation policy changed from {old_policy} to {escalation_policy}"
        else:
            note = "Escalation policy cleared"
            
        await self.storage.add_history_entry(
            alarm_id,
            action='escalation_updated',
            user=user,
            note=note
        )
        
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'updated')
        
        logger.info(f"Updated alarm {alarm_id} escalation policy to {escalation_policy}")
        return alarm
        
    async def add_watcher(
        self,
        alarm_id: str,
        watcher: str,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a watcher to an alarm
        
        Args:
            alarm_id: Alarm ID
            watcher: Username to add as watcher
            user: User making the change
            
        Returns:
            Updated alarm
        """
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        watchers = alarm.get('watchers', [])
        
        if watcher in watchers:
            raise ValueError(f"User {watcher} is already watching this alarm")
            
        watchers.append(watcher)
        
        await self.storage.update_alarm(alarm_id, {'watchers': json.dumps(watchers)})
        
        await self.storage.add_history_entry(
            alarm_id,
            action='watcher_added',
            user=user,
            note=f"Added {watcher} as watcher"
        )
        
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'updated')
        
        logger.info(f"Added watcher {watcher} to alarm {alarm_id}")
        return alarm
        
    async def remove_watcher(
        self,
        alarm_id: str,
        watcher: str,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a watcher from an alarm
        
        Args:
            alarm_id: Alarm ID
            watcher: Username to remove from watchers
            user: User making the change
            
        Returns:
            Updated alarm
        """
        alarm = await self.storage.get_alarm(alarm_id)
        if not alarm:
            raise ValueError(f"Alarm {alarm_id} not found")
            
        watchers = alarm.get('watchers', [])
        
        if watcher not in watchers:
            raise ValueError(f"User {watcher} is not watching this alarm")
            
        watchers.remove(watcher)
        
        await self.storage.update_alarm(alarm_id, {'watchers': json.dumps(watchers)})
        
        await self.storage.add_history_entry(
            alarm_id,
            action='watcher_removed',
            user=user,
            note=f"Removed {watcher} from watchers"
        )
        
        alarm = await self.storage.get_alarm(alarm_id)
        await self._notify_subscribers(alarm, 'updated')
        
        logger.info(f"Removed watcher {watcher} from alarm {alarm_id}")
        return alarm
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.storage.cleanup()

