"""
ExecutionEngine - Workflow execution logic

Handles the execution of workflows, managing the flow between nodes.
"""

import logging
import traceback
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from ..models import (
    Workflow, WorkflowNode, Execution, ExecutionLog,
    ExecutionStatus, TriggerType
)

User = get_user_model()
logger = logging.getLogger(__name__)


class NodeExecutionContext:
    """Context passed to each node during execution"""
    
    def __init__(
        self,
        execution: Execution,
        workflow: Workflow,
        trigger_data: Dict,
        credentials: Dict = None
    ):
        self.execution = execution
        self.workflow = workflow
        self.trigger_data = trigger_data
        self.credentials = credentials or {}
        self.node_outputs = {}  # Store outputs from each node
        self.variables = {}  # Workflow variables
    
    def get_input_data(self, node_id: str, input_index: int = 0) -> Any:
        """Get input data for a node from connected output"""
        # Find connection to this input
        for conn in self.workflow.connections.all():
            if str(conn.target_node.node_id) == str(node_id) and conn.target_input == input_index:
                source_key = f"{conn.source_node.node_id}_{conn.source_output}"
                return self.node_outputs.get(source_key)
        return None
    
    def set_output_data(self, node_id: str, output_index: int, data: Any) -> None:
        """Set output data from a node"""
        key = f"{node_id}_{output_index}"
        self.node_outputs[key] = data


class ExecutionEngine:
    """Engine for executing workflows"""

    @classmethod
    def execute_workflow(
        cls,
        workflow: Workflow,
        trigger_type: str = TriggerType.MANUAL,
        trigger_data: Optional[Dict] = None,
        user: Optional[User] = None,
        async_execution: bool = False
    ) -> Execution:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow to execute
            trigger_type: How the workflow was triggered
            trigger_data: Data from the trigger
            user: User who triggered the execution (optional)
            async_execution: Whether to run asynchronously with Django-Q
            
        Returns:
            Execution instance
        """
        # Create execution record
        execution = Execution.objects.create(
            workflow=workflow,
            trigger_type=trigger_type,
            trigger_data=trigger_data or {},
            triggered_by=user,
            status=ExecutionStatus.PENDING
        )
        
        logger.info(f"Created execution {execution.id} for workflow {workflow.id}")
        
        if async_execution:
            # Queue for async execution
            from .worker_service import WorkerService
            WorkerService.queue_execution(execution.id)
            return execution
        
        # Execute synchronously
        cls._run_execution(execution)
        return execution

    @classmethod
    def _run_execution(cls, execution: Execution) -> None:
        """
        Run the actual execution logic.
        
        Args:
            execution: Execution to run
        """
        workflow = execution.workflow
        
        try:
            execution.start()
            
            # Create execution context
            context = NodeExecutionContext(
                execution=execution,
                workflow=workflow,
                trigger_data=execution.trigger_data
            )
            
            # Build execution order (topological sort)
            node_order = cls._get_execution_order(workflow)
            
            if not node_order:
                # No nodes to execute
                execution.complete({'message': 'No nodes to execute'})
                return
            
            # Execute each node in order
            results = {}
            for node in node_order:
                try:
                    node_result = cls._execute_node(node, context)
                    results[str(node.node_id)] = {
                        'status': 'success',
                        'output': node_result
                    }
                except Exception as e:
                    results[str(node.node_id)] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    # Log node error
                    ExecutionLog.objects.create(
                        execution=execution,
                        node_id=node.node_id,
                        node_type=node.node_type,
                        node_title=node.title,
                        level='error',
                        message=f"Node execution failed: {str(e)}",
                        data={'traceback': traceback.format_exc()}
                    )
                    # Continue or stop based on settings
                    if not workflow.settings.get('continue_on_error', False):
                        raise
            
            # Complete execution
            execution.node_results = results
            execution.save(update_fields=['node_results'])
            execution.complete(result_data={'node_results': results})
            
            logger.info(f"Execution {execution.id} completed successfully")
            
        except Exception as e:
            error_message = str(e)
            error_stack = traceback.format_exc()
            
            logger.error(f"Execution {execution.id} failed: {error_message}")
            execution.fail(error_message, error_stack)

    @classmethod
    def _get_execution_order(cls, workflow: Workflow) -> List[WorkflowNode]:
        """
        Get nodes in topological execution order.
        
        Nodes are executed from triggers/inputs to outputs.
        
        Args:
            workflow: Workflow to analyze
            
        Returns:
            List of WorkflowNode in execution order
        """
        nodes = list(workflow.nodes.all())
        connections = list(workflow.connections.all())
        
        if not nodes:
            return []
        
        # Build adjacency list
        dependencies = {str(n.node_id): set() for n in nodes}
        for conn in connections:
            target_id = str(conn.target_node.node_id)
            source_id = str(conn.source_node.node_id)
            if target_id in dependencies:
                dependencies[target_id].add(source_id)
        
        # Topological sort (Kahn's algorithm)
        result = []
        nodes_by_id = {str(n.node_id): n for n in nodes}
        
        # Find nodes with no dependencies (usually triggers)
        ready = [nid for nid, deps in dependencies.items() if not deps]
        
        while ready:
            node_id = ready.pop(0)
            if node_id in nodes_by_id:
                result.append(nodes_by_id[node_id])
            
            # Remove this node from dependencies
            for nid, deps in dependencies.items():
                if node_id in deps:
                    deps.remove(node_id)
                    if not deps and nid not in [n.node_id for n in result]:
                        ready.append(nid)
        
        # If we couldn't process all nodes, there might be a cycle
        if len(result) != len(nodes):
            logger.warning(f"Possible cycle detected in workflow {workflow.id}")
            # Add remaining nodes anyway
            for node in nodes:
                if node not in result:
                    result.append(node)
        
        return result

    @classmethod
    def _execute_node(cls, node: WorkflowNode, context: NodeExecutionContext) -> Any:
        """
        Execute a single node.
        
        Args:
            node: Node to execute
            context: Execution context
            
        Returns:
            Node output data
        """
        from .node_registry import NodeRegistry
        
        # Log start
        log_entry = ExecutionLog.objects.create(
            execution=context.execution,
            node_id=node.node_id,
            node_type=node.node_type,
            node_title=node.title,
            level='info',
            message=f"Executing node: {node.title or node.node_type}",
            started_at=timezone.now()
        )
        
        try:
            # Get node handler from registry
            handler = NodeRegistry.get_node_handler(node.node_type)
            
            if not handler:
                raise ValueError(f"Unknown node type: {node.node_type}")
            
            # Get input data
            input_data = context.get_input_data(node.node_id)
            
            # Execute node
            output_data = handler.execute(
                config=node.config,
                input_data=input_data,
                context=context
            )
            
            # Store output
            for i in range(len(node.outputs) if node.outputs else 1):
                context.set_output_data(node.node_id, i, output_data)
            
            # Update log
            log_entry.finished_at = timezone.now()
            log_entry.message = f"Node completed: {node.title or node.node_type}"
            log_entry.data = {'output_preview': str(output_data)[:500]}
            log_entry.save()
            
            return output_data
            
        except Exception as e:
            log_entry.level = 'error'
            log_entry.message = f"Node failed: {str(e)}"
            log_entry.finished_at = timezone.now()
            log_entry.save()
            raise

    @classmethod
    def cancel_execution(cls, execution: Execution) -> None:
        """
        Cancel a running execution.
        
        Args:
            execution: Execution to cancel
        """
        if execution.status == ExecutionStatus.RUNNING:
            execution.status = ExecutionStatus.CANCELLED
            execution.finished_at = timezone.now()
            execution.save(update_fields=['status', 'finished_at', 'updated_at'])
            
            logger.info(f"Cancelled execution {execution.id}")

    @classmethod
    def retry_execution(cls, execution: Execution, user: Optional[User] = None) -> Execution:
        """
        Retry a failed execution.
        
        Args:
            execution: Failed execution to retry
            user: User performing the retry
            
        Returns:
            New Execution instance
        """
        if execution.retry_count >= execution.max_retries:
            raise ValueError("Maximum retries exceeded")
        
        # Create new execution as retry
        new_execution = Execution.objects.create(
            workflow=execution.workflow,
            trigger_type=execution.trigger_type,
            trigger_data=execution.trigger_data,
            triggered_by=user or execution.triggered_by,
            retry_count=execution.retry_count + 1,
            max_retries=execution.max_retries
        )
        
        cls._run_execution(new_execution)
        return new_execution
