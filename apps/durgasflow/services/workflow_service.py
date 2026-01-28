"""
WorkflowService - CRUD operations for workflows

Handles workflow creation, updates, and management.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.contrib.auth import get_user_model

from ..models import (
    Workflow, WorkflowNode, WorkflowConnection,
    WorkflowStatus, TriggerType
)

User = get_user_model()
logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflows"""

    @classmethod
    def create_workflow(
        cls,
        name: str,
        user: User,
        description: str = '',
        trigger_type: str = TriggerType.MANUAL,
        graph_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            user: Owner user
            description: Optional description
            trigger_type: Trigger type (manual, webhook, schedule, event)
            graph_data: Optional initial graph data from LiteGraph
            tags: Optional list of tags
            
        Returns:
            Created Workflow instance
        """
        workflow = Workflow.objects.create(
            name=name,
            description=description,
            trigger_type=trigger_type,
            graph_data=graph_data or cls._get_initial_graph_data(),
            tags=tags or [],
            created_by=user
        )
        
        logger.info(f"Created workflow: {workflow.id} - {workflow.name}")
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
        workflow: Workflow,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trigger_type: Optional[str] = None,
        graph_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        settings: Optional[Dict] = None
    ) -> Workflow:
        """
        Update a workflow.
        
        Args:
            workflow: Workflow to update
            name: Optional new name
            description: Optional new description
            trigger_type: Optional new trigger type
            graph_data: Optional new graph data
            tags: Optional new tags
            settings: Optional new settings
            
        Returns:
            Updated Workflow instance
        """
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if trigger_type is not None:
            workflow.trigger_type = trigger_type
        if graph_data is not None:
            workflow.graph_data = graph_data
        if tags is not None:
            workflow.tags = tags
        if settings is not None:
            workflow.settings = settings
        
        workflow.save()
        logger.info(f"Updated workflow: {workflow.id}")
        return workflow

    @classmethod
    @transaction.atomic
    def save_graph(cls, workflow: Workflow, graph_data: Dict) -> Workflow:
        """
        Save graph data from the visual editor.
        
        This also syncs the WorkflowNode and WorkflowConnection models
        for easier querying.
        
        Args:
            workflow: Workflow to update
            graph_data: LiteGraph serialized graph data
            
        Returns:
            Updated Workflow instance
        """
        workflow.graph_data = graph_data
        workflow.save(update_fields=['graph_data', 'updated_at'])
        
        # Sync nodes and connections
        cls._sync_nodes_from_graph(workflow, graph_data)
        cls._sync_connections_from_graph(workflow, graph_data)
        
        logger.info(f"Saved graph for workflow: {workflow.id}")
        return workflow

    @classmethod
    def _sync_nodes_from_graph(cls, workflow: Workflow, graph_data: Dict) -> None:
        """Sync WorkflowNode models from graph data"""
        # Clear existing nodes
        WorkflowNode.objects.filter(workflow=workflow).delete()
        
        nodes_data = graph_data.get('nodes', [])
        for node_data in nodes_data:
            node_type = node_data.get('type', 'unknown')
            category = cls._get_node_category(node_type)
            
            WorkflowNode.objects.create(
                workflow=workflow,
                node_id=str(node_data.get('id', '')),
                node_type=node_type,
                category=category,
                title=node_data.get('title', node_type),
                position_x=node_data.get('pos', [0, 0])[0],
                position_y=node_data.get('pos', [0, 0])[1],
                config=node_data.get('properties', {}),
                inputs=node_data.get('inputs', []),
                outputs=node_data.get('outputs', []),
                properties=node_data.get('properties', {})
            )

    @classmethod
    def _sync_connections_from_graph(cls, workflow: Workflow, graph_data: Dict) -> None:
        """Sync WorkflowConnection models from graph data"""
        # Clear existing connections
        WorkflowConnection.objects.filter(workflow=workflow).delete()
        
        links_data = graph_data.get('links', [])
        nodes = {str(n.node_id): n for n in workflow.nodes.all()}
        
        for link_data in links_data:
            if not link_data or len(link_data) < 6:
                continue
            
            # LiteGraph link format: [link_id, origin_id, origin_slot, target_id, target_slot, type]
            source_id = str(link_data[1])
            target_id = str(link_data[3])
            
            source_node = nodes.get(source_id)
            target_node = nodes.get(target_id)
            
            if source_node and target_node:
                WorkflowConnection.objects.create(
                    workflow=workflow,
                    source_node=source_node,
                    source_output=link_data[2],
                    target_node=target_node,
                    target_input=link_data[4]
                )

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
    def duplicate_workflow(cls, workflow: Workflow, user: User) -> Workflow:
        """
        Duplicate a workflow.
        
        Args:
            workflow: Workflow to duplicate
            user: User who will own the duplicate
            
        Returns:
            New duplicated Workflow instance
        """
        new_workflow = Workflow.objects.create(
            name=f"{workflow.name} (Copy)",
            description=workflow.description,
            graph_data=workflow.graph_data,
            trigger_type=workflow.trigger_type,
            tags=workflow.tags.copy(),
            settings=workflow.settings.copy(),
            created_by=user
        )
        
        logger.info(f"Duplicated workflow {workflow.id} to {new_workflow.id}")
        return new_workflow

    @classmethod
    def export_workflow(cls, workflow: Workflow) -> Dict:
        """
        Export workflow to JSON format.
        
        Args:
            workflow: Workflow to export
            
        Returns:
            Dict containing workflow export data
        """
        return {
            'name': workflow.name,
            'description': workflow.description,
            'trigger_type': workflow.trigger_type,
            'graph_data': workflow.graph_data,
            'tags': workflow.tags,
            'settings': workflow.settings,
            'version': '1.0',
        }

    @classmethod
    def import_workflow(cls, data: Dict, user: User) -> Workflow:
        """
        Import workflow from JSON format.

        Args:
            data: Workflow export data
            user: User who will own the imported workflow

        Returns:
            Created Workflow instance
        """
        return cls.create_workflow(
            name=data.get('name', 'Imported Workflow'),
            description=data.get('description', ''),
            trigger_type=data.get('trigger_type', TriggerType.MANUAL),
            graph_data=data.get('graph_data'),
            tags=data.get('tags'),
            user=user
        )

    @classmethod
    def import_n8n_workflow(cls, n8n_data: Dict, user: User) -> Workflow:
        """
        Import n8n workflow and convert to durgasflow format.

        Args:
            n8n_data: n8n workflow JSON data
            user: User who will own the imported workflow

        Returns:
            Created Workflow instance
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
        litegraph_data['extra']['n8n_metadata']['imported_at'] = timezone.now().isoformat()

        # Get conversion statistics
        stats = N8nParser.get_mapping_stats(n8n_data)
        litegraph_data['extra']['conversion_stats'] = stats

        # Determine trigger type from n8n workflow
        trigger_type = cls._detect_trigger_type(n8n_data)

        # Create workflow
        workflow = cls.create_workflow(
            name=f"{n8n_data.get('name', 'Imported N8n Workflow')} (N8n)",
            description=f"Imported from n8n workflow. {stats['supported_nodes']}/{stats['total_nodes']} nodes converted successfully.",
            trigger_type=trigger_type,
            graph_data=litegraph_data,
            tags=['n8n-import', 'imported'],
            user=user
        )

        logger.info(f"Successfully imported n8n workflow: {workflow.id} - {stats['supported_nodes']}/{stats['total_nodes']} nodes converted")
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
    def get_workflow_stats(cls, user: User) -> Dict:
        """
        Get workflow statistics for a user.
        
        Args:
            user: User to get stats for
            
        Returns:
            Dict containing workflow statistics
        """
        from django.db.models import Count, Sum
        from ..models import Execution, ExecutionStatus
        
        workflows = Workflow.objects.filter(created_by=user)
        
        return {
            'total_workflows': workflows.count(),
            'active_workflows': workflows.filter(is_active=True).count(),
            'draft_workflows': workflows.filter(status=WorkflowStatus.DRAFT).count(),
            'total_executions': sum(w.execution_count for w in workflows),
            'total_successes': sum(w.success_count for w in workflows),
            'total_failures': sum(w.failure_count for w in workflows),
        }
