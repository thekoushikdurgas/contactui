"""
Logic Nodes - Control flow and data transformation nodes

These nodes handle branching, loops, and data manipulation.
"""

import json
import logging
from typing import Dict, Any, List
from ..services.node_registry import NodeRegistry, BaseNodeHandler

logger = logging.getLogger(__name__)


@NodeRegistry.register
class SwitchNode(BaseNodeHandler):
    """Switch node - multi-way branching"""
    node_type = "logic/switch"
    title = "Switch"
    category = "logic"
    description = "Route to different outputs based on value"
    color = "#ff8844"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [
        {"name": "case_1", "type": "object"},
        {"name": "case_2", "type": "object"},
        {"name": "case_3", "type": "object"},
        {"name": "default", "type": "object"}
    ]
    properties = [
        {"name": "field", "type": "string", "default": ""},
        {"name": "case_1_value", "type": "string", "default": ""},
        {"name": "case_2_value", "type": "string", "default": ""},
        {"name": "case_3_value", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        field = config.get('field', '')
        
        # Get value to switch on
        if isinstance(input_data, dict) and field:
            value = str(input_data.get(field, ''))
        else:
            value = str(input_data)
        
        # Find matching case
        matched_case = 'default'
        for i in range(1, 4):
            case_value = str(config.get(f'case_{i}_value', ''))
            if value == case_value:
                matched_case = f'case_{i}'
                break
        
        return {
            'matched_case': matched_case,
            'value': value,
            'input': input_data
        }


@NodeRegistry.register
class LoopNode(BaseNodeHandler):
    """Loop node - iterate over array"""
    node_type = "logic/loop"
    title = "Loop/For Each"
    category = "logic"
    description = "Iterate over array items"
    color = "#ff8844"
    
    inputs = [{"name": "array", "type": "array"}]
    outputs = [
        {"name": "item", "type": "object"},
        {"name": "completed", "type": "object"}
    ]
    properties = [
        {"name": "array_field", "type": "string", "default": "items"},
        {"name": "max_iterations", "type": "number", "default": 100}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        array_field = config.get('array_field', 'items')
        max_iterations = config.get('max_iterations', 100)
        
        # Get array from input
        if isinstance(input_data, dict):
            items = input_data.get(array_field, [])
        elif isinstance(input_data, list):
            items = input_data
        else:
            items = [input_data]
        
        # Limit iterations
        items = items[:max_iterations]
        
        results = []
        for index, item in enumerate(items):
            results.append({
                'index': index,
                'item': item,
                'is_first': index == 0,
                'is_last': index == len(items) - 1
            })
        
        return {
            'items': results,
            'count': len(results)
        }


@NodeRegistry.register
class FilterNode(BaseNodeHandler):
    """Filter node - filter array items"""
    node_type = "logic/filter"
    title = "Filter"
    category = "logic"
    description = "Filter array items by condition"
    color = "#ff8844"
    
    inputs = [{"name": "array", "type": "array"}]
    outputs = [
        {"name": "matched", "type": "array"},
        {"name": "unmatched", "type": "array"}
    ]
    properties = [
        {"name": "field", "type": "string", "default": ""},
        {"name": "operator", "type": "select", "options": ["equals", "not_equals", "contains", "greater_than", "less_than"], "default": "equals"},
        {"name": "value", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        field = config.get('field', '')
        operator = config.get('operator', 'equals')
        compare_value = config.get('value', '')
        
        # Get array from input
        if isinstance(input_data, dict):
            items = input_data.get('items', [])
        elif isinstance(input_data, list):
            items = input_data
        else:
            items = [input_data]
        
        matched = []
        unmatched = []
        
        for item in items:
            # Get field value
            if isinstance(item, dict):
                item_value = item.get(field, '')
            else:
                item_value = item
            
            # Check condition
            passes = False
            if operator == 'equals':
                passes = str(item_value) == str(compare_value)
            elif operator == 'not_equals':
                passes = str(item_value) != str(compare_value)
            elif operator == 'contains':
                passes = str(compare_value) in str(item_value)
            elif operator == 'greater_than':
                try:
                    passes = float(item_value) > float(compare_value)
                except (ValueError, TypeError):
                    passes = False
            elif operator == 'less_than':
                try:
                    passes = float(item_value) < float(compare_value)
                except (ValueError, TypeError):
                    passes = False
            
            if passes:
                matched.append(item)
            else:
                unmatched.append(item)
        
        return {
            'matched': matched,
            'matched_count': len(matched),
            'unmatched': unmatched,
            'unmatched_count': len(unmatched)
        }


@NodeRegistry.register
class MapNode(BaseNodeHandler):
    """Map node - transform array items"""
    node_type = "logic/map"
    title = "Map/Transform Array"
    category = "logic"
    description = "Transform each item in an array"
    color = "#ff8844"
    
    inputs = [{"name": "array", "type": "array"}]
    outputs = [{"name": "transformed", "type": "array"}]
    properties = [
        {"name": "mapping", "type": "json", "default": '{"output_field": "input_field"}'},
        {"name": "include_original", "type": "boolean", "default": False}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        mapping = config.get('mapping', {})
        if isinstance(mapping, str):
            mapping = json.loads(mapping)
        
        include_original = config.get('include_original', False)
        
        # Get array from input
        if isinstance(input_data, dict):
            items = input_data.get('items', [])
        elif isinstance(input_data, list):
            items = input_data
        else:
            items = [input_data]
        
        transformed = []
        for item in items:
            new_item = {}
            
            if include_original and isinstance(item, dict):
                new_item.update(item)
            
            for output_field, input_field in mapping.items():
                if isinstance(item, dict):
                    new_item[output_field] = item.get(input_field, '')
                else:
                    new_item[output_field] = item
            
            transformed.append(new_item)
        
        return transformed


@NodeRegistry.register
class AggregateNode(BaseNodeHandler):
    """Aggregate node - aggregate array data"""
    node_type = "logic/aggregate"
    title = "Aggregate"
    category = "logic"
    description = "Aggregate array data (sum, avg, count, etc.)"
    color = "#ff8844"
    
    inputs = [{"name": "array", "type": "array"}]
    outputs = [{"name": "result", "type": "object"}]
    properties = [
        {"name": "field", "type": "string", "default": ""},
        {"name": "operation", "type": "select", "options": ["count", "sum", "avg", "min", "max", "first", "last"], "default": "count"},
        {"name": "group_by", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        field = config.get('field', '')
        operation = config.get('operation', 'count')
        group_by = config.get('group_by', '')
        
        # Get array from input
        if isinstance(input_data, dict):
            items = input_data.get('items', input_data.get('matched', []))
        elif isinstance(input_data, list):
            items = input_data
        else:
            items = [input_data]
        
        # Extract values
        values = []
        for item in items:
            if isinstance(item, dict):
                val = item.get(field, 0)
            else:
                val = item
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                values.append(0)
        
        # Calculate result
        if operation == 'count':
            result = len(items)
        elif operation == 'sum':
            result = sum(values)
        elif operation == 'avg':
            result = sum(values) / len(values) if values else 0
        elif operation == 'min':
            result = min(values) if values else 0
        elif operation == 'max':
            result = max(values) if values else 0
        elif operation == 'first':
            result = items[0] if items else None
        elif operation == 'last':
            result = items[-1] if items else None
        else:
            result = len(items)
        
        return {
            'result': result,
            'operation': operation,
            'field': field,
            'item_count': len(items)
        }


@NodeRegistry.register
class JoinNode(BaseNodeHandler):
    """Join node - join two arrays"""
    node_type = "logic/join"
    title = "Join Arrays"
    category = "logic"
    description = "Join two arrays by a common field"
    color = "#ff8844"
    
    inputs = [
        {"name": "left", "type": "array"},
        {"name": "right", "type": "array"}
    ]
    outputs = [{"name": "joined", "type": "array"}]
    properties = [
        {"name": "left_key", "type": "string", "default": "id"},
        {"name": "right_key", "type": "string", "default": "id"},
        {"name": "join_type", "type": "select", "options": ["inner", "left", "right", "full"], "default": "inner"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        left_key = config.get('left_key', 'id')
        right_key = config.get('right_key', 'id')
        
        # Get arrays - this would need both inputs
        # For now, just pass through
        return input_data


@NodeRegistry.register 
class SplitNode(BaseNodeHandler):
    """Split node - split text into array"""
    node_type = "logic/split"
    title = "Split Text"
    category = "logic"
    description = "Split text into an array by delimiter"
    color = "#ff8844"
    
    inputs = [{"name": "text", "type": "string"}]
    outputs = [{"name": "array", "type": "array"}]
    properties = [
        {"name": "delimiter", "type": "string", "default": ","},
        {"name": "trim", "type": "boolean", "default": True},
        {"name": "remove_empty", "type": "boolean", "default": True}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        delimiter = config.get('delimiter', ',')
        trim = config.get('trim', True)
        remove_empty = config.get('remove_empty', True)
        
        # Get text
        if isinstance(input_data, dict):
            text = str(input_data.get('text', ''))
        else:
            text = str(input_data)
        
        # Split
        parts = text.split(delimiter)
        
        if trim:
            parts = [p.strip() for p in parts]
        
        if remove_empty:
            parts = [p for p in parts if p]
        
        return parts
