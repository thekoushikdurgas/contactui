"""
Durgasflow Views - Workflow Automation UI

Template views for the workflow automation interface.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q

from .models import (
    Workflow, WorkflowNode, Execution, ExecutionLog,
    Credential, WorkflowTemplate, WorkflowStatus, ExecutionStatus
)
from .services.workflow_service import WorkflowService
from .services.execution_engine import ExecutionEngine


@login_required
def dashboard(request):
    """Main durgasflow dashboard"""
    user = request.user
    
    # Get user's workflows
    workflows = Workflow.objects.filter(created_by=user)[:5]
    
    # Get recent executions
    recent_executions = Execution.objects.filter(
        workflow__created_by=user
    ).select_related('workflow')[:10]
    
    # Statistics
    stats = {
        'total_workflows': Workflow.objects.filter(created_by=user).count(),
        'active_workflows': Workflow.objects.filter(created_by=user, is_active=True).count(),
        'total_executions': Execution.objects.filter(workflow__created_by=user).count(),
        'successful_executions': Execution.objects.filter(
            workflow__created_by=user,
            status=ExecutionStatus.COMPLETED
        ).count(),
        'failed_executions': Execution.objects.filter(
            workflow__created_by=user,
            status=ExecutionStatus.FAILED
        ).count(),
    }
    
    # Featured templates
    templates = WorkflowTemplate.objects.filter(is_featured=True)[:4]
    
    context = {
        'workflows': workflows,
        'recent_executions': recent_executions,
        'stats': stats,
        'templates': templates,
    }
    return render(request, 'durgasflow/dashboard.html', context)


@login_required
def workflow_list(request):
    """List all workflows"""
    user = request.user
    
    # Filtering
    status = request.GET.get('status', '')
    trigger = request.GET.get('trigger', '')
    search = request.GET.get('search', '')
    
    workflows = Workflow.objects.filter(created_by=user)
    
    if status:
        workflows = workflows.filter(status=status)
    if trigger:
        workflows = workflows.filter(trigger_type=trigger)
    if search:
        workflows = workflows.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(workflows, 12)
    page = request.GET.get('page', 1)
    workflows = paginator.get_page(page)
    
    context = {
        'workflows': workflows,
        'status_filter': status,
        'trigger_filter': trigger,
        'search': search,
        'status_choices': WorkflowStatus.choices,
    }
    return render(request, 'durgasflow/workflow_list.html', context)


@login_required
def workflow_create(request):
    """Create a new workflow"""
    if request.method == 'POST':
        name = request.POST.get('name', 'Untitled Workflow')
        description = request.POST.get('description', '')
        trigger_type = request.POST.get('trigger_type', 'manual')
        
        workflow = WorkflowService.create_workflow(
            name=name,
            description=description,
            trigger_type=trigger_type,
            user=request.user
        )
        
        messages.success(request, f'Workflow "{workflow.name}" created successfully.')
        return redirect('durgasflow:editor', workflow_id=workflow.id)
    
    return render(request, 'durgasflow/workflow_form.html', {
        'is_create': True,
    })


@login_required
def workflow_detail(request, workflow_id):
    """View workflow details"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    # Get recent executions for this workflow
    executions = Execution.objects.filter(workflow=workflow)[:10]
    
    context = {
        'workflow': workflow,
        'executions': executions,
    }
    return render(request, 'durgasflow/workflow_detail.html', context)


@login_required
def workflow_edit(request, workflow_id):
    """Edit workflow settings"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    if request.method == 'POST':
        workflow.name = request.POST.get('name', workflow.name)
        workflow.description = request.POST.get('description', workflow.description)
        workflow.trigger_type = request.POST.get('trigger_type', workflow.trigger_type)
        workflow.save()
        
        messages.success(request, f'Workflow "{workflow.name}" updated successfully.')
        return redirect('durgasflow:workflow_detail', workflow_id=workflow.id)
    
    context = {
        'workflow': workflow,
        'is_create': False,
    }
    return render(request, 'durgasflow/workflow_form.html', context)


@login_required
@require_POST
def workflow_delete(request, workflow_id):
    """Delete a workflow"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    name = workflow.name
    workflow.delete()
    
    messages.success(request, f'Workflow "{name}" deleted successfully.')
    return redirect('durgasflow:workflow_list')


@login_required
def editor(request, workflow_id):
    """Visual workflow editor"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    # Get available node types for the palette
    from .services.node_registry import NodeRegistry
    node_types = NodeRegistry.get_all_node_types()
    
    context = {
        'workflow': workflow,
        'graph_data': json.dumps(workflow.graph_data),
        'node_types': node_types,
    }
    return render(request, 'durgasflow/editor.html', context)


@login_required
def editor_new(request):
    """Create and open a new workflow in the editor"""
    workflow = WorkflowService.create_workflow(
        name='Untitled Workflow',
        user=request.user
    )
    return redirect('durgasflow:editor', workflow_id=workflow.id)


@login_required
def execution_list(request):
    """List all executions"""
    user = request.user
    
    # Filtering
    status = request.GET.get('status', '')
    workflow_id = request.GET.get('workflow', '')
    
    executions = Execution.objects.filter(
        workflow__created_by=user
    ).select_related('workflow')
    
    if status:
        executions = executions.filter(status=status)
    if workflow_id:
        executions = executions.filter(workflow_id=workflow_id)
    
    # Pagination
    paginator = Paginator(executions, 20)
    page = request.GET.get('page', 1)
    executions = paginator.get_page(page)
    
    # Get workflows for filter dropdown
    workflows = Workflow.objects.filter(created_by=user)
    
    context = {
        'executions': executions,
        'workflows': workflows,
        'status_filter': status,
        'workflow_filter': workflow_id,
        'status_choices': ExecutionStatus.choices,
    }
    return render(request, 'durgasflow/execution_list.html', context)


@login_required
def execution_detail(request, execution_id):
    """View execution details and logs"""
    execution = get_object_or_404(
        Execution,
        id=execution_id,
        workflow__created_by=request.user
    )
    
    logs = ExecutionLog.objects.filter(execution=execution)
    
    context = {
        'execution': execution,
        'logs': logs,
    }
    return render(request, 'durgasflow/execution_detail.html', context)


@login_required
@require_POST
def workflow_execute(request, workflow_id):
    """Manually execute a workflow"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    try:
        # Parse trigger data from request
        trigger_data = {}
        if request.content_type == 'application/json':
            trigger_data = json.loads(request.body) if request.body else {}
        
        execution = ExecutionEngine.execute_workflow(
            workflow=workflow,
            trigger_type='manual',
            trigger_data=trigger_data,
            user=request.user
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'execution_id': str(execution.id),
                'status': execution.status,
            })
        
        messages.success(request, 'Workflow execution started.')
        return redirect('durgasflow:execution_detail', execution_id=execution.id)
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=500)
        
        messages.error(request, f'Failed to execute workflow: {str(e)}')
        return redirect('durgasflow:workflow_detail', workflow_id=workflow.id)


@login_required
@require_POST
def workflow_activate(request, workflow_id):
    """Activate a workflow"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    workflow.activate()
    messages.success(request, f'Workflow "{workflow.name}" activated.')
    
    return redirect('durgasflow:workflow_detail', workflow_id=workflow.id)


@login_required
@require_POST
def workflow_deactivate(request, workflow_id):
    """Deactivate a workflow"""
    workflow = get_object_or_404(
        Workflow,
        id=workflow_id,
        created_by=request.user
    )
    
    workflow.deactivate()
    messages.success(request, f'Workflow "{workflow.name}" deactivated.')
    
    return redirect('durgasflow:workflow_detail', workflow_id=workflow.id)


@login_required
def credential_list(request):
    """List all credentials"""
    credentials = Credential.objects.filter(created_by=request.user)
    
    context = {
        'credentials': credentials,
    }
    return render(request, 'durgasflow/credential_list.html', context)


@login_required
def credential_create(request):
    """Create a new credential"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        credential_type = request.POST.get('credential_type', 'api_key')
        service_name = request.POST.get('service_name', '')
        description = request.POST.get('description', '')
        
        # Build credential data based on type
        data = {}
        if credential_type == 'api_key':
            data['api_key'] = request.POST.get('api_key', '')
        elif credential_type == 'basic_auth':
            data['username'] = request.POST.get('username', '')
            data['password'] = request.POST.get('password', '')
        elif credential_type == 'bearer_token':
            data['token'] = request.POST.get('token', '')
        elif credential_type == 'oauth2':
            data['client_id'] = request.POST.get('client_id', '')
            data['client_secret'] = request.POST.get('client_secret', '')
            data['access_token'] = request.POST.get('access_token', '')
            data['refresh_token'] = request.POST.get('refresh_token', '')
        
        credential = Credential.objects.create(
            name=name,
            credential_type=credential_type,
            service_name=service_name,
            description=description,
            data=data,
            created_by=request.user
        )
        
        messages.success(request, f'Credential "{credential.name}" created successfully.')
        return redirect('durgasflow:credential_list')
    
    return render(request, 'durgasflow/credential_form.html', {
        'is_create': True,
    })


@login_required
def credential_detail(request, credential_id):
    """View/edit credential details"""
    credential = get_object_or_404(
        Credential,
        id=credential_id,
        created_by=request.user
    )
    
    if request.method == 'POST':
        credential.name = request.POST.get('name', credential.name)
        credential.description = request.POST.get('description', credential.description)
        credential.service_name = request.POST.get('service_name', credential.service_name)
        credential.save()
        
        messages.success(request, f'Credential "{credential.name}" updated successfully.')
        return redirect('durgasflow:credential_list')
    
    context = {
        'credential': credential,
        'is_create': False,
    }
    return render(request, 'durgasflow/credential_form.html', context)


@login_required
@require_POST
def credential_delete(request, credential_id):
    """Delete a credential"""
    credential = get_object_or_404(
        Credential,
        id=credential_id,
        created_by=request.user
    )
    
    name = credential.name
    credential.delete()
    
    messages.success(request, f'Credential "{name}" deleted successfully.')
    return redirect('durgasflow:credential_list')


@login_required
def template_list(request):
    """List available workflow templates"""
    category = request.GET.get('category', '')
    
    templates = WorkflowTemplate.objects.all()
    
    if category:
        templates = templates.filter(category=category)
    
    context = {
        'templates': templates,
        'category_filter': category,
        'categories': WorkflowTemplate.TEMPLATE_CATEGORIES,
    }
    return render(request, 'durgasflow/template_list.html', context)


@login_required
@require_POST
def template_use(request, template_id):
    """Create a workflow from a template"""
    template = get_object_or_404(WorkflowTemplate, id=template_id)

    # Create workflow from template
    workflow = Workflow.objects.create(
        name=f"{template.name} (Copy)",
        description=template.description,
        graph_data=template.graph_data,
        created_by=request.user
    )

    # Increment template usage
    template.use_count += 1
    template.save(update_fields=['use_count'])

    messages.success(request, f'Workflow created from template "{template.name}".')
    return redirect('durgasflow:editor', workflow_id=workflow.id)


@login_required
@require_POST
def import_n8n_workflow(request, workflow_path):
    """
    Import an n8n workflow from the media directory.

    Args:
        workflow_path: Path to the n8n workflow file relative to media/n8n/
    """
    import os
    import json
    from pathlib import Path
    from django.conf import settings

    try:
        # Construct the full path to the n8n workflow file
        base_dir = Path(settings.BASE_DIR)
        n8n_dir = base_dir / 'media' / 'n8n'

        # Security check: ensure the path is within the n8n directory
        workflow_file = (n8n_dir / workflow_path).resolve()
        if not str(workflow_file).startswith(str(n8n_dir)):
            raise ValueError("Invalid workflow path")

        if not workflow_file.exists() or not workflow_file.is_file():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        # Read and parse the n8n workflow
        with open(workflow_file, 'r', encoding='utf-8') as f:
            n8n_data = json.load(f)

        # Import the workflow
        workflow = WorkflowService.import_n8n_workflow(n8n_data, request.user)

        # Add success message
        messages.success(
            request,
            f'Successfully imported n8n workflow "{workflow.name}". '
            f'Converted to durgasflow format with {len(workflow.nodes.all())} nodes.'
        )

        # Redirect to the editor
        return redirect('durgasflow:editor', workflow_id=workflow.id)

    except json.JSONDecodeError as e:
        messages.error(request, f'Invalid JSON in workflow file: {str(e)}')
        return redirect('documentation:media_manager_dashboard')
    except FileNotFoundError:
        messages.error(request, f'Workflow file not found: {workflow_path}')
        return redirect('documentation:media_manager_dashboard')
    except ValueError as e:
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('documentation:media_manager_dashboard')
    except Exception as e:
        logger.error(f"N8n workflow import failed: {e}", exc_info=True)
        messages.error(request, f'Import failed due to an unexpected error: {str(e)}')
        return redirect('documentation:media_manager_dashboard')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def webhook_handler(request, workflow_id, webhook_path):
    """Handle incoming webhooks for workflow triggers"""
    try:
        workflow = Workflow.objects.get(
            id=workflow_id,
            webhook_path=webhook_path,
            is_active=True,
            trigger_type='webhook'
        )
    except Workflow.DoesNotExist:
        return JsonResponse({'error': 'Workflow not found or inactive'}, status=404)
    
    # Validate webhook secret if set
    if workflow.webhook_secret:
        provided_secret = request.headers.get('X-Webhook-Secret', '')
        if provided_secret != workflow.webhook_secret:
            return JsonResponse({'error': 'Invalid webhook secret'}, status=403)
    
    # Build trigger data from request
    trigger_data = {
        'method': request.method,
        'headers': dict(request.headers),
        'query_params': dict(request.GET),
    }
    
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                trigger_data['body'] = json.loads(request.body)
            else:
                trigger_data['body'] = dict(request.POST)
        except json.JSONDecodeError:
            trigger_data['body'] = request.body.decode('utf-8', errors='replace')
    
    # Execute the workflow
    try:
        execution = ExecutionEngine.execute_workflow(
            workflow=workflow,
            trigger_type='webhook',
            trigger_data=trigger_data
        )
        
        return JsonResponse({
            'success': True,
            'execution_id': str(execution.id),
            'status': execution.status,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)
