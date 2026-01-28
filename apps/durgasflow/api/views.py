"""
Durgasflow API Views
"""

import json
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.core.decorators.auth import require_super_admin
from ..services.workflow_service import WorkflowService
from ..services.execution_engine import ExecutionEngine
from ..services.node_registry import NodeRegistry
from ..services.workflow_storage_service import (
    WorkflowStorageService,
    CredentialStorageService,
    WorkflowTemplateStorageService
)
from .serializers import (
    WorkflowListSerializer, WorkflowDetailSerializer, WorkflowCreateSerializer,
    WorkflowGraphSerializer, ExecutionListSerializer, ExecutionDetailSerializer,
    ExecutionLogSerializer, CredentialListSerializer, CredentialDetailSerializer,
    WorkflowTemplateSerializer, NodeTypeSerializer, StatsSerializer
)


# ============================================
# Workflow Endpoints
# ============================================

@require_super_admin
@api_view(['GET', 'POST'])
def workflow_list(request):
    """List all workflows or create a new one"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    
    if request.method == 'GET':
        filters = {'created_by': user_uuid}
        
        # Filtering
        status_filter = request.query_params.get('status')
        trigger_filter = request.query_params.get('trigger')
        
        if status_filter:
            filters['status'] = status_filter
        if trigger_filter:
            filters['trigger_type'] = trigger_filter
        
        workflows_result = storage.list(filters=filters, limit=None, offset=0)
        workflows = workflows_result.get('items', [])
        
        # Convert to serializer format (dicts should work with serializers)
        serializer = WorkflowListSerializer(workflows, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = WorkflowCreateSerializer(data=request.data)
        if serializer.is_valid():
            workflow = WorkflowService.create_workflow(
                name=serializer.validated_data.get('name', 'Untitled Workflow'),
                description=serializer.validated_data.get('description', ''),
                trigger_type=serializer.validated_data.get('trigger_type', 'manual'),
                graph_data=serializer.validated_data.get('graph_data'),
                tags=serializer.validated_data.get('tags'),
                user_uuid=user_uuid
            )
            return Response(
                WorkflowDetailSerializer(workflow).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@require_super_admin
@api_view(['GET', 'PUT', 'DELETE'])
def workflow_detail(request, workflow_id):
    """Get, update, or delete a workflow"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = WorkflowDetailSerializer(workflow)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = WorkflowCreateSerializer(workflow, data=request.data, partial=True)
        if serializer.is_valid():
            updated = WorkflowService.update_workflow(
                workflow_id=workflow_id,
                name=serializer.validated_data.get('name'),
                description=serializer.validated_data.get('description'),
                trigger_type=serializer.validated_data.get('trigger_type'),
                tags=serializer.validated_data.get('tags'),
                settings=serializer.validated_data.get('settings')
            )
            if updated:
                return Response(WorkflowDetailSerializer(updated).data)
            return Response({'error': 'Failed to update workflow'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        storage.delete_workflow(workflow_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@require_super_admin
@api_view(['GET', 'PUT'])
def workflow_graph(request, workflow_id):
    """Get or update workflow graph data"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        return Response({
            'workflow_id': workflow_id,
            'graph_data': workflow.get('graph_data', {})
        })
    
    elif request.method == 'PUT':
        serializer = WorkflowGraphSerializer(data=request.data)
        if serializer.is_valid():
            updated = WorkflowService.save_graph(
                workflow_id=workflow_id,
                graph_data=serializer.validated_data['graph_data']
            )
            if updated:
                return Response({
                    'workflow_id': workflow_id,
                    'graph_data': updated.get('graph_data', {}),
                    'saved': True
                })
            return Response({'error': 'Failed to save graph'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@require_super_admin
@api_view(['POST'])
def workflow_execute(request, workflow_id):
    """Execute a workflow manually"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    trigger_data = request.data.get('trigger_data', {})
    async_execution = request.data.get('async', False)
    
    try:
        execution = ExecutionEngine.execute_workflow(
            workflow=workflow,
            trigger_type='manual',
            trigger_data=trigger_data,
            user_uuid=user_uuid,
            async_execution=async_execution
        )
        
        return Response({
            'execution_id': execution.get('execution_id') or execution.get('id'),
            'status': execution.get('status'),
            'async': async_execution
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_super_admin
@api_view(['POST'])
def workflow_activate(request, workflow_id):
    """Activate a workflow"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    storage.update_workflow(workflow_id, is_active=True, status='active')
    return Response({'status': 'activated', 'is_active': True})


@require_super_admin
@api_view(['POST'])
def workflow_deactivate(request, workflow_id):
    """Deactivate a workflow"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    storage.update_workflow(workflow_id, is_active=False, status='paused')
    return Response({'status': 'deactivated', 'is_active': False})


@require_super_admin
@api_view(['POST'])
def workflow_duplicate(request, workflow_id):
    """Duplicate a workflow"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    new_workflow = WorkflowService.duplicate_workflow(workflow_id, user_uuid)
    return Response(
        WorkflowDetailSerializer(new_workflow).data,
        status=status.HTTP_201_CREATED
    )


@require_super_admin
@api_view(['GET'])
def workflow_export(request, workflow_id):
    """Export a workflow to JSON"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    workflow = storage.get_workflow(workflow_id)
    
    if not workflow or workflow.get('created_by') != user_uuid:
        return Response(
            {'error': 'Workflow not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    export_data = WorkflowService.export_workflow(workflow_id)
    if export_data:
        return Response(export_data)
    return Response({'error': 'Failed to export workflow'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_super_admin
@api_view(['POST'])
def workflow_import(request):
    """Import a workflow from JSON"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    try:
        workflow = WorkflowService.import_workflow(request.data, user_uuid)
        return Response(
            WorkflowDetailSerializer(workflow).data,
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# Execution Endpoints
# ============================================

@require_super_admin
@api_view(['GET'])
def execution_detail(request, execution_id):
    """Get execution details"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    
    # Find execution in workflows
    workflows_result = storage.list(
        filters={'created_by': user_uuid},
        limit=None,
        offset=0
    )
    
    execution = None
    workflow = None
    for wf in workflows_result.get('items', []):
        executions = wf.get('executions', [])
        for exec_data in executions:
            if exec_data.get('execution_id') == execution_id or exec_data.get('id') == execution_id:
                execution = exec_data
                workflow = wf
                break
        if execution:
            break
    
    if not execution:
        return Response(
            {'error': 'Execution not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    execution['workflow'] = workflow
    serializer = ExecutionDetailSerializer(execution)
    return Response(serializer.data)


@require_super_admin
@api_view(['GET'])
def execution_logs(request, execution_id):
    """Get execution logs"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = WorkflowStorageService()
    
    # Find execution in workflows
    workflows_result = storage.list(
        filters={'created_by': user_uuid},
        limit=None,
        offset=0
    )
    
    logs = []
    for wf in workflows_result.get('items', []):
        executions = wf.get('executions', [])
        for exec_data in executions:
            if exec_data.get('execution_id') == execution_id or exec_data.get('id') == execution_id:
                logs = exec_data.get('logs', [])
                break
        if logs:
            break
    
    if not logs:
        return Response(
            {'error': 'Execution not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Filter by level
    level = request.query_params.get('level')
    if level:
        logs = [log for log in logs if log.get('level') == level]
    
    serializer = ExecutionLogSerializer(logs, many=True)
    return Response(serializer.data)


# ============================================
# Node Registry Endpoints
# ============================================

@require_super_admin
@api_view(['GET'])
def node_types(request):
    """Get all available node types"""
    # Get by category if requested
    by_category = request.query_params.get('by_category', 'false').lower() == 'true'
    
    if by_category:
        return Response(NodeRegistry.get_node_types_by_category())
    
    nodes = NodeRegistry.get_all_node_types()
    serializer = NodeTypeSerializer(nodes, many=True)
    return Response(serializer.data)


@require_super_admin
@api_view(['GET'])
def node_schema(request, node_type):
    """Get schema for a specific node type"""
    # Replace / with url-safe character for URL
    node_type = node_type.replace('-', '/')
    
    handler = NodeRegistry.get_node_handler(node_type)
    if not handler:
        return Response({
            'error': f'Node type not found: {node_type}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(handler.get_schema())


# ============================================
# Credential Endpoints
# ============================================

@require_super_admin
@api_view(['GET', 'POST'])
def credential_list(request):
    """List or create credentials"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    credential_storage = CredentialStorageService()
    
    if request.method == 'GET':
        credentials_result = credential_storage.list(
            filters={'created_by': user_uuid},
            limit=None,
            offset=0
        )
        credentials = credentials_result.get('items', [])
        serializer = CredentialListSerializer(credentials, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CredentialDetailSerializer(data=request.data)
        if serializer.is_valid():
            credential = credential_storage.create_credential(
                created_by=user_uuid,
                **serializer.validated_data
            )
            return Response(
                CredentialListSerializer(credential).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@require_super_admin
@api_view(['GET', 'PUT', 'DELETE'])
def credential_detail(request, credential_id):
    """Get, update, or delete a credential"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    credential_storage = CredentialStorageService()
    credential = credential_storage.get_credential(credential_id)
    
    if not credential or credential.get('created_by') != user_uuid:
        return Response(
            {'error': 'Credential not found or unauthorized'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        # Don't return sensitive data
        serializer = CredentialListSerializer(credential)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CredentialDetailSerializer(credential, data=request.data, partial=True)
        if serializer.is_valid():
            updated = credential_storage.update_credential(credential_id, **serializer.validated_data)
            if updated:
                return Response(CredentialListSerializer(updated).data)
            return Response({'error': 'Failed to update credential'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        credential_storage.delete_credential(credential_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Template Endpoints
# ============================================

@require_super_admin
@api_view(['GET'])
def template_list(request):
    """List workflow templates"""
    template_storage = WorkflowTemplateStorageService()
    
    filters = {}
    category = request.query_params.get('category')
    if category:
        filters['category'] = category
    
    templates_result = template_storage.list(
        filters=filters,
        limit=None,
        offset=0
    )
    templates = templates_result.get('items', [])
    
    serializer = WorkflowTemplateSerializer(templates, many=True)
    return Response(serializer.data)


@require_super_admin
@api_view(['GET'])
def template_detail(request, template_id):
    """Get template details"""
    template_storage = WorkflowTemplateStorageService()
    template = template_storage.get_template(template_id)
    
    if not template:
        return Response(
            {'error': 'Template not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = WorkflowTemplateSerializer(template)
    return Response(serializer.data)


# ============================================
# Stats Endpoint
# ============================================

@require_super_admin
@api_view(['GET'])
def stats(request):
    """Get workflow statistics for the current user"""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    stats_data = WorkflowService.get_workflow_stats(user_uuid)
    serializer = StatsSerializer(stats_data)
    return Response(serializer.data)
