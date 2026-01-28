"""
N8n Parser Service - Convert n8n workflows to LiteGraph format

This service handles the conversion of n8n workflow JSON files to the
LiteGraph format used by the durgasflow visual editor.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class N8nNodeMapping:
    """Mapping configuration for n8n to durgasflow node conversion"""
    n8n_type: str
    durgasflow_type: str
    category: str
    parameter_mappings: Dict[str, str]
    input_mappings: Dict[str, List[str]]
    output_mappings: Dict[str, List[str]]
    color: str = "#666666"


class N8nParser:
    """
    Parser for converting n8n workflow JSON to LiteGraph format
    """

    # N8n node type mappings to durgasflow equivalents
    NODE_MAPPINGS = {
        # Triggers
        'n8n-nodes-base.webhook': N8nNodeMapping(
            n8n_type='n8n-nodes-base.webhook',
            durgasflow_type='trigger/webhook',
            category='trigger',
            parameter_mappings={
                'httpMethod': 'method',
                'path': 'webhook_path',
                'responseMode': 'response_mode'
            },
            input_mappings={},
            output_mappings={'main': ['response']},
            color='#8855ff'
        ),

        'n8n-nodes-base.scheduleTrigger': N8nNodeMapping(
            n8n_type='n8n-nodes-base.scheduleTrigger',
            durgasflow_type='trigger/schedule',
            category='trigger',
            parameter_mappings={
                'rule': 'cron_expression',
                'timezone': 'timezone'
            },
            input_mappings={},
            output_mappings={'main': ['trigger']},
            color='#8855ff'
        ),

        # Actions
        'n8n-nodes-base.httpRequest': N8nNodeMapping(
            n8n_type='n8n-nodes-base.httpRequest',
            durgasflow_type='action/http_request',
            category='action',
            parameter_mappings={
                'method': 'method',
                'url': 'url',
                'sendHeaders': 'send_headers',
                'headerParameters': 'headers',
                'sendBody': 'send_body',
                'bodyParameters': 'body',
                'options': 'options'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['response']},
            color='#44aa88'
        ),

        'n8n-nodes-base.emailSend': N8nNodeMapping(
            n8n_type='n8n-nodes-base.emailSend',
            durgasflow_type='action/email',
            category='action',
            parameter_mappings={
                'toEmail': 'to',
                'subject': 'subject',
                'text': 'body',
                'html': 'html',
                'attachments': 'attachments'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['result']},
            color='#44aa88'
        ),

        'n8n-nodes-base.slack': N8nNodeMapping(
            n8n_type='n8n-nodes-base.slack',
            durgasflow_type='action/slack',
            category='action',
            parameter_mappings={
                'webhookUri': 'webhook_url',
                'text': 'message',
                'channel': 'channel',
                'username': 'username',
                'iconEmoji': 'icon_emoji'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['result']},
            color='#44aa88'
        ),

        # Logic
        'n8n-nodes-base.if': N8nNodeMapping(
            n8n_type='n8n-nodes-base.if',
            durgasflow_type='logic/condition',
            category='logic',
            parameter_mappings={
                'conditions': 'conditions',
                'combineOperation': 'combinator'
            },
            input_mappings={'main': ['input']},
            output_mappings={
                'main': ['true', 'false']
            },
            color='#ff8844'
        ),

        'n8n-nodes-base.code': N8nNodeMapping(
            n8n_type='n8n-nodes-base.code',
            durgasflow_type='logic/code',
            category='logic',
            parameter_mappings={
                'mode': 'mode',
                'jsCode': 'code'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['output']},
            color='#ff8844'
        ),

        'n8n-nodes-base.set': N8nNodeMapping(
            n8n_type='n8n-nodes-base.set',
            durgasflow_type='logic/set_variable',
            category='logic',
            parameter_mappings={
                'values': 'values',
                'options': 'options'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['output']},
            color='#ff8844'
        ),

        # AI Nodes (custom mapping)
        'n8n-nodes-langchain.chatOpenAi': N8nNodeMapping(
            n8n_type='n8n-nodes-langchain.chatOpenAi',
            durgasflow_type='ai/chat_completion',
            category='ai_agent',
            parameter_mappings={
                'model': 'model',
                'messages': 'messages',
                'temperature': 'temperature',
                'maxTokens': 'max_tokens'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['response']},
            color='#aa44ff'
        ),

        # Database nodes
        'n8n-nodes-base.postgres': N8nNodeMapping(
            n8n_type='n8n-nodes-base.postgres',
            durgasflow_type='action/database_query',
            category='action',
            parameter_mappings={
                'operation': 'operation',
                'query': 'query',
                'parameters': 'params'
            },
            input_mappings={'main': ['input']},
            output_mappings={'main': ['results']},
            color='#44aa88'
        ),

        # File operations
        'n8n-nodes-base.readBinaryFile': N8nNodeMapping(
            n8n_type='n8n-nodes-base.readBinaryFile',
            durgasflow_type='action/read_file',
            category='action',
            parameter_mappings={
                'fileName': 'filename',
                'options': 'options'
            },
            input_mappings={},
            output_mappings={'main': ['data']},
            color='#44aa88'
        ),

        'n8n-nodes-base.writeBinaryFile': N8nNodeMapping(
            n8n_type='n8n-nodes-base.writeBinaryFile',
            durgasflow_type='action/write_file',
            category='action',
            parameter_mappings={
                'fileName': 'filename',
                'options': 'options'
            },
            input_mappings={'main': ['data']},
            output_mappings={'main': ['result']},
            color='#44aa88'
        )
    }

    @classmethod
    def parse_n8n_workflow(cls, n8n_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert n8n workflow JSON to LiteGraph format

        Args:
            n8n_data: n8n workflow JSON data

        Returns:
            LiteGraph compatible graph data
        """
        if not isinstance(n8n_data, dict) or 'nodes' not in n8n_data:
            raise ValueError("Invalid n8n workflow format")

        # Create LiteGraph structure
        litegraph_data = {
            "version": 0.4,
            "config": {},
            "nodes": [],
            "links": [],
            "groups": [],
            "extra": {
                "n8n_metadata": {
                    "original_name": n8n_data.get('name', 'Imported N8n Workflow'),
                    "imported_at": None,  # Will be set by caller
                    "n8n_version": "unknown"
                }
            }
        }

        # Convert nodes
        node_id_mapping = {}
        for n8n_node in n8n_data.get('nodes', []):
            try:
                litegraph_node, node_id = cls._convert_n8n_node(n8n_node)
                if litegraph_node:
                    litegraph_data["nodes"].append(litegraph_node)
                    node_id_mapping[n8n_node['id']] = node_id
            except Exception as e:
                logger.warning(f"Failed to convert n8n node {n8n_node.get('name', 'unknown')}: {e}")
                continue

        # Convert connections
        for connection in n8n_data.get('connections', []):
            try:
                litegraph_links = cls._convert_n8n_connections(connection, node_id_mapping)
                litegraph_data["links"].extend(litegraph_links)
            except Exception as e:
                logger.warning(f"Failed to convert n8n connections: {e}")
                continue

        return litegraph_data

    @classmethod
    def _convert_n8n_node(cls, n8n_node: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Convert a single n8n node to LiteGraph format

        Args:
            n8n_node: n8n node data

        Returns:
            Tuple of (litegraph_node_dict, node_id) or (None, None) if conversion fails
        """
        n8n_type = n8n_node.get('type', '')
        mapping = cls.NODE_MAPPINGS.get(n8n_type)

        if not mapping:
            # Try fuzzy matching for custom nodes
            mapping = cls._find_best_mapping(n8n_type)

        if not mapping:
            logger.info(f"No mapping found for n8n node type: {n8n_type}")
            return None, None

        # Generate unique node ID
        node_id = f"{mapping.durgasflow_type}_{n8n_node['id']}"

        # Convert position
        position = n8n_node.get('position', [0, 0])

        # Convert parameters
        parameters = cls._convert_parameters(
            n8n_node.get('parameters', {}),
            mapping.parameter_mappings
        )

        # Create LiteGraph node
        litegraph_node = {
            "id": node_id,
            "type": mapping.durgasflow_type,
            "pos": position,
            "size": [180, 80],  # Default size
            "flags": {},
            "order": 0,
            "mode": 0,
            "inputs": cls._create_inputs(mapping.input_mappings),
            "outputs": cls._create_outputs(mapping.output_mappings),
            "properties": parameters,
            "widgets_values": [],
            "title": n8n_node.get('name', mapping.durgasflow_type.split('/')[-1])
        }

        # Add color if specified
        if mapping.color:
            litegraph_node["color"] = mapping.color

        return litegraph_node, node_id

    @classmethod
    def _find_best_mapping(cls, n8n_type: str) -> Optional[N8nNodeMapping]:
        """
        Find the best mapping for an unknown n8n node type using fuzzy matching

        Args:
            n8n_type: The n8n node type to find a mapping for

        Returns:
            Best matching N8nNodeMapping or None
        """
        # Check for common patterns
        if 'webhook' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.webhook')
        elif 'http' in n8n_type.lower() or 'request' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.httpRequest')
        elif 'email' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.emailSend')
        elif 'slack' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.slack')
        elif 'schedule' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.scheduleTrigger')
        elif 'code' in n8n_type.lower() or 'javascript' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.code')
        elif 'if' in n8n_type.lower() or 'condition' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.if')
        elif 'set' in n8n_type.lower() or 'variable' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.set')
        elif 'ai' in n8n_type.lower() or 'openai' in n8n_type.lower() or 'chat' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-langchain.chatOpenAi')
        elif 'database' in n8n_type.lower() or 'postgres' in n8n_type.lower() or 'mysql' in n8n_type.lower():
            return cls.NODE_MAPPINGS.get('n8n-nodes-base.postgres')
        elif 'file' in n8n_type.lower():
            if 'read' in n8n_type.lower():
                return cls.NODE_MAPPINGS.get('n8n-nodes-base.readBinaryFile')
            elif 'write' in n8n_type.lower():
                return cls.NODE_MAPPINGS.get('n8n-nodes-base.writeBinaryFile')

        return None

    @classmethod
    def _convert_parameters(cls, n8n_params: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert n8n parameters to durgasflow format

        Args:
            n8n_params: n8n node parameters
            mapping: Parameter name mapping

        Returns:
            Converted parameters
        """
        converted = {}

        for n8n_key, durgasflow_key in mapping.items():
            if n8n_key in n8n_params:
                value = n8n_params[n8n_key]
                converted[durgasflow_key] = cls._convert_parameter_value(value)

        return converted

    @classmethod
    def _convert_parameter_value(cls, value: Any) -> Any:
        """
        Convert individual parameter values, handling expressions and complex types

        Args:
            value: The parameter value to convert

        Returns:
            Converted value
        """
        if isinstance(value, str):
            # Handle n8n expressions like {{$json.field}}
            if value.startswith('{{$') and value.endswith('}}'):
                # Convert n8n expressions to a format that can be handled
                # For now, we'll keep them as-is and let the node handlers process them
                return value

            # Handle environment variables like {{$env.VARIABLE}}
            env_match = re.search(r'\{\{\$env\.([^}]+)\}\}', value)
            if env_match:
                # Convert to Django settings format
                var_name = env_match.group(1).upper()
                return f"{{{{ settings.{var_name} }}}}"

        elif isinstance(value, dict):
            # Recursively convert nested dictionaries
            return {k: cls._convert_parameter_value(v) for k, v in value.items()}

        elif isinstance(value, list):
            # Convert lists
            return [cls._convert_parameter_value(item) for item in value]

        return value

    @classmethod
    def _create_inputs(cls, input_mappings: Dict[str, List[str]]) -> List[Dict]:
        """
        Create LiteGraph input definitions from mapping

        Args:
            input_mappings: Input mapping configuration

        Returns:
            List of input definitions
        """
        inputs = []
        for connection_type, names in input_mappings.items():
            for name in names:
                inputs.append({
                    "name": name,
                    "type": "object",  # Default type
                    "link": None
                })
        return inputs

    @classmethod
    def _create_outputs(cls, output_mappings: Dict[str, List[str]]) -> List[Dict]:
        """
        Create LiteGraph output definitions from mapping

        Args:
            output_mappings: Output mapping configuration

        Returns:
            List of output definitions
        """
        outputs = []
        for connection_type, names in output_mappings.items():
            for name in names:
                outputs.append({
                    "name": name,
                    "type": "object",  # Default type
                    "links": []
                })
        return outputs

    @classmethod
    def _convert_n8n_connections(cls, connection_data: Dict, node_id_mapping: Dict[str, str]) -> List[Dict]:
        """
        Convert n8n connections to LiteGraph links

        Args:
            connection_data: n8n connection data
            node_id_mapping: Mapping from n8n node IDs to LiteGraph node IDs

        Returns:
            List of LiteGraph link definitions
        """
        links = []

        for node_name, node_connections in connection_data.items():
            if not isinstance(node_connections, dict):
                continue

            for connection_type, connections in node_connections.items():
                if not isinstance(connections, list):
                    continue

                for connection_list in connections:
                    if not isinstance(connection_list, list):
                        continue

                    for connection in connection_list:
                        if not isinstance(connection, dict):
                            continue

                        target_node = connection.get('node')
                        target_type = connection.get('type', 'main')
                        target_index = connection.get('index', 0)

                        # Find the source node ID
                        source_node_id = None
                        for n8n_id, lg_id in node_id_mapping.items():
                            # This is a simplified mapping - in practice you'd need
                            # to match by node name or maintain a proper mapping
                            if node_name in lg_id:
                                source_node_id = lg_id
                                break

                        target_node_id = None
                        for n8n_id, lg_id in node_id_mapping.items():
                            if target_node in lg_id:
                                target_node_id = lg_id
                                break

                        if source_node_id and target_node_id:
                            link = {
                                "id": f"{source_node_id}_{target_node_id}_{len(links)}",
                                "origin_id": source_node_id,
                                "origin_slot": 0,  # Default output slot
                                "target_id": target_node_id,
                                "target_slot": target_index
                            }
                            links.append(link)

        return links

    @classmethod
    def validate_n8n_workflow(cls, n8n_data: Dict[str, Any]) -> List[str]:
        """
        Validate n8n workflow before conversion

        Args:
            n8n_data: n8n workflow data

        Returns:
            List of validation errors
        """
        errors = []

        if not isinstance(n8n_data, dict):
            errors.append("Workflow data must be a dictionary")
            return errors

        if 'nodes' not in n8n_data:
            errors.append("Workflow must contain 'nodes' array")
            return errors

        nodes = n8n_data.get('nodes', [])
        if not isinstance(nodes, list):
            errors.append("'nodes' must be an array")
            return errors

        if len(nodes) == 0:
            errors.append("Workflow must contain at least one node")
            return errors

        # Check for required node fields
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"Node {i} must be a dictionary")
                continue

            if 'id' not in node:
                errors.append(f"Node {i} missing 'id' field")
            if 'type' not in node:
                errors.append(f"Node {i} missing 'type' field")

        # Check connections
        connections = n8n_data.get('connections', {})
        if not isinstance(connections, dict):
            errors.append("'connections' must be a dictionary")

        return errors

    @classmethod
    def get_supported_node_types(cls) -> List[str]:
        """
        Get list of supported n8n node types

        Returns:
            List of supported n8n node type strings
        """
        return list(cls.NODE_MAPPINGS.keys())

    @classmethod
    def get_mapping_stats(cls, n8n_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze n8n workflow and provide conversion statistics

        Args:
            n8n_data: n8n workflow data

        Returns:
            Dictionary with conversion statistics
        """
        nodes = n8n_data.get('nodes', [])
        total_nodes = len(nodes)

        supported_nodes = 0
        unsupported_nodes = 0
        partially_supported = 0

        supported_types = []
        unsupported_types = []

        for node in nodes:
            node_type = node.get('type', '')
            mapping = cls.NODE_MAPPINGS.get(node_type)

            if mapping:
                supported_nodes += 1
                supported_types.append(node_type)
            else:
                mapping = cls._find_best_mapping(node_type)
                if mapping:
                    partially_supported += 1
                    supported_types.append(f"{node_type} (mapped to {mapping.durgasflow_type})")
                else:
                    unsupported_nodes += 1
                    unsupported_types.append(node_type)

        return {
            'total_nodes': total_nodes,
            'supported_nodes': supported_nodes,
            'partially_supported_nodes': partially_supported,
            'unsupported_nodes': unsupported_nodes,
            'supported_types': list(set(supported_types)),
            'unsupported_types': list(set(unsupported_types)),
            'conversion_confidence': (supported_nodes + partially_supported) / total_nodes if total_nodes > 0 else 0
        }