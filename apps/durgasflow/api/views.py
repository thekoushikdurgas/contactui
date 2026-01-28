"""
Durgasflow API Views
"""

import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import (
    Workflow, Execution, ExecutionLog, Credential, WorkflowTemplate
)
from ..services.workflow_service import WorkflowService
from ..services.execution_engine import ExecutionEngine
from ..services.node_registry import NodeRegistry
from .serializers import (
    WorkflowListSerializer, WorkflowDetailSerializer, WorkflowCreateSerializer,
    WorkflowGraphSerializer, ExecutionListSerializer, ExecutionDetailSerializer,
    ExecutionLogSerializer, CredentialListSerializer, CredentialDetailSerializer,
    WorkflowTemplateSerializer, NodeTypeSerializer, StatsSerializer
)


# ============================================
# Workflow Endpoints
# ============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workflow_list(request):
    """List all workflows or create a new one"""
    if request.method == 'GET':
        workflows = Workflow.objects.filter(created_by=request.user)
        
        # Filtering
        status_filter = request.query_params.get('status')
        trigger_filter = request.query_params.get('trigger')
        
        if status_filter:
            workflows = workflows.filter(status=status_filter)
        if trigger_filter:
            workflows = workflows.filter(trigger_type=trigger_filter)
        
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
                user=request.user
            )
            return Response(
                WorkflowDetailSerializer(workflow).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def workflow_detail(request, workflow_id):
    """Get, update, or delete a workflow"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    
    if request.method == 'GET':
        serializer = WorkflowDetailSerializer(workflow)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = WorkflowCreateSerializer(workflow, data=request.data, partial=True)
        if serializer.is_valid():
            workflow = WorkflowService.update_workflow(
                workflow=workflow,
                name=serializer.validated_data.get('name'),
                description=serializer.validated_data.get('description'),
                trigger_type=serializer.validated_data.get('trigger_type'),
                tags=serializer.validated_data.get('tags'),
                settings=serializer.validated_data.get('settings')
            )
            return Response(WorkflowDetailSerializer(workflow).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        workflow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def workflow_graph(request, workflow_id):
    """Get or update workflow graph data"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    
    if request.method == 'GET':
        return Response({
            'workflow_id': str(workflow.id),
            'graph_data': workflow.graph_data
        })
    
    elif request.method == 'PUT':
        serializer = WorkflowGraphSerializer(data=request.data)
        if serializer.is_valid():
            workflow = WorkflowService.save_graph(
                workflow=workflow,
                graph_data=serializer.validated_data['graph_data']
            )
            return Response({
                'workflow_id': str(workflow.id),
                'graph_data': workflow.graph_data,
                'saved': True
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workflow_execute(request, workflow_id):
    """Execute a workflow manually"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    
    trigger_data = request.data.get('trigger_data', {})
    async_execution = request.data.get('async', False)
    
    try:
        execution = ExecutionEngine.execute_workflow(
            workflow=workflow,
            trigger_type='manual',
            trigger_data=trigger_data,
            user=request.user,
            async_execution=async_execution
        )
        
        return Response({
            'execution_id': str(execution.id),
            'status': execution.status,
            'async': async_execution
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workflow_activate(request, workflow_id):
    """Activate a workflow"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    workflow.activate()
    return Response({'status': 'activated', 'is_active': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workflow_deactivate(request, workflow_id):
    """Deactivate a workflow"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    workflow.deactivate()
    return Response({'status': 'deactivated', 'is_active': False})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workflow_duplicate(request, workflow_id):
    """Duplicate a workflow"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    new_workflow = WorkflowService.duplicate_workflow(workflow, request.user)
    return Response(
        WorkflowDetailSerializer(new_workflow).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workflow_export(request, workflow_id):
    """Export a workflow to JSON"""
    workflow = get_object_or_404(Workflow, id=workflow_id, created_by=request.user)
    export_data = WorkflowService.export_workflow(workflow)
    return Response(export_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workflow_import(request):
    """Import a workflow from JSON"""
    try:
        workflow = WorkflowService.import_workflow(request.data, request.user)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execution_list(request):
    """List all executions"""
    executions = Execution.objects.filter(
        workflow__created_by=request.user
    ).select_related('workflow')
    
    # Filtering
    status_filter = request.query_params.get('status')
    workflow_filter = request.query_params.get('workflow')
    
    if status_filter:
        executions = executions.filter(status=status_filter)
    if workflow_filter:
        executions = executions.filter(workflow_id=workflow_filter)
    
    # Limit
    limit = int(request.query_params.get('limit', 50))
    executions = executions[:limit]
    
    serializer = ExecutionListSerializer(executions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execution_detail(request, execution_id):
    """Get execution details"""
    execution = get_object_or_404(
        Execution,
        id=execution_id,
        workflow__created_by=request.user
    )
    serializer = ExecutionDetailSerializer(execution)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execution_cancel(request, execution_id):
    """Cancel a running execution"""
    execution = get_object_or_404(
        Execution,
        id=execution_id,
        workflow__created_by=request.user
    )
    
    ExecutionEngine.cancel_execution(execution)
    return Response({'status': 'cancelled'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execution_retry(request, execution_id):
    """Retry a failed execution"""
    execution = get_object_or_404(
        Execution,
        id=execution_id,
        workflow__created_by=request.user
    )
    
    try:
        new_execution = ExecutionEngine.retry_execution(execution, request.user)
        return Response(
            ExecutionDetailSerializer(new_execution).data,
            status=status.HTTP_201_CREATED
        )
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execution_logs(request, execution_id):
    """Get execution logs"""
    execution = get_object_or_404(
        Execution,
        id=execution_id,
        workflow__created_by=request.user
    )
    
    logs = ExecutionLog.objects.filter(execution=execution)
    
    # Filter by level
    level = request.query_params.get('level')
    if level:
        logs = logs.filter(level=level)
    
    serializer = ExecutionLogSerializer(logs, many=True)
    return Response(serializer.data)


# ============================================
# Node Registry Endpoints
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def node_types(request):
    """Get all available node types"""
    # Get by category if requested
    by_category = request.query_params.get('by_category', 'false').lower() == 'true'
    
    if by_category:
        return Response(NodeRegistry.get_node_types_by_category())
    
    nodes = NodeRegistry.get_all_node_types()
    serializer = NodeTypeSerializer(nodes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def credential_list(request):
    """List or create credentials"""
    if request.method == 'GET':
        credentials = Credential.objects.filter(created_by=request.user)
        serializer = CredentialListSerializer(credentials, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CredentialDetailSerializer(data=request.data)
        if serializer.is_valid():
            credential = Credential.objects.create(
                created_by=request.user,
                **serializer.validated_data
            )
            return Response(
                CredentialListSerializer(credential).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def credential_detail(request, credential_id):
    """Get, update, or delete a credential"""
    credential = get_object_or_404(
        Credential,
        id=credential_id,
        created_by=request.user
    )
    
    if request.method == 'GET':
        # Don't return sensitive data
        serializer = CredentialListSerializer(credential)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CredentialDetailSerializer(credential, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(CredentialListSerializer(credential).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        credential.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Template Endpoints
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def template_list(request):
    """List workflow templates"""
    templates = WorkflowTemplate.objects.all()
    
    # Filter by category
    category = request.query_params.get('category')
    if category:
        templates = templates.filter(category=category)
    
    serializer = WorkflowTemplateSerializer(templates, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def template_detail(request, template_id):
    """Get template details"""
    template = get_object_or_404(WorkflowTemplate, id=template_id)
    serializer = WorkflowTemplateSerializer(template)
    return Response(serializer.data)


# ============================================
# Stats Endpoint
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    """Get workflow statistics for the current user"""
    stats_data = WorkflowService.get_workflow_stats(request.user)
    serializer = StatsSerializer(stats_data)
    return Response(serializer.data)
