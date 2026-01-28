"""
Base Node - Abstract base class for all workflow nodes
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseNode(ABC):
    """
    Abstract base class for workflow nodes.
    
    All custom nodes should inherit from this class and implement
    the execute method.
    """
    
    # Node identification
    node_type: str = ""
    title: str = ""
    category: str = "action"
    description: str = ""
    
    # Visual properties
    color: str = "#666666"
    icon: str = ""
    
    # Port definitions
    # Each port: {"name": "port_name", "type": "object|string|number|boolean|array"}
    inputs: List[Dict] = []
    outputs: List[Dict] = []
    
    # Node properties/configuration schema
    # Each property: {"name": "prop_name", "type": "string|number|boolean|select|json|code", ...}
    properties: List[Dict] = []
    
    def __init__(self):
        """Initialize the node"""
        pass
    
    @abstractmethod
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        """
        Execute the node logic.
        
        This method must be implemented by all node subclasses.
        
        Args:
            config: Node configuration/properties set by the user
            input_data: Data received from connected input nodes
            context: Execution context with access to:
                     - context.execution: Current Execution object
                     - context.workflow: Current Workflow object
                     - context.trigger_data: Original trigger data
                     - context.credentials: Available credentials
                     - context.variables: Workflow variables
                     - context.get_input_data(node_id, input_index): Get input from specific slot
                     - context.set_output_data(node_id, output_index, data): Set output for specific slot
        
        Returns:
            Output data to pass to connected nodes
        
        Raises:
            Exception: Any exception will mark the node as failed
        """
        pass
    
    def validate_config(self, config: Dict) -> List[str]:
        """
        Validate node configuration.
        
        Override this to add custom validation logic.
        
        Args:
            config: Node configuration to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required properties
        for prop in self.properties:
            if prop.get('required', False):
                if prop['name'] not in config or not config[prop['name']]:
                    errors.append(f"Property '{prop['name']}' is required")
        
        return errors
    
    def get_default_config(self) -> Dict:
        """
        Get default configuration values.
        
        Returns:
            Dict with default values for all properties
        """
        return {
            prop['name']: prop.get('default', '')
            for prop in self.properties
        }
    
    @classmethod
    def get_schema(cls) -> Dict:
        """
        Get the node schema for the visual editor.
        
        Returns:
            Dict containing full node schema
        """
        return {
            'type': cls.node_type,
            'title': cls.title,
            'category': cls.category,
            'description': cls.description,
            'color': cls.color,
            'icon': cls.icon,
            'inputs': cls.inputs,
            'outputs': cls.outputs,
            'properties': cls.properties,
        }
    
    def pre_execute(self, config: Dict, context: Any) -> None:
        """
        Hook called before execute.
        
        Override to add pre-processing logic.
        """
        pass
    
    def post_execute(self, result: Any, context: Any) -> Any:
        """
        Hook called after execute.
        
        Override to add post-processing logic.
        
        Args:
            result: The result from execute()
            context: Execution context
            
        Returns:
            Modified result (or original result)
        """
        return result
    
    def on_error(self, error: Exception, context: Any) -> None:
        """
        Hook called when execute raises an exception.
        
        Override to add error handling logic.
        """
        pass


class CompositeNode(BaseNode):
    """
    A node that contains a sub-workflow.
    
    Useful for creating reusable workflow components.
    """
    
    category = "composite"
    
    def __init__(self):
        super().__init__()
        self.sub_workflow = None
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        """Execute the sub-workflow"""
        if not self.sub_workflow:
            return input_data
        
        # Execute sub-workflow with input data
        from ..services.execution_engine import ExecutionEngine
        
        # Create a sub-context for the nested execution
        # Implementation would go here
        
        return input_data
