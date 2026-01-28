"""
NodeRegistry - Registry of available workflow nodes

Manages the catalog of node types available in the visual editor.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseNodeHandler(ABC):
    """Abstract base class for node handlers"""
    
    # Node metadata
    node_type: str = ""
    title: str = ""
    category: str = "action"
    description: str = ""
    color: str = "#666666"
    
    # Port definitions
    inputs: List[Dict] = []
    outputs: List[Dict] = []
    
    # Properties/configuration schema
    properties: List[Dict] = []
    
    @abstractmethod
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        """
        Execute the node logic.
        
        Args:
            config: Node configuration/properties
            input_data: Data from connected input
            context: Execution context
            
        Returns:
            Output data to pass to connected nodes
        """
        pass
    
    @classmethod
    def get_schema(cls) -> Dict:
        """Get the node schema for the visual editor"""
        return {
            'type': cls.node_type,
            'title': cls.title,
            'category': cls.category,
            'description': cls.description,
            'color': cls.color,
            'inputs': cls.inputs,
            'outputs': cls.outputs,
            'properties': cls.properties,
        }


class NodeRegistry:
    """Registry for workflow node types"""
    
    _handlers: Dict[str, Type[BaseNodeHandler]] = {}
    
    @classmethod
    def register(cls, handler_class: Type[BaseNodeHandler]) -> Type[BaseNodeHandler]:
        """
        Register a node handler class.
        
        Can be used as a decorator:
        @NodeRegistry.register
        class MyNodeHandler(BaseNodeHandler):
            ...
        """
        cls._handlers[handler_class.node_type] = handler_class
        logger.debug(f"Registered node handler: {handler_class.node_type}")
        return handler_class
    
    @classmethod
    def get_node_handler(cls, node_type: str) -> Optional[BaseNodeHandler]:
        """
        Get a node handler instance by type.
        
        Args:
            node_type: The node type string
            
        Returns:
            Instance of the node handler, or None if not found
        """
        handler_class = cls._handlers.get(node_type)
        if handler_class:
            return handler_class()
        return None
    
    @classmethod
    def get_all_node_types(cls) -> List[Dict]:
        """
        Get all registered node types with their schemas.
        
        Returns:
            List of node schemas
        """
        return [
            handler.get_schema()
            for handler in cls._handlers.values()
        ]
    
    @classmethod
    def get_node_types_by_category(cls) -> Dict[str, List[Dict]]:
        """
        Get node types organized by category.
        
        Returns:
            Dict mapping category names to lists of node schemas
        """
        categories = {}
        for handler in cls._handlers.values():
            category = handler.category
            if category not in categories:
                categories[category] = []
            categories[category].append(handler.get_schema())
        return categories


# ============================================
# Built-in Node Handlers
# ============================================

@NodeRegistry.register
class ManualTriggerNode(BaseNodeHandler):
    """Manual trigger node - starts workflow manually"""
    node_type = "trigger/manual"
    title = "Manual Trigger"
    category = "trigger"
    description = "Start workflow manually"
    color = "#8855ff"
    
    inputs = []
    outputs = [{"name": "trigger", "type": "object"}]
    properties = [
        {"name": "description", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        return {
            'triggered_at': str(context.execution.started_at),
            'trigger_data': context.trigger_data,
            'user': str(context.execution.triggered_by) if context.execution.triggered_by else None
        }


@NodeRegistry.register
class WebhookTriggerNode(BaseNodeHandler):
    """Webhook trigger node - starts workflow via HTTP webhook"""
    node_type = "trigger/webhook"
    title = "Webhook Trigger"
    category = "trigger"
    description = "Start workflow via HTTP webhook"
    color = "#8855ff"
    
    inputs = []
    outputs = [{"name": "request", "type": "object"}]
    properties = [
        {"name": "method", "type": "select", "options": ["GET", "POST", "PUT", "DELETE"], "default": "POST"},
        {"name": "path", "type": "string", "default": ""},
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        return context.trigger_data


@NodeRegistry.register
class ScheduleTriggerNode(BaseNodeHandler):
    """Schedule trigger node - starts workflow on a schedule"""
    node_type = "trigger/schedule"
    title = "Schedule Trigger"
    category = "trigger"
    description = "Start workflow on a schedule"
    color = "#8855ff"
    
    inputs = []
    outputs = [{"name": "trigger", "type": "object"}]
    properties = [
        {"name": "cron", "type": "string", "default": "0 * * * *"},
        {"name": "timezone", "type": "string", "default": "UTC"},
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        return {
            'scheduled_at': str(context.execution.started_at),
            'cron': config.get('cron', ''),
        }


@NodeRegistry.register
class ConditionNode(BaseNodeHandler):
    """Condition/If node - branches based on condition"""
    node_type = "logic/condition"
    title = "If/Condition"
    category = "logic"
    description = "Branch workflow based on condition"
    color = "#ff8844"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [
        {"name": "true", "type": "object"},
        {"name": "false", "type": "object"}
    ]
    properties = [
        {"name": "field", "type": "string", "default": ""},
        {"name": "operator", "type": "select", "options": ["equals", "not_equals", "contains", "greater_than", "less_than", "is_empty", "is_not_empty"], "default": "equals"},
        {"name": "value", "type": "string", "default": ""},
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        field = config.get('field', '')
        operator = config.get('operator', 'equals')
        compare_value = config.get('value', '')
        
        # Get field value from input
        if input_data and isinstance(input_data, dict):
            field_value = input_data.get(field)
        else:
            field_value = input_data
        
        # Evaluate condition
        result = False
        if operator == 'equals':
            result = str(field_value) == str(compare_value)
        elif operator == 'not_equals':
            result = str(field_value) != str(compare_value)
        elif operator == 'contains':
            result = str(compare_value) in str(field_value)
        elif operator == 'greater_than':
            try:
                result = float(field_value) > float(compare_value)
            except (ValueError, TypeError):
                result = False
        elif operator == 'less_than':
            try:
                result = float(field_value) < float(compare_value)
            except (ValueError, TypeError):
                result = False
        elif operator == 'is_empty':
            result = not field_value
        elif operator == 'is_not_empty':
            result = bool(field_value)
        
        return {
            'condition_result': result,
            'input': input_data
        }


@NodeRegistry.register
class MergeNode(BaseNodeHandler):
    """Merge node - combines multiple inputs"""
    node_type = "logic/merge"
    title = "Merge"
    category = "logic"
    description = "Merge multiple inputs into one"
    color = "#ff8844"
    
    inputs = [
        {"name": "input1", "type": "object"},
        {"name": "input2", "type": "object"}
    ]
    outputs = [{"name": "merged", "type": "object"}]
    properties = [
        {"name": "mode", "type": "select", "options": ["combine", "append", "overwrite"], "default": "combine"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        # In practice, we'd need to get multiple inputs
        # For now, just pass through
        return input_data


@NodeRegistry.register
class SetVariableNode(BaseNodeHandler):
    """Set variable node - sets a workflow variable"""
    node_type = "logic/set_variable"
    title = "Set Variable"
    category = "logic"
    description = "Set a workflow variable"
    color = "#ff8844"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "output", "type": "object"}]
    properties = [
        {"name": "variable_name", "type": "string", "default": "myVar"},
        {"name": "value", "type": "string", "default": ""},
        {"name": "use_input", "type": "boolean", "default": True}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        var_name = config.get('variable_name', 'myVar')
        if config.get('use_input', True):
            value = input_data
        else:
            value = config.get('value', '')
        
        context.variables[var_name] = value
        return input_data


@NodeRegistry.register
class HTTPRequestNode(BaseNodeHandler):
    """HTTP Request node - makes HTTP API calls"""
    node_type = "action/http_request"
    title = "HTTP Request"
    category = "action"
    description = "Make HTTP API requests"
    color = "#44aa88"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "response", "type": "object"}]
    properties = [
        {"name": "url", "type": "string", "default": ""},
        {"name": "method", "type": "select", "options": ["GET", "POST", "PUT", "PATCH", "DELETE"], "default": "GET"},
        {"name": "headers", "type": "json", "default": "{}"},
        {"name": "body", "type": "json", "default": "{}"},
        {"name": "timeout", "type": "number", "default": 30}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        import requests
        import json
        
        url = config.get('url', '')
        method = config.get('method', 'GET')
        headers = config.get('headers', {})
        body = config.get('body', {})
        timeout = config.get('timeout', 30)
        
        if isinstance(headers, str):
            headers = json.loads(headers)
        if isinstance(body, str):
            body = json.loads(body)
        
        # Make the request
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body if method in ['POST', 'PUT', 'PATCH'] else None,
            params=body if method == 'GET' else None,
            timeout=timeout
        )
        
        try:
            response_body = response.json()
        except:
            response_body = response.text
        
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response_body
        }


@NodeRegistry.register
class TransformDataNode(BaseNodeHandler):
    """Transform data node - transform/map data"""
    node_type = "transform/data"
    title = "Transform Data"
    category = "logic"
    description = "Transform and map data"
    color = "#ff8844"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "output", "type": "object"}]
    properties = [
        {"name": "expression", "type": "code", "default": "return input;"},
        {"name": "language", "type": "select", "options": ["json_path", "javascript"], "default": "json_path"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        # Simple pass-through for now
        # In production, implement JSONPath or safe JavaScript evaluation
        return input_data


@NodeRegistry.register
class DebugNode(BaseNodeHandler):
    """Debug node - log data for debugging"""
    node_type = "action/debug"
    title = "Debug"
    category = "action"
    description = "Log data for debugging"
    color = "#888888"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "output", "type": "object"}]
    properties = [
        {"name": "message", "type": "string", "default": "Debug output"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from ..models import ExecutionLog
        
        message = config.get('message', 'Debug output')
        
        ExecutionLog.objects.create(
            execution=context.execution,
            node_id='debug',
            node_type='action/debug',
            node_title='Debug',
            level='debug',
            message=message,
            data={'input': str(input_data)[:1000]}
        )
        
        return input_data
