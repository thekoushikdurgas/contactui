"""Tasks views."""
import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from apps.core.decorators.auth import require_super_admin
from apps.tasks.services import TaskService

logger = logging.getLogger(__name__)


@require_super_admin
def list_tasks_view(request):
    """List all tasks."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    task_service = TaskService()
    
    # Get filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    task_type = request.GET.get('task_type')
    
    try:
        tasks = task_service.list_tasks(
            status=status,
            priority=priority,
            task_type=task_type,
            assigned_to=user_uuid,
            limit=50
        )
        
        # Calculate stats
        all_tasks = task_service.list_tasks(assigned_to=user_uuid)
        stats = {
            'total': len(all_tasks),
            'pending': len([t for t in all_tasks if t.get('status') == 'pending']),
            'in_progress': len([t for t in all_tasks if t.get('status') == 'in_progress']),
            'completed': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed': len([t for t in all_tasks if t.get('status') == 'failed']),
        }
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading tasks.')
        tasks = []
        stats = {'total': 0, 'pending': 0, 'in_progress': 0, 'completed': 0, 'failed': 0}
    
    context = {
        'tasks': tasks,
        'stats': stats,
        'empty_state_create_url': reverse('tasks:create'),
    }
    return render(request, 'tasks/list.html', context)


@require_super_admin
def task_detail_view(request, task_id):
    """Task detail view."""
    task_service = TaskService()
    
    try:
        task = task_service.get_task(task_id)
        if not task:
            messages.error(request, 'Task not found.')
            return redirect('tasks:list')
        
        # Get comments from task dictionary
        comments = task.get('comments', [])
        
        context = {'task': task, 'comments': comments}
    except Exception as e:
        logger.error(f"Error loading task {task_id}: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the task.')
        return redirect('tasks:list')
    
    return render(request, 'tasks/detail.html', context)


@require_super_admin
def task_start_view(request, task_id):
    """Set task status to in_progress (Start)."""
    task_service = TaskService()
    updated = task_service.update_task(task_id, status='in_progress')
    if updated:
        messages.success(request, 'Task started.')
    else:
        messages.error(request, 'Could not start task.')
    return redirect('tasks:detail', task_id=task_id)


@require_super_admin
def task_complete_view(request, task_id):
    """Set task status to completed (Complete)."""
    task_service = TaskService()
    updated = task_service.update_task(task_id, status='completed')
    if updated:
        messages.success(request, 'Task completed.')
    else:
        messages.error(request, 'Could not complete task.')
    return redirect('tasks:detail', task_id=task_id)


@require_super_admin
def task_form_view(request, task_id=None):
    """Task create/edit form."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    task_service = TaskService()
    task = None
    
    if request.method == 'POST':
        try:
            task_data = {
                'task_type': request.POST.get('task_type', 'documentation_sync'),
                'title': request.POST.get('title', ''),
                'description': request.POST.get('description', ''),
                'priority': request.POST.get('priority', 'medium'),
                'status': request.POST.get('status', 'pending')
            }
            
            if task_id:
                updated = task_service.update_task(task_id, **task_data)
                if updated:
                    messages.success(request, 'Task updated successfully.')
                    return redirect('tasks:detail', task_id=task_id)
            else:
                created = task_service.create_task(
                    task_type=task_data['task_type'],
                    title=task_data['title'],
                    description=task_data['description'],
                    priority=task_data['priority'],
                    created_by=user_uuid,
                    assigned_to=user_uuid if request.POST.get('assign_to_me') else None
                )
                if created:
                    task_id_str = created.get('task_id') or created.get('id') or created.get('uuid')
                    messages.success(request, 'Task created successfully.')
                    return redirect('tasks:detail', task_id=task_id_str)
        except Exception as e:
            logger.error(f"Error saving task: {e}", exc_info=True)
            messages.error(request, f'An error occurred: {str(e)}')
    
    if task_id:
        try:
            task = task_service.get_task(task_id)
            if not task:
                messages.error(request, 'Task not found.')
                return redirect('tasks:list')
        except Exception as e:
            logger.error(f"Error loading task {task_id}: {e}", exc_info=True)
            messages.error(request, 'An error occurred while loading the task.')
            return redirect('tasks:list')
    
    context = {
        'task': task,
        'is_edit': task_id is not None
    }
    
    return render(request, 'tasks/form.html', context)


@require_super_admin
@require_http_methods(["POST"])
@csrf_exempt
def task_create_api(request):
    """API endpoint to create a task."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    try:
        data = json.loads(request.body)
        task_service = TaskService()
        
        created = task_service.create_task(
            task_type=data.get('task_type', 'documentation_sync'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            assigned_to=user_uuid if data.get('assign_to_me') else None,
            created_by=user_uuid,
            metadata=data.get('metadata', {})
        )
        
        task_id = created.get('task_id') or created.get('id') or created.get('uuid')
        return JsonResponse({
            'success': True,
            'data': {
                'task_id': str(task_id),
                'title': created.get('title', ''),
                'status': created.get('status', 'pending')
            }
        }, status=201)
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_super_admin
@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def task_update_api(request, task_id):
    """API endpoint to update a task."""
    try:
        data = json.loads(request.body)
        task_service = TaskService()
        
        updated = task_service.update_task(task_id, **data)
        
        if updated:
            task_id_str = updated.get('task_id') or updated.get('id') or updated.get('uuid')
            return JsonResponse({
                'success': True,
                'data': {
                    'task_id': str(task_id_str),
                    'title': updated.get('title', ''),
                    'status': updated.get('status', 'pending')
                }
            })
        else:
            return JsonResponse({'error': 'Task not found'}, status=404)
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
