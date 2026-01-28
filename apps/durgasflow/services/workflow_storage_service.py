"""Durgasflow workflow storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class WorkflowStorageService(S3ModelStorage):
    """Storage service for workflows using S3 JSON storage."""
    
    def __init__(self):
        """Initialize workflow storage service."""
        super().__init__(model_name='workflows')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for workflow index."""
        return {
            'uuid': data.get('uuid') or data.get('id'),
            'id': data.get('id') or data.get('uuid'),
            'name': data.get('name', ''),
            'status': data.get('status', 'draft'),
            'is_active': data.get('is_active', False),
            'trigger_type': data.get('trigger_type', 'manual'),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'last_executed_at': data.get('last_executed_at'),
        }
    
    def create_workflow(
        self,
        name: str,
        description: str = '',
        graph_data: Optional[Dict] = None,
        status: str = 'draft',
        trigger_type: str = 'manual',
        created_by: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new workflow."""
        workflow_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        workflow_data = {
            'id': workflow_id,
            'name': name,
            'description': description,
            'graph_data': graph_data or {},
            'status': status,
            'is_active': False,
            'trigger_type': trigger_type,
            'schedule_cron': kwargs.get('schedule_cron', ''),
            'webhook_path': kwargs.get('webhook_path', ''),
            'webhook_secret': kwargs.get('webhook_secret', ''),
            'tags': kwargs.get('tags', []),
            'settings': kwargs.get('settings', {}),
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
            'last_executed_at': None,
            'execution_count': 0,
            'success_count': 0,
            'failure_count': 0,
            'nodes': [],  # WorkflowNode data stored as nested list
            'connections': [],  # WorkflowConnection data stored as nested list
            'executions': [],  # Execution data stored as nested list
        }
        
        return self.create(workflow_data, item_uuid=workflow_id)
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        return self.get(workflow_id)
    
    def update_workflow(self, workflow_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a workflow."""
        return self.update(workflow_id, kwargs)
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        return self.delete(workflow_id)
    
    def add_node(
        self,
        workflow_id: str,
        node_id: str,
        node_type: str,
        category: str = 'action',
        title: str = '',
        position_x: float = 0,
        position_y: float = 0,
        config: Optional[Dict] = None,
        inputs: Optional[List] = None,
        outputs: Optional[List] = None,
        properties: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a node to a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        node_data = {
            'id': str(uuid_lib.uuid4()),
            'node_id': node_id,
            'node_type': node_type,
            'category': category,
            'title': title,
            'position_x': position_x,
            'position_y': position_y,
            'config': config or {},
            'inputs': inputs or [],
            'outputs': outputs or [],
            'properties': properties or {},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        nodes = workflow.get('nodes', [])
        # Remove existing node with same node_id if exists
        nodes = [n for n in nodes if n.get('node_id') != node_id]
        nodes.append(node_data)
        
        return self.update_workflow(workflow_id, {'nodes': nodes})
    
    def add_connection(
        self,
        workflow_id: str,
        source_node_id: str,
        target_node_id: str,
        source_output: int = 0,
        target_input: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Add a connection between nodes."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        connection_data = {
            'id': str(uuid_lib.uuid4()),
            'source_node_id': source_node_id,
            'target_node_id': target_node_id,
            'source_output': source_output,
            'target_input': target_input,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        connections = workflow.get('connections', [])
        connections.append(connection_data)
        
        return self.update_workflow(workflow_id, {'connections': connections})
    
    def create_execution(
        self,
        workflow_id: str,
        trigger_type: str = 'manual',
        trigger_data: Optional[Dict] = None,
        triggered_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new execution for a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        execution_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        execution_data = {
            'id': execution_id,
            'status': 'pending',
            'trigger_type': trigger_type,
            'trigger_data': trigger_data or {},
            'started_at': None,
            'finished_at': None,
            'result_data': {},
            'error_message': '',
            'error_stack': '',
            'node_results': {},
            'retry_count': 0,
            'max_retries': 3,
            'triggered_by': triggered_by,
            'created_at': now,
            'updated_at': now,
            'logs': [],  # ExecutionLog data stored as nested list
        }
        
        executions = workflow.get('executions', [])
        executions.append(execution_data)
        
        return self.update_workflow(workflow_id, {'executions': executions})
    
    def update_execution(
        self,
        workflow_id: str,
        execution_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update an execution."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        executions = workflow.get('executions', [])
        execution_found = False
        
        for i, execution in enumerate(executions):
            if execution.get('id') == execution_id:
                # Handle status timestamp updates
                if 'status' in kwargs:
                    if kwargs['status'] == 'running' and not execution.get('started_at'):
                        kwargs['started_at'] = datetime.utcnow().isoformat()
                    elif kwargs['status'] in ['completed', 'failed', 'cancelled'] and not execution.get('finished_at'):
                        kwargs['finished_at'] = datetime.utcnow().isoformat()
                
                executions[i] = {**execution, **kwargs, 'updated_at': datetime.utcnow().isoformat()}
                execution_found = True
                break
        
        if not execution_found:
            return None
        
        # Update workflow statistics
        workflow_stats = {
            'execution_count': len(executions),
            'success_count': len([e for e in executions if e.get('status') == 'completed']),
            'failure_count': len([e for e in executions if e.get('status') == 'failed']),
        }
        
        latest_execution = executions[-1] if executions else None
        if latest_execution and latest_execution.get('finished_at'):
            workflow_stats['last_executed_at'] = latest_execution.get('finished_at')
        
        return self.update_workflow(workflow_id, {
            'executions': executions,
            **workflow_stats
        })
    
    def add_execution_log(
        self,
        workflow_id: str,
        execution_id: str,
        node_id: str,
        node_type: str,
        level: str,
        message: str,
        data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a log entry to an execution."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        executions = workflow.get('executions', [])
        execution = None
        execution_index = None
        
        for i, exec_item in enumerate(executions):
            if exec_item.get('id') == execution_id:
                execution = exec_item
                execution_index = i
                break
        
        if not execution:
            return None
        
        log_data = {
            'id': str(uuid_lib.uuid4()),
            'node_id': node_id,
            'node_type': node_type,
            'node_title': '',
            'level': level,
            'message': message,
            'data': data or {},
            'started_at': None,
            'finished_at': None,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        logs = execution.get('logs', [])
        logs.append(log_data)
        executions[execution_index] = {**execution, 'logs': logs}
        
        return self.update_workflow(workflow_id, {'executions': executions})


class CredentialStorageService(S3ModelStorage):
    """Storage service for credentials using S3 JSON storage."""
    
    def __init__(self):
        """Initialize credential storage service."""
        super().__init__(model_name='credentials')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for credential index."""
        return {
            'uuid': data.get('uuid') or data.get('id'),
            'id': data.get('id') or data.get('uuid'),
            'name': data.get('name', ''),
            'credential_type': data.get('credential_type', 'api_key'),
            'service_name': data.get('service_name', ''),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'last_used_at': data.get('last_used_at'),
        }
    
    def create_credential(
        self,
        name: str,
        credential_type: str = 'api_key',
        service_name: str = '',
        data: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new credential."""
        credential_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        credential_data = {
            'id': credential_id,
            'name': name,
            'description': '',
            'credential_type': credential_type,
            'service_name': service_name,
            'data': data or {},  # Encrypted credential data
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
            'last_used_at': None,
        }
        
        return self.create(credential_data, item_uuid=credential_id)
    
    def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """Get credential by ID."""
        return self.get(credential_id)
    
    def update_credential(self, credential_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a credential."""
        return self.update(credential_id, kwargs)
    
    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential."""
        return self.delete(credential_id)


class WorkflowTemplateStorageService(S3ModelStorage):
    """Storage service for workflow templates using S3 JSON storage."""
    
    def __init__(self):
        """Initialize workflow template storage service."""
        super().__init__(model_name='workflow_templates')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for template index."""
        return {
            'uuid': data.get('uuid') or data.get('id'),
            'id': data.get('id') or data.get('uuid'),
            'name': data.get('name', ''),
            'category': data.get('category', 'automation'),
            'is_featured': data.get('is_featured', False),
            'use_count': data.get('use_count', 0),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
    
    def create_template(
        self,
        name: str,
        description: str = '',
        category: str = 'automation',
        graph_data: Optional[Dict] = None,
        thumbnail_url: str = '',
        tags: Optional[List[str]] = None,
        is_featured: bool = False
    ) -> Dict[str, Any]:
        """Create a new workflow template."""
        template_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        template_data = {
            'id': template_id,
            'name': name,
            'description': description,
            'category': category,
            'graph_data': graph_data or {},
            'thumbnail_url': thumbnail_url,
            'tags': tags or [],
            'is_featured': is_featured,
            'use_count': 0,
            'created_at': now,
            'updated_at': now,
        }
        
        return self.create(template_data, item_uuid=template_id)
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        return self.get(template_id)
    
    def update_template(self, template_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a template."""
        return self.update(template_id, kwargs)
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        return self.delete(template_id)
