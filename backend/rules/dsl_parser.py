"""
DSL Parser for YAML-based rule definitions
"""
import yaml
import logging
from typing import Dict, Any, List
from pathlib import Path

from .schemas import Rule, RuleAction


logger = logging.getLogger('overwatch.rules.parser')


class DSLParser:
    """Parse YAML DSL into Rule objects"""
    
    @staticmethod
    def parse_yaml(yaml_content: str) -> Rule:
        """Parse YAML DSL into a Rule"""
        try:
            data = yaml.safe_load(yaml_content)
            return DSLParser._parse_rule(data)
        except Exception as e:
            logger.error(f"Error parsing DSL: {e}")
            raise ValueError(f"Invalid DSL syntax: {e}")
            
    @staticmethod
    def _parse_rule(data: Dict[str, Any]) -> Rule:
        """Parse rule data structure"""
        rule_id = data.get('rule', 'unnamed_rule')
        
        # Parse conditions
        when_block = data.get('when', {})
        conditions = DSLParser._parse_conditions(when_block)
        
        # Parse actions
        then_block = data.get('then', [])
        actions = DSLParser._parse_actions(then_block)
        
        # Parse suppress/cooldown
        suppress = data.get('suppress')
        
        rule = Rule(
            id=rule_id,
            name=rule_id,
            enabled=data.get('enabled', True),
            priority=data.get('priority', 10),
            conditions=conditions,
            actions=actions,
            suppress=suppress,
            metadata=data.get('metadata', {})
        )
        
        return rule
        
    @staticmethod
    def _parse_conditions(when_block: Dict[str, Any]) -> Dict[str, Any]:
        """Parse condition tree"""
        if 'all' in when_block:
            return {'all': when_block['all']}
        elif 'any' in when_block:
            return {'any': when_block['any']}
        else:
            # Single condition
            return {'all': [when_block]}
            
    @staticmethod
    def _parse_actions(then_block: List[Any]) -> List[RuleAction]:
        """Parse action definitions"""
        actions = []
        
        for action_def in then_block:
            if isinstance(action_def, dict):
                for action_type, config in action_def.items():
                    if action_type == 'correlate.by':
                        # Skip correlation (handled by AlarmManager)
                        continue
                    elif action_type == 'alarm.create_or_update':
                        actions.append(RuleAction(
                            type='alarm',
                            config=config if isinstance(config, dict) else {}
                        ))
                    elif action_type == 'notify':
                        actions.append(RuleAction(
                            type='notify',
                            config=config if isinstance(config, dict) else {}
                        ))
                    elif action_type == 'automation':
                        # Parse automation sub-actions
                        if isinstance(config, list):
                            for auto_action in config:
                                if isinstance(auto_action, dict):
                                    for key, val in auto_action.items():
                                        actions.append(RuleAction(
                                            type='automation',
                                            config={'action': key, 'params': val}
                                        ))
                        
        return actions
        
    @staticmethod
    def load_from_file(file_path: Path) -> Rule:
        """Load rule from YAML file"""
        with open(file_path, 'r') as f:
            return DSLParser.parse_yaml(f.read())
            
    @staticmethod
    def to_yaml(rule: Rule) -> str:
        """Convert Rule back to YAML DSL"""
        data = {
            'rule': rule.id,
            'enabled': rule.enabled,
            'priority': rule.priority,
            'when': rule.conditions,
            'then': [{'alarm.create_or_update': action.config} if action.type == 'alarm' else {action.type: action.config} for action in rule.actions],
        }
        
        if rule.suppress:
            data['suppress'] = rule.suppress
            
        return yaml.dump(data, default_flow_style=False)


