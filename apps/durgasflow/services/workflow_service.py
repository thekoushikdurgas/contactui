"""
WorkflowService - CRUD operations for workflows

Handles workflow creation, updates, and management.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone

from .workflow_storage_service import WorkflowStorageService

logger = logging.getLogger(__name__)

# Constants (moved from models)
class TriggerType:
    """Types of workflow triggers"""
    MANUAL = 'manual'
    WEBHOOK = 'webhook'
    SCHEDULE = 'schedule'
    EVENT = 'event'

class WorkflowStatus:
    """Workflow status"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ARCHIVED = 'archived'


class WorkflowService:
    """Service for managing workflows using S3 storage"""
    
    _storage = WorkflowStorageService()

    @classmethod
    def create_workflow(
        cls,
        name: str,
        user_uuid: str,
        description: str = '',
        trigger_type: str = TriggerType.MANUAL,
        graph_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            user_uuid: Owner user UUID string
            description: Optional description
            trigger_type: Trigger type (manual, webhook, schedule, event)
            graph_data: Optional initial graph data from LiteGraph
            tags: Optional list of tags
            
        Returns:
            Created workflow data dictionary
        """
        # Convert user_uuid to string if needed
        if hasattr(user_uuid, 'uuid'):
            user_uuid = str(user_uuid.uuid)
        elif hasattr(user_uuid, 'id'):
            user_uuid = str(user_uuid.id)
        else:
            user_uuid = str(user_uuid)
        
        workflow = cls._storage.create_workflow(
            name=name,
            description=description,
            trigger_type=trigger_type,
            graph_data=graph_data or cls._get_initial_graph_data(),
            tags=tags or [],
            created_by=user_uuid,
            status='draft'
        )
        
        logger.info(f"Created workflow: {workflow.get('id')} - {workflow.get('name')}")
        return workflow

    @classmethod
    def _get_initial_graph_data(cls) -> Dict:
        """Get initial empty graph data structure for LiteGraph"""
        return {
            "version": 0.4,
            "config": {},
            "nodes": [],
            "links": [],
            "groups": [],
            "extra": {}
        }

    @classmethod
    def update_workflow(
        cls,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trigger_type: Optional[str] = None,
        graph_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        settings: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID to update
            name: Optional new name
            description: Optional new description
            trigger_type: Optional new trigger type
            graph_data: Optional new graph data
            tags: Optional new tags
            settings: Optional new settings
            
        Returns:
            Updated workflow data dictionary, or None if not found
        """
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        if trigger_type is not None:
            update_data['trigger_type'] = trigger_type
        if graph_data is not None:
            update_data['graph_data'] = graph_data
        if tags is not None:
            update_data['tags'] = tags
        if settings is not None:
            update_data['settings'] = settings
        
        updated = cls._storage.update_workflow(workflow_id, **update_data)
        if updated:
            logger.info(f"Updated workflow: {workflow_id}")
        return updated

    @classmethod
    def save_graph(cls, workflow_id: str, graph_data: Dict) -> Optional[Dict[str, Any]]:
        """
        Save graph data from the visual editor.
        
        This also syncs the nodes and connections within the workflow data.
        
        Args:
            workflow_id: Workflow ID to update
            graph_data: LiteGraph serialized graph data
            
        Returns:
            Updated workflow data dictionary, or None if not found
        """
        # Sync nodes and connections from graph data
        nodes, connections = cls._extract_nodes_and_connections(graph_data)
        
        # Update workflow with graph data and synced nodes/connections
        updated = cls._storage.update_workflow(
            workflow_id,
            graph_data=graph_data,
            nodes=nodes,
            connections=connections
        )
        
        if updated:
            logger.info(f"Saved graph for workflow: {workflow_id}")
        return updated

    @classmethod
    def _extract_nodes_and_connections(cls, graph_data: Dict) -> tuple[List[Dict], List[Dict]]:
        """Extract nodes and connections from graph data"""
        nodes_data = graph_data.get('nodes', [])
        links_data = graph_data.get('links', [])
        
        nodes = []
        for node_data in nodes_data:
            node_type = node_data.get('type', 'unknown')
            category = cls._get_node_category(node_type)
            
            nodes.append({
                'node_id': str(node_data.get('id', '')),
                'node_type': node_type,
                'category': category,
                'title': node_data.get('title', node_type),
                'position_x': node_data.get('pos', [0, 0])[0],
                'position_y': node_data.get('pos', [0, 0])[1],
                'config': node_data.get('properties', {}),
                'inputs': node_data.get('inputs', []),
                'outputs': node_data.get('outputs', []),
                'properties': node_data.get('properties', {})
            })
        
        connections = []
        for link_data in links_data:
            if not link_data or len(link_data) < 6:
                continue
            
            # LiteGraph link format: [link_id, origin_id, origin_slot, target_id, target_slot, type]
            connections.append({
                'source_id': str(link_data[1]),
                'source_output': link_data[2],
                'target_id': str(link_data[3]),
                'target_input': link_data[4],
                'link_type': link_data[5] if len(link_data) > 5 else None
            })
        
        return nodes, connections

    @classmethod
    def _get_node_category(cls, node_type: str) -> str:
        """Determine node category from node type"""
        if node_type.startswith('trigger/'):
            return 'trigger'
        elif node_type.startswith('ai/') or node_type.startswith('agent/'):
            return 'ai_agent'
        elif node_type.startswith('logic/') or node_type.startswith('transform/'):
            return 'logic'
        elif node_type.startswith('docsai/'):
            return 'docsai'
        else:
            return 'action'

    @classmethod
    def duplicate_workflow(cls, workflow_id: str, user_uuid: str) -> Dict[str, Any]:
        """
        Duplicate a workflow.
        
        Args:
            workflow_id: Workflow ID to duplicate
            user_uuid: User UUID who will own the duplicate
            
        Returns:
            New duplicated workflow data dictionary
        """
        workflow = cls._storage.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Convert user_uuid to string if needed
        if hasattr(user_uuid, 'uuid'):
            user_uuid = str(user_uuid.uuid)
        elif hasattr(user_uuid, 'id'):
            user_uuid = str(user_uuid.id)
        else:
            user_uuid = str(user_uuid)
        
        new_workflow = cls._storage.create_workflow(
            name=f"{workflow.get('name')} (Copy)",
            description=workflow.get('description', ''),
            graph_data=workflow.get('graph_data', {}),
            trigger_type=workflow.get('trigger_type', TriggerType.MANUAL),
            tags=workflow.get('tags', []).copy() if workflow.get('tags') else [],
            settings=workflow.get('settings', {}).copy() if workflow.get('settings') else {},
            created_by=user_uuid,
            status=workflow.get('status', 'draft')
        )
        
        logger.info(f"Duplicated workflow {workflow_id} to {new_workflow.get('id')}")
        return new_workflow

    @classmethod
    def export_workflow(cls, workflow_id: str) -> Optional[Dict]:
        """
        Export workflow to JSON format.
        
        Args:
            workflow_id: Workflow ID to export
            
        Returns:
            Dict containing workflow export data, or None if not found
        """
        workflow = cls._storage.get_workflow(workflow_id)
        if not workflow:
            return None
        
        return {
            'name': workflow.get('name'),
            'description': workflow.get('description', ''),
            'trigger_type': workflow.get('trigger_type'),
            'graph_data': workflow.get('graph_data', {}),
            'tags': workflow.get('tags', []),
            'settings': workflow.get('settings', {}),
            'version': '1.0',
        }

    @classmethod
    def import_workflow(cls, data: Dict, user_uuid: str) -> Dict[str, Any]:
        """
        Import workflow from JSON format.

        Args:
            data: Workflow export data
            user_uuid: User UUID who will own the imported workflow

        Returns:
            Created workflow dictionary
        """
        # Convert user_uuid to string if needed
        user_uuid_str = None
        if user_uuid:
            if hasattr(user_uuid, 'uuid'):
                user_uuid_str = str(user_uuid.uuid)
            elif hasattr(user_uuid, 'id'):
                user_uuid_str = str(user_uuid.id)
            else:
                user_uuid_str = str(user_uuid)
        
        return cls.create_workflow(
            name=data.get('name', 'Imported Workflow'),
            description=data.get('description', ''),
            trigger_type=data.get('trigger_type', TriggerType.MANUAL),
            graph_data=data.get('graph_data'),
            tags=data.get('tags'),
            user_uuid=user_uuid_str
        )

    @classmethod
    def import_n8n_workflow(cls, n8n_data: Dict, user_uuid: str) -> Dict[str, Any]:
        """
        Import n8n workflow and convert to durgasflow format.

        Args:
            n8n_data: n8n workflow JSON data
            user_uuid: User UUID who will own the imported workflow

        Returns:
            Created workflow data dictionary
        """
        from .n8n_parser import N8nParser

        # Validate n8n workflow
        validation_errors = N8nParser.validate_n8n_workflow(n8n_data)
        if validation_errors:
            raise ValueError(f"Invalid n8n workflow: {', '.join(validation_errors)}")

        # Convert to LiteGraph format
        try:
            litegraph_data = N8nParser.parse_n8n_workflow(n8n_data)
        except Exception as e:
            raise ValueError(f"Failed to convert n8n workflow: {str(e)}")

        # Add import metadata
        if 'extra' not in litegraph_data:
            litegraph_data['extra'] = {}
        if 'n8n_metadata' not in litegraph_data['extra']:
            litegraph_data['extra']['n8n_metadata'] = {}
        litegraph_data['extra']['n8n_metadata']['imported_at'] = timezone.now().isoformat()

        # Get conversion statistics
        stats = N8nParser.get_mapping_stats(n8n_data)
        litegraph_data['extra']['conversion_stats'] = stats

        # Determine trigger type from n8n workflow
        trigger_type = cls._detect_trigger_type(n8n_data)

        # Convert user_uuid to string if needed
        if hasattr(user_uuid, 'uuid'):
            user_uuid = str(user_uuid.uuid)
        elif hasattr(user_uuid, 'id'):
            user_uuid = str(user_uuid.id)
        else:
            user_uuid = str(user_uuid)

        # Create workflow
        workflow = cls.create_workflow(
            name=f"{n8n_data.get('name', 'Imported N8n Workflow')} (N8n)",
            description=f"Imported from n8n workflow. {stats['supported_nodes']}/{stats['total_nodes']} nodes converted successfully.",
            trigger_type=trigger_type,
            graph_data=litegraph_data,
            tags=['n8n-import', 'imported'],
            user_uuid=user_uuid
        )

        logger.info(f"Successfully imported n8n workflow: {workflow.get('id')} - {stats['supported_nodes']}/{stats['total_nodes']} nodes converted")
        return workflow

    @classmethod
    def _detect_trigger_type(cls, n8n_data: Dict) -> str:
        """
        Detect the primary trigger type from n8n workflow nodes.

        Args:
            n8n_data: n8n workflow data

        Returns:
            Trigger type string
        """
        nodes = n8n_data.get('nodes', [])

        # Check for webhook triggers
        for node in nodes:
            if node.get('type') == 'n8n-nodes-base.webhook':
                return TriggerType.WEBHOOK

        # Check for schedule triggers
        for node in nodes:
            if node.get('type') == 'n8n-nodes-base.scheduleTrigger':
                return TriggerType.SCHEDULE

        # Check for event-based triggers
        for node in nodes:
            node_type = node.get('type', '').lower()
            if 'event' in node_type or 'trigger' in node_type:
                return TriggerType.EVENT

        # Default to manual
        return TriggerType.MANUAL

    @classmethod
    def get_workflow_stats(cls, user_uuid: str) -> Dict:
        """
        Get workflow statistics for a user.
        
        Args:
            user_uuid: User UUID to get stats for
            
        Returns:
            Dict containing workflow statistics
        """
        # Convert user_uuid to string if needed
        if hasattr(user_uuid, 'uuid'):
            user_uuid = str(user_uuid.uuid)
        elif hasattr(user_uuid, 'id'):
            user_uuid = str(user_uuid.id)
        else:
            user_uuid = str(user_uuid)
        
        workflows_result = cls._storage.list(
            filters={'created_by': user_uuid},
            limit=None,
            offset=0
        )
        workflows = workflows_result.get('items', [])
        
        total_executions = 0
        total_successes = 0
        total_failures = 0
        
        for workflow in workflows:
            executions = workflow.get('executions', [])
            total_executions += len(executions)
            total_successes += len([e for e in executions if e.get('status') == 'completed'])
            total_failures += len([e for e in executions if e.get('status') == 'failed'])
        
        return {
            'total_workflows': len(workflows),
            'active_workflows': len([w for w in workflows if w.get('is_active')]),
            'draft_workflows': len([w for w in workflows if w.get('status') == WorkflowStatus.DRAFT]),
            'total_executions': total_executions,
            'total_successes': total_successes,
            'total_failures': total_failures,
        }
