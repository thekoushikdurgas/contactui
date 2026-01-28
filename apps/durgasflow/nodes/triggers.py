"""
Trigger Nodes - Workflow trigger nodes

These nodes start workflow execution based on various events.
"""

from typing import Dict, Any
from ..services.node_registry import NodeRegistry, BaseNodeHandler


@NodeRegistry.register
class EventTriggerNode(BaseNodeHandler):
    """Event trigger node - starts workflow on application events"""
    node_type = "trigger/event"
    title = "Event Trigger"
    category = "trigger"
    description = "Start workflow when an event occurs in DocsAI"
    color = "#8855ff"
    
    inputs = []
    outputs = [{"name": "event", "type": "object"}]
    properties = [
        {
            "name": "event_type",
            "type": "select",
            "options": [
                "page.created",
                "page.updated",
                "page.deleted",
                "endpoint.created",
                "endpoint.updated",
                "relationship.created",
                "execution.completed",
                "execution.failed"
            ],
            "default": "page.created"
        },
        {"name": "filter", "type": "json", "default": "{}"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        return {
            'event_type': config.get('event_type', ''),
            'event_data': context.trigger_data,
            'triggered_at': str(context.execution.started_at)
        }


@NodeRegistry.register
class IntervalTriggerNode(BaseNodeHandler):
    """Interval trigger node - runs workflow at regular intervals"""
    node_type = "trigger/interval"
    title = "Interval Trigger"
    category = "trigger"
    description = "Run workflow at regular intervals"
    color = "#8855ff"
    
    inputs = []
    outputs = [{"name": "trigger", "type": "object"}]
    properties = [
        {
            "name": "interval",
            "type": "number",
            "default": 60,
            "description": "Interval in seconds"
        },
        {
            "name": "unit",
            "type": "select",
            "options": ["seconds", "minutes", "hours", "days"],
            "default": "minutes"
        }
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        return {
            'interval': config.get('interval', 60),
            'unit': config.get('unit', 'minutes'),
            'triggered_at': str(context.execution.started_at)
        }


@NodeRegistry.register
class FormTriggerNode(BaseNodeHandler):
    """Form trigger node - starts workflow from a form submission"""
    node_type = "trigger/form"
    title = "Form Trigger"
    category = "trigger"
    description = "Start workflow from a form submission"
    color = "#8855ff"
    
    inputs = []
    outputs = [{"name": "form_data", "type": "object"}]
    properties = [
        {"name": "form_fields", "type": "json", "default": "[]"},
        {"name": "submit_button_text", "type": "string", "default": "Submit"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        return context.trigger_data
