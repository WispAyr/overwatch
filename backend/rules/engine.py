"""
Rules Engine
Evaluates rules against event streams and triggers actions
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .schemas import Rule, RuleAction


logger = logging.getLogger('overwatch.rules.engine')


class RulesEngine:
    """
    Rules engine for event-driven automation
    Evaluates rules and triggers actions
    """
    
    def __init__(self, alarm_manager=None):
        self.rules: Dict[str, Rule] = {}
        self.alarm_manager = alarm_manager
        self.cooldowns: Dict[str, datetime] = {}  # rule_id -> last_triggered
        self.event_windows: Dict[str, List[Dict]] = defaultdict(list)  # For windowing
        self._notifiers = {}
        self._automation_handlers = {}
        
    async def initialize(self):
        """Initialize rules engine"""
        logger.info("Initializing rules engine...")
        
    def register_notifier(self, channel: str, handler):
        """Register a notification handler"""
        self._notifiers[channel] = handler
        logger.info(f"Registered notifier: {channel}")
        
    def register_automation(self, action_type: str, handler):
        """Register an automation handler"""
        self._automation_handlers[action_type] = handler
        logger.info(f"Registered automation: {action_type}")
        
    def add_rule(self, rule: Rule):
        """Add or update a rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added rule: {rule.id}")
        
    def remove_rule(self, rule_id: str):
        """Remove a rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed rule: {rule_id}")
            
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)
        
    def list_rules(self) -> List[Rule]:
        """List all rules"""
        return list(self.rules.values())
        
    async def evaluate_event(self, event: Dict[str, Any]):
        """
        Evaluate an event against all rules
        Trigger actions for matching rules
        """
        for rule in self.rules.values():
            if not rule.enabled:
                continue
                
            # Check cooldown
            if rule.id in self.cooldowns:
                cooldown_config = rule.suppress or {}
                cooldown_str = cooldown_config.get('cooldown', '0s')
                cooldown_secs = self._parse_duration(cooldown_str)
                
                if datetime.utcnow() < self.cooldowns[rule.id] + timedelta(seconds=cooldown_secs):
                    logger.debug(f"Rule {rule.id} in cooldown")
                    continue
                    
            # Evaluate conditions
            if await self._evaluate_conditions(rule.conditions, event):
                logger.info(f"Rule {rule.id} triggered for event {event['id']}")
                
                # Execute actions
                await self._execute_actions(rule, event)
                
                # Update cooldown
                if rule.suppress:
                    self.cooldowns[rule.id] = datetime.utcnow()
                    
    async def _evaluate_conditions(self, conditions: Dict[str, Any], event: Dict[str, Any]) -> bool:
        """Evaluate condition tree against event"""
        if 'all' in conditions:
            # All conditions must match
            for cond in conditions['all']:
                if not await self._evaluate_single_condition(cond, event):
                    return False
            return True
            
        elif 'any' in conditions:
            # Any condition must match
            for cond in conditions['any']:
                if await self._evaluate_single_condition(cond, event):
                    return True
            return False
            
        else:
            # Single condition
            return await self._evaluate_single_condition(conditions, event)
            
    async def _evaluate_single_condition(self, condition: Any, event: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        if isinstance(condition, str):
            # Parse simple condition like "event.type == 'crowd_density_high'"
            return self._eval_expression(condition, event)
        elif isinstance(condition, dict):
            # Dictionary condition
            for key, value in condition.items():
                event_value = self._get_nested(event, key)
                if event_value != value:
                    return False
            return True
        return False
        
    def _eval_expression(self, expr: str, event: Dict[str, Any]) -> bool:
        """Evaluate a simple expression"""
        try:
            # Simple expression parser for "field operator value"
            if '==' in expr:
                field, value = expr.split('==')
                field = field.strip()
                value = value.strip().strip('"\'')
                event_value = self._get_nested(event, field)
                return str(event_value) == value
            elif '>=' in expr:
                field, value = expr.split('>=')
                event_value = self._get_nested(event, field.strip())
                return float(event_value) >= float(value.strip())
            elif '>' in expr:
                field, value = expr.split('>')
                event_value = self._get_nested(event, field.strip())
                return float(event_value) > float(value.strip())
            # Add more operators as needed
            return False
        except Exception as e:
            logger.warning(f"Error evaluating expression '{expr}': {e}")
            return False
            
    def _get_nested(self, data: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
        
    async def _execute_actions(self, rule: Rule, event: Dict[str, Any]):
        """Execute rule actions"""
        for action in rule.actions:
            try:
                if action.type == 'alarm':
                    await self._action_alarm(action.config, event)
                elif action.type == 'notify':
                    await self._action_notify(action.config, event)
                elif action.type == 'automation':
                    await self._action_automation(action.config, event)
            except Exception as e:
                logger.error(f"Error executing action {action.type}: {e}")
                
    async def _action_alarm(self, config: Dict[str, Any], event: Dict[str, Any]):
        """Create or update alarm"""
        if self.alarm_manager:
            # Update event with alarm config
            event['severity'] = config.get('severity', event.get('severity', 'info'))
            event['runbook_id'] = config.get('runbook')
            
            # Let alarm manager handle correlation
            await self.alarm_manager.process_event(event)
        else:
            logger.warning("No alarm manager configured")
            
    async def _action_notify(self, config: Dict[str, Any], event: Dict[str, Any]):
        """Send notifications"""
        channels = config.get('channels', [])
        message = config.get('message', 'Alert triggered')
        
        # Template substitution
        message = self._substitute_template(message, event)
        
        for channel in channels:
            if isinstance(channel, str):
                # Parse "type:target" format
                if ':' in channel:
                    channel_type, target = channel.split(':', 1)
                else:
                    channel_type = channel
                    target = None
                    
                if channel_type in self._notifiers:
                    await self._notifiers[channel_type](message, target, event)
                else:
                    logger.warning(f"Unknown notification channel: {channel_type}")
                    
    async def _action_automation(self, config: Dict[str, Any], event: Dict[str, Any]):
        """Execute automation action"""
        action_name = config.get('action')
        params = config.get('params', {})
        
        if action_name in self._automation_handlers:
            await self._automation_handlers[action_name](params, event)
        else:
            logger.warning(f"Unknown automation action: {action_name}")
            
    def _substitute_template(self, template: str, event: Dict[str, Any]) -> str:
        """Substitute {{field}} placeholders in template"""
        import re
        
        def replace_match(match):
            field = match.group(1)
            value = self._get_nested(event, field)
            return str(value) if value is not None else ''
            
        return re.sub(r'\{\{(.+?)\}\}', replace_match, template)
        
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '30s', '2m', '1h' to seconds"""
        import re
        match = re.match(r'(\d+)([smh])', duration_str)
        if not match:
            return 0
            
        value, unit = match.groups()
        value = int(value)
        
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
            
        return 0
        
    async def cleanup(self):
        """Cleanup resources"""
        pass


