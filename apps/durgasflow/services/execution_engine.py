"""
ExecutionEngine - Workflow execution logic

Handles the execution of workflows, managing the flow between nodes.
"""

import logging
import traceback
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from django.utils import timezone

from .workflow_storage_service import WorkflowStorageService

logger = logging.getLogger(__name__)

# Constants (moved from models)
class ExecutionStatus:
    """Execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class TriggerType:
    """Types of workflow triggers"""
    MANUAL = 'manual'
    WEBHOOK = 'webhook'
    SCHEDULE = 'schedule'
    EVENT = 'event'


class NodeExecutionContext:
    """Context passed to each node during execution"""
    
    def __init__(
        self,
        execution: Dict[str, Any],
        workflow: Dict[str, Any],
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
        connections = self.workflow.get('connections', [])
        for conn in connections:
            if (str(conn.get('target_id')) == str(node_id) and 
                conn.get('target_input') == input_index):
                source_key = f"{conn.get('source_id')}_{conn.get('source_output')}"
                return self.node_outputs.get(source_key)
        return None
    
    def set_output_data(self, node_id: str, output_index: int, data: Any) -> None:
        """Set output data from a node"""
        key = f"{node_id}_{output_index}"
        self.node_outputs[key] = data


class ExecutionEngine:
    """Engine for executing workflows using S3 storage"""
    
    _storage = WorkflowStorageService()

    @classmethod
    def execute_workflow(
        cls,
        workflow: Dict[str, Any],
        trigger_type: str = TriggerType.MANUAL,
        trigger_data: Optional[Dict] = None,
        user_uuid: Optional[str] = None,
        async_execution: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow dict to execute
            trigger_type: How the workflow was triggered
            trigger_data: Data from the trigger
            user_uuid: User UUID who triggered the execution (optional)
            async_execution: Whether to run asynchronously with Django-Q
            
        Returns:
            Execution data dictionary
        """
        workflow_id = workflow.get('id') or workflow.get('workflow_id')
        
        # Convert user_uuid to string if needed
        if user_uuid:
            if hasattr(user_uuid, 'uuid'):
                user_uuid = str(user_uuid.uuid)
            elif hasattr(user_uuid, 'id'):
                user_uuid = str(user_uuid.id)
            else:
                user_uuid = str(user_uuid)
        
        # Create execution record in workflow
        execution_id = str(uuid_lib.uuid4())
        execution_data = {
            'execution_id': execution_id,
            'id': execution_id,
            'trigger_type': trigger_type,
            'trigger_data': trigger_data or {},
            'triggered_by': user_uuid,
            'status': ExecutionStatus.PENDING,
            'created_at': timezone.now().isoformat(),
            'started_at': None,
            'finished_at': None,
            'node_results': {},
            'logs': [],
        }
        
        # Add execution to workflow
        executions = workflow.get('executions', [])
        executions.append(execution_data)
        cls._storage.update_workflow(workflow_id, executions=executions)
        
        logger.info(f"Created execution {execution_id} for workflow {workflow_id}")
        
        if async_execution:
            # Queue for async execution
            from .worker_service import WorkerService
            WorkerService.queue_execution(execution_id, workflow_id)
            return execution_data
        
        # Execute synchronously
        cls._run_execution(execution_data, workflow, workflow_id)
        return execution_data

    @classmethod
    def _run_execution(cls, execution: Dict[str, Any], workflow: Dict[str, Any], workflow_id: str) -> None:
        """
        Run the actual execution logic.
        
        Args:
            execution: Execution dict to run
            workflow: Workflow dict
            workflow_id: Workflow ID
        """
        execution_id = execution.get('execution_id') or execution.get('id')
        
        try:
            # Update execution status to running
            execution['status'] = ExecutionStatus.RUNNING
            execution['started_at'] = timezone.now().isoformat()
            cls._update_execution_in_workflow(workflow_id, execution_id, execution)
            
            # Create execution context
            context = NodeExecutionContext(
                execution=execution,
                workflow=workflow,
                trigger_data=execution.get('trigger_data', {}),
                workflow_id=workflow_id,
                execution_id=execution_id
            )
            
            # Build execution order (topological sort)
            node_order = cls._get_execution_order(workflow)
            
            if not node_order:
                # No nodes to execute
                execution['status'] = ExecutionStatus.COMPLETED
                execution['finished_at'] = timezone.now().isoformat()
                execution['result_data'] = {'message': 'No nodes to execute'}
                cls._update_execution_in_workflow(workflow_id, execution_id, execution)
                return
            
            # Execute each node in order
            results = {}
            for node in node_order:
                try:
                    node_result = cls._execute_node(node, context, workflow_id, execution_id)
                    results[str(node.get('node_id'))] = {
                        'status': 'success',
                        'output': node_result
                    }
                except Exception as e:
                    results[str(node.get('node_id'))] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    # Log node error
                    cls._add_execution_log(workflow_id, execution_id, {
                        'node_id': node.get('node_id'),
                        'node_type': node.get('node_type'),
                        'node_title': node.get('title'),
                        'level': 'error',
                        'message': f"Node execution failed: {str(e)}",
                        'data': {'traceback': traceback.format_exc()},
                        'created_at': timezone.now().isoformat()
                    })
                    # Continue or stop based on settings
                    if not workflow.get('settings', {}).get('continue_on_error', False):
                        raise
            
            # Complete execution
            execution['node_results'] = results
            execution['status'] = ExecutionStatus.COMPLETED
            execution['finished_at'] = timezone.now().isoformat()
            execution['result_data'] = {'node_results': results}
            cls._update_execution_in_workflow(workflow_id, execution_id, execution)
            
            logger.info(f"Execution {execution_id} completed successfully")
            
        except Exception as e:
            error_message = str(e)
            error_stack = traceback.format_exc()
            
            logger.error(f"Execution {execution_id} failed: {error_message}")
            execution['status'] = ExecutionStatus.FAILED
            execution['finished_at'] = timezone.now().isoformat()
            execution['error_message'] = error_message
            execution['error_stack'] = error_stack
            cls._update_execution_in_workflow(workflow_id, execution_id, execution)
    
    @classmethod
    def _update_execution_in_workflow(cls, workflow_id: str, execution_id: str, execution_data: Dict[str, Any]) -> None:
        """Update execution in workflow's executions list"""
        workflow = cls._storage.get_workflow(workflow_id)
        if not workflow:
            return
        
        executions = workflow.get('executions', [])
        for i, exec_item in enumerate(executions):
            if exec_item.get('execution_id') == execution_id or exec_item.get('id') == execution_id:
                executions[i] = execution_data
                break
        
        cls._storage.update_workflow(workflow_id, executions=executions)
    
    @classmethod
    def _add_execution_log(cls, workflow_id: str, execution_id: str, log_data: Dict[str, Any]) -> None:
        """Add log entry to execution"""
        workflow = cls._storage.get_workflow(workflow_id)
        if not workflow:
            return
        
        executions = workflow.get('executions', [])
        for exec_item in executions:
            if exec_item.get('execution_id') == execution_id or exec_item.get('id') == execution_id:
                logs = exec_item.get('logs', [])
                logs.append(log_data)
                exec_item['logs'] = logs
                break
        
        cls._storage.update_workflow(workflow_id, executions=executions)

    @classmethod
    def _get_execution_order(cls, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get nodes in topological execution order.
        
        Nodes are executed from triggers/inputs to outputs.
        
        Args:
            workflow: Workflow dict to analyze
            
        Returns:
            List of node dicts in execution order
        """
        nodes = workflow.get('nodes', [])
        connections = workflow.get('connections', [])
        
        if not nodes:
            return []
        
        # Build adjacency list
        dependencies = {str(n.get('node_id')): set() for n in nodes}
        for conn in connections:
            target_id = str(conn.get('target_id'))
            source_id = str(conn.get('source_id'))
            if target_id in dependencies:
                dependencies[target_id].add(source_id)
        
        # Topological sort (Kahn's algorithm)
        result = []
        nodes_by_id = {str(n.get('node_id')): n for n in nodes}
        
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
                    if not deps and nid not in [str(n.get('node_id')) for n in result]:
                        ready.append(nid)
        
        # If we couldn't process all nodes, there might be a cycle
        if len(result) != len(nodes):
            logger.warning(f"Possible cycle detected in workflow {workflow.get('id')}")
            # Add remaining nodes anyway
            for node in nodes:
                if node not in result:
                    result.append(node)
        
        return result

    @classmethod
    def _execute_node(cls, node: Dict[str, Any], context: NodeExecutionContext, workflow_id: str, execution_id: str) -> Any:
        """
        Execute a single node.
        
        Args:
            node: Node dict to execute
            context: Execution context
            workflow_id: Workflow ID
            execution_id: Execution ID
            
        Returns:
            Node output data
        """
        from .node_registry import NodeRegistry
        
        node_id = node.get('node_id')
        node_type = node.get('node_type')
        node_title = node.get('title')
        
        # Log start
        log_entry = {
            'node_id': node_id,
            'node_type': node_type,
            'node_title': node_title,
            'level': 'info',
            'message': f"Executing node: {node_title or node_type}",
            'created_at': timezone.now().isoformat(),
            'finished_at': None
        }
        cls._add_execution_log(workflow_id, execution_id, log_entry)
        
        try:
            # Get node handler from registry
            handler = NodeRegistry.get_node_handler(node_type)
            
            if not handler:
                raise ValueError(f"Unknown node type: {node_type}")
            
            # Get input data
            input_data = context.get_input_data(node_id)
            
            # Execute node
            output_data = handler.execute(
                config=node.get('config', {}),
                input_data=input_data,
                context=context
            )
            
            # Store output
            outputs = node.get('outputs', [])
            for i in range(len(outputs) if outputs else 1):
                context.set_output_data(node_id, i, output_data)
            
            # Update log
            log_entry['finished_at'] = timezone.now().isoformat()
            log_entry['message'] = f"Node completed: {node_title or node_type}"
            log_entry['data'] = {'output_preview': str(output_data)[:500]}
            cls._add_execution_log(workflow_id, execution_id, log_entry)
            
            return output_data
            
        except Exception as e:
            log_entry['level'] = 'error'
            log_entry['message'] = f"Node failed: {str(e)}"
            log_entry['finished_at'] = timezone.now().isoformat()
            cls._add_execution_log(workflow_id, execution_id, log_entry)
            raise

    @classmethod
    def cancel_execution(cls, workflow_id: str, execution_id: str) -> None:
        """
        Cancel a running execution.
        
        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID to cancel
        """
        workflow = cls._storage.get_workflow(workflow_id)
        if not workflow:
            return
        
        executions = workflow.get('executions', [])
        for exec_item in executions:
            if exec_item.get('execution_id') == execution_id or exec_item.get('id') == execution_id:
                if exec_item.get('status') == ExecutionStatus.RUNNING:
                    exec_item['status'] = ExecutionStatus.CANCELLED
                    exec_item['finished_at'] = timezone.now().isoformat()
                    cls._update_execution_in_workflow(workflow_id, execution_id, exec_item)
                    logger.info(f"Cancelled execution {execution_id}")
                break

    @classmethod
    def retry_execution(cls, workflow_id: str, execution_id: str, user_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        Retry a failed execution.
        
        Args:
            workflow_id: Workflow ID
            execution_id: Failed execution ID to retry
            user_uuid: User UUID performing the retry
            
        Returns:
            New execution data dictionary
        """
        workflow = cls._storage.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Find the failed execution
        executions = workflow.get('executions', [])
        failed_execution = None
        for exec_item in executions:
            if exec_item.get('execution_id') == execution_id or exec_item.get('id') == execution_id:
                failed_execution = exec_item
                break
        
        if not failed_execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        retry_count = failed_execution.get('retry_count', 0)
        max_retries = failed_execution.get('max_retries', 3)
        
        if retry_count >= max_retries:
            raise ValueError("Maximum retries exceeded")
        
        # Convert user_uuid to string if needed
        if user_uuid:
            if hasattr(user_uuid, 'uuid'):
                user_uuid = str(user_uuid.uuid)
            elif hasattr(user_uuid, 'id'):
                user_uuid = str(user_uuid.id)
            else:
                user_uuid = str(user_uuid)
        
        # Create new execution as retry
        new_execution_id = str(uuid_lib.uuid4())
        new_execution = {
            'execution_id': new_execution_id,
            'id': new_execution_id,
            'trigger_type': failed_execution.get('trigger_type'),
            'trigger_data': failed_execution.get('trigger_data', {}),
            'triggered_by': user_uuid or failed_execution.get('triggered_by'),
            'retry_count': retry_count + 1,
            'max_retries': max_retries,
            'status': ExecutionStatus.PENDING,
            'created_at': timezone.now().isoformat(),
            'started_at': None,
            'finished_at': None,
            'node_results': {},
            'logs': [],
        }
        
        # Add to workflow executions
        executions.append(new_execution)
        cls._storage.update_workflow(workflow_id, executions=executions)
        
        cls._run_execution(new_execution, workflow, workflow_id)
        return new_execution
