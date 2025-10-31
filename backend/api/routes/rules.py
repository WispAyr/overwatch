"""
Rules API Routes
"""
from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional, List

from rules.dsl_parser import DSLParser
from rules.schemas import Rule


router = APIRouter(prefix="/api/rules", tags=["rules"])


class RuleCreateRequest(BaseModel):
    yaml_content: str


class RuleUpdateRequest(BaseModel):
    yaml_content: str
    enabled: Optional[bool] = None


@router.get("")
async def list_rules(request: Request):
    """List all rules"""
    rules_engine = request.app.state.rules_engine
    
    rules = rules_engine.list_rules()
    
    return {
        'rules': [r.dict() for r in rules],
        'total': len(rules)
    }


@router.get("/{rule_id}")
async def get_rule(request: Request, rule_id: str, as_yaml: bool = False):
    """Get a rule by ID"""
    rules_engine = request.app.state.rules_engine
    
    rule = rules_engine.get_rule(rule_id)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    if as_yaml:
        return {
            'yaml': DSLParser.to_yaml(rule)
        }
    
    return rule.dict()


@router.put("/{rule_id}")
async def update_rule(request: Request, rule_id: str, data: RuleUpdateRequest):
    """Update a rule"""
    rules_engine = request.app.state.rules_engine
    
    try:
        # Parse YAML DSL
        rule = DSLParser.parse_yaml(data.yaml_content)
        rule.id = rule_id  # Ensure ID matches
        
        if data.enabled is not None:
            rule.enabled = data.enabled
            
        # Add/update in engine
        rules_engine.add_rule(rule)
        
        return rule.dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("")
async def create_rule(request: Request, data: RuleCreateRequest):
    """Create a new rule"""
    rules_engine = request.app.state.rules_engine
    
    try:
        # Parse YAML DSL
        rule = DSLParser.parse_yaml(data.yaml_content)
        
        # Add to engine
        rules_engine.add_rule(rule)
        
        return rule.dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rule_id}")
async def delete_rule(request: Request, rule_id: str):
    """Delete a rule"""
    rules_engine = request.app.state.rules_engine
    
    rule = rules_engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    rules_engine.remove_rule(rule_id)
    
    return {"status": "ok", "rule_id": rule_id}


@router.post("/{rule_id}/enable")
async def enable_rule(request: Request, rule_id: str):
    """Enable a rule"""
    rules_engine = request.app.state.rules_engine
    
    rule = rules_engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    rule.enabled = True
    rules_engine.add_rule(rule)
    
    return rule.dict()


@router.post("/{rule_id}/disable")
async def disable_rule(request: Request, rule_id: str):
    """Disable a rule"""
    rules_engine = request.app.state.rules_engine
    
    rule = rules_engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    rule.enabled = False
    rules_engine.add_rule(rule)
    
    return rule.dict()


