"""
WorkerService - Django-Q integration for async workflow execution

Manages background task execution for workflows.
"""

import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class WorkerService:
    """Service for managing async workflow execution with Django-Q"""

    @classmethod
    def queue_execution(cls, execution_id: str) -> Optional[str]:
        """
        Queue a workflow execution for async processing.
        
        Args:
            execution_id: UUID of the execution to run
            
        Returns:
            Task ID if queued successfully, None otherwise
        """
        try:
            from django_q.tasks import async_task
            
            task_id = async_task(
                'apps.durgasflow.services.worker_service.run_execution_task',
                str(execution_id),
                task_name=f'durgasflow_execution_{execution_id}',
                group='durgasflow'
            )
            
            logger.info(f"Queued execution {execution_id} with task ID {task_id}")
            return task_id
            
        except ImportError:
            logger.warning("Django-Q not available, running synchronously")
            cls.run_execution_task(str(execution_id))
            return None
        except Exception as e:
            logger.error(f"Failed to queue execution {execution_id}: {e}")
            raise

    @classmethod
    def queue_scheduled_workflow(cls, workflow_id: str) -> Optional[str]:
        """
        Queue a scheduled workflow execution.
        
        Args:
            workflow_id: UUID of the workflow to execute
            
        Returns:
            Task ID if queued successfully
        """
        try:
            from django_q.tasks import async_task
            
            task_id = async_task(
                'apps.durgasflow.services.worker_service.run_scheduled_workflow_task',
                str(workflow_id),
                task_name=f'durgasflow_scheduled_{workflow_id}',
                group='durgasflow_scheduled'
            )
            
            logger.info(f"Queued scheduled workflow {workflow_id}")
            return task_id
            
        except ImportError:
            logger.warning("Django-Q not available")
            return None

    @classmethod
    def setup_schedule(cls, workflow_id: str, cron: str) -> None:
        """
        Set up a scheduled task for a workflow.
        
        Args:
            workflow_id: UUID of the workflow
            cron: Cron expression for the schedule
        """
        try:
            from django_q.models import Schedule
            
            # Remove existing schedule if any
            Schedule.objects.filter(name=f'durgasflow_cron_{workflow_id}').delete()
            
            # Create new schedule
            Schedule.objects.create(
                name=f'durgasflow_cron_{workflow_id}',
                func='apps.durgasflow.services.worker_service.run_scheduled_workflow_task',
                args=str(workflow_id),
                cron=cron,
                repeats=-1,  # Run indefinitely
            )
            
            logger.info(f"Created schedule for workflow {workflow_id}: {cron}")
            
        except ImportError:
            logger.warning("Django-Q not available for scheduling")

    @classmethod
    def remove_schedule(cls, workflow_id: str) -> None:
        """
        Remove scheduled task for a workflow.
        
        Args:
            workflow_id: UUID of the workflow
        """
        try:
            from django_q.models import Schedule
            
            deleted, _ = Schedule.objects.filter(
                name=f'durgasflow_cron_{workflow_id}'
            ).delete()
            
            if deleted:
                logger.info(f"Removed schedule for workflow {workflow_id}")
                
        except ImportError:
            pass


def run_execution_task(execution_id: str) -> dict:
    """
    Task function to run a workflow execution.
    
    This is called by Django-Q worker.
    
    Args:
        execution_id: UUID of the execution to run
        
    Returns:
        Result dict with status
    """
    from ..models import Execution
    from .execution_engine import ExecutionEngine
    
    try:
        execution = Execution.objects.get(id=execution_id)
        ExecutionEngine._run_execution(execution)
        
        return {
            'status': 'success',
            'execution_id': execution_id,
            'result_status': execution.status
        }
        
    except Execution.DoesNotExist:
        logger.error(f"Execution {execution_id} not found")
        return {
            'status': 'error',
            'error': 'Execution not found'
        }
    except Exception as e:
        logger.error(f"Execution {execution_id} failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


def run_scheduled_workflow_task(workflow_id: str) -> dict:
    """
    Task function to run a scheduled workflow.
    
    Args:
        workflow_id: UUID of the workflow to execute
        
    Returns:
        Result dict with status
    """
    from ..models import Workflow
    from .execution_engine import ExecutionEngine
    
    try:
        workflow = Workflow.objects.get(id=workflow_id, is_active=True)
        
        execution = ExecutionEngine.execute_workflow(
            workflow=workflow,
            trigger_type='schedule',
            trigger_data={'scheduled': True}
        )
        
        return {
            'status': 'success',
            'workflow_id': workflow_id,
            'execution_id': str(execution.id)
        }
        
    except Workflow.DoesNotExist:
        logger.warning(f"Scheduled workflow {workflow_id} not found or inactive")
        return {
            'status': 'skipped',
            'reason': 'Workflow not found or inactive'
        }
    except Exception as e:
        logger.error(f"Scheduled workflow {workflow_id} failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
