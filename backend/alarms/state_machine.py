"""
Alarm State Machine
Manages alarm state transitions per docs/alarm.md
"""
import logging
from typing import Optional, Set, Dict
from datetime import datetime, timedelta


logger = logging.getLogger('overwatch.alarms.state_machine')


class AlarmStateMachine:
    """
    Manages alarm lifecycle state transitions
    
    States: NEW → TRIAGE → ACTIVE → CONTAINED → RESOLVED → CLOSED
    Additional: SNOOZED, SUPPRESSED
    """
    
    # Valid states
    STATES = {'NEW', 'TRIAGE', 'ACTIVE', 'CONTAINED', 'RESOLVED', 'CLOSED', 'SNOOZED', 'SUPPRESSED'}
    
    # Valid transitions (from_state -> set of allowed to_states)
    TRANSITIONS: Dict[str, Set[str]] = {
        'NEW': {'TRIAGE', 'SUPPRESSED'},
        'TRIAGE': {'ACTIVE', 'SNOOZED', 'SUPPRESSED', 'RESOLVED'},
        'SNOOZED': {'TRIAGE', 'SUPPRESSED'},
        'ACTIVE': {'CONTAINED', 'RESOLVED', 'SUPPRESSED'},
        'CONTAINED': {'RESOLVED', 'ACTIVE', 'SUPPRESSED'},
        'RESOLVED': {'CLOSED', 'ACTIVE', 'SUPPRESSED'},  # Re-open if needed
        'CLOSED': set(),  # Terminal state
        'SUPPRESSED': set()  # Terminal state
    }
    
    # SLA timers by severity (in minutes)
    SLA_TIMERS = {
        'critical': {'triage': 2, 'active': 5, 'contained': 15, 'resolved': 60},
        'major': {'triage': 5, 'active': 15, 'contained': 30, 'resolved': 120},
        'minor': {'triage': 15, 'active': 60, 'contained': 240, 'resolved': 480},
        'info': {'triage': 60, 'active': 240, 'contained': 480, 'resolved': 1440}
    }
    
    @classmethod
    def is_valid_state(cls, state: str) -> bool:
        """Check if state is valid"""
        return state in cls.STATES
        
    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        """Check if transition is allowed"""
        if from_state not in cls.TRANSITIONS:
            return False
        return to_state in cls.TRANSITIONS[from_state]
        
    @classmethod
    def get_allowed_transitions(cls, from_state: str) -> Set[str]:
        """Get allowed transitions from a state"""
        return cls.TRANSITIONS.get(from_state, set())
        
    @classmethod
    def calculate_sla_deadline(cls, severity: str, state: str, created_at: str) -> Optional[str]:
        """Calculate SLA deadline for current state"""
        if severity not in cls.SLA_TIMERS:
            return None
            
        state_key = state.lower()
        if state_key not in cls.SLA_TIMERS[severity]:
            return None
            
        minutes = cls.SLA_TIMERS[severity][state_key]
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        deadline = created + timedelta(minutes=minutes)
        
        return deadline.isoformat()
        
    @classmethod
    def is_sla_breached(cls, current_sla_deadline: Optional[str]) -> bool:
        """Check if SLA is breached"""
        if not current_sla_deadline:
            return False
            
        deadline = datetime.fromisoformat(current_sla_deadline.replace('Z', '+00:00'))
        return datetime.utcnow() > deadline
        
    @classmethod
    def get_escalation_severity(cls, current_severity: str) -> str:
        """Get escalated severity level"""
        escalation_map = {
            'info': 'minor',
            'minor': 'major',
            'major': 'critical',
            'critical': 'critical'  # Already max
        }
        return escalation_map.get(current_severity, current_severity)
        
    @classmethod
    def validate_transition(
        cls,
        from_state: str,
        to_state: str,
        user: Optional[str] = None,
        note: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a transition request
        
        Returns:
            (is_valid, error_message)
        """
        if not cls.is_valid_state(from_state):
            return False, f"Invalid current state: {from_state}"
            
        if not cls.is_valid_state(to_state):
            return False, f"Invalid target state: {to_state}"
            
        if not cls.can_transition(from_state, to_state):
            return False, f"Cannot transition from {from_state} to {to_state}"
            
        # State-specific validations
        if to_state == 'ACTIVE' and not user:
            return False, "Active state requires assignee"
            
        if to_state in {'RESOLVED', 'CLOSED'} and not note:
            return False, f"{to_state} state requires resolution note"
            
        return True, None

