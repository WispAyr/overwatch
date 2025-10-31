"""
Rule Schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class RuleCondition(BaseModel):
    """Rule condition definition"""
    field: str
    operator: str  # ==, !=, >, <, >=, <=, in, contains
    value: Any
    

class RuleAction(BaseModel):
    """Rule action definition"""
    type: str  # alarm, notify, automation, suppress
    config: Dict[str, Any]
    

class Rule(BaseModel):
    """Rule definition"""
    id: str
    name: str
    enabled: bool = True
    priority: int = 10
    conditions: Dict[str, Any]  # all, any, or condition tree
    actions: List[RuleAction]
    suppress: Optional[Dict[str, Any]] = None  # Cooldown config
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


