"""Durgasman storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class CollectionStorageService(S3ModelStorage):
    """Storage service for API collections using S3 JSON storage."""
    
    def __init__(self):
        """Initialize collection storage service."""
        super().__init__(model_name='collections')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for collection index."""
        return {
            'uuid': data.get('uuid') or data.get('id'),
            'id': data.get('id') or data.get('uuid'),
            'name': data.get('name', ''),
            'user': data.get('user'),  # UUID string
            'created_at': data.get('created_at', ''),
        }
    
    def create_collection(
        self,
        name: str,
        description: str = '',
        user: Optional[str] = None,
        ai_docs: str = ''
    ) -> Dict[str, Any]:
        """Create a new collection."""
        collection_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        collection_data = {
            'id': collection_id,
            'name': name,
            'description': description,
            'user': user,
            'ai_docs': ai_docs,
            'created_at': now,
            'requests': [],  # ApiRequest data stored as nested list
            'mocks': [],  # MockEndpoint data stored as nested list
        }
        
        return self.create(collection_data, item_uuid=collection_id)
    
    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get collection by ID."""
        return self.get(collection_id)
    
    def update_collection(self, collection_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a collection."""
        return self.update(collection_id, kwargs)
    
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection."""
        return self.delete(collection_id)
    
    def add_request(
        self,
        collection_id: str,
        name: str,
        method: str,
        url: str,
        headers: Optional[List] = None,
        params: Optional[List] = None,
        body: str = '',
        auth_type: str = 'None',
        response_schema: str = ''
    ) -> Optional[Dict[str, Any]]:
        """Add an API request to a collection."""
        collection = self.get_collection(collection_id)
        if not collection:
            return None
        
        request_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        request_data = {
            'id': request_id,
            'name': name,
            'method': method,
            'url': url,
            'headers': headers or [],
            'params': params or [],
            'body': body,
            'auth_type': auth_type,
            'response_schema': response_schema,
            'created_at': now,
            'updated_at': now,
        }
        
        requests = collection.get('requests', [])
        requests.append(request_data)
        
        return self.update_collection(collection_id, {'requests': requests})
    
    def add_mock(
        self,
        collection_id: str,
        path: str,
        method: str,
        response_body: str,
        response_schema: str = '',
        status_code: int = 200,
        enabled: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Add a mock endpoint to a collection."""
        collection = self.get_collection(collection_id)
        if not collection:
            return None
        
        mock_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        mock_data = {
            'id': mock_id,
            'path': path,
            'method': method,
            'response_body': response_body,
            'response_schema': response_schema,
            'status_code': status_code,
            'enabled': enabled,
            'created_at': now,
        }
        
        mocks = collection.get('mocks', [])
        # Remove existing mock with same path+method if exists
        mocks = [m for m in mocks if not (m.get('path') == path and m.get('method') == method)]
        mocks.append(mock_data)
        
        return self.update_collection(collection_id, {'mocks': mocks})


class EnvironmentStorageService(S3ModelStorage):
    """Storage service for environments using S3 JSON storage."""
    
    def __init__(self):
        """Initialize environment storage service."""
        super().__init__(model_name='environments')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for environment index."""
        return {
            'uuid': data.get('uuid') or data.get('id'),
            'id': data.get('id') or data.get('uuid'),
            'name': data.get('name', ''),
            'user': data.get('user'),  # UUID string
            'created_at': data.get('created_at', ''),
        }
    
    def create_environment(
        self,
        name: str,
        user: Optional[str] = None,
        variables_list: Optional[List] = None
    ) -> Dict[str, Any]:
        """Create a new environment."""
        environment_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        environment_data = {
            'id': environment_id,
            'name': name,
            'user': user,
            'variables_list': variables_list or [],
            'created_at': now,
        }
        
        return self.create(environment_data, item_uuid=environment_id)
    
    def get_environment(self, environment_id: str) -> Optional[Dict[str, Any]]:
        """Get environment by ID."""
        return self.get(environment_id)
    
    def update_environment(self, environment_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update an environment."""
        return self.update(environment_id, kwargs)
    
    def delete_environment(self, environment_id: str) -> bool:
        """Delete an environment."""
        return self.delete(environment_id)
    
    def add_variable(
        self,
        environment_id: str,
        key: str,
        value: str,
        enabled: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Add a variable to an environment."""
        environment = self.get_environment(environment_id)
        if not environment:
            return None
        
        variables_list = environment.get('variables_list', [])
        # Remove existing variable with same key
        variables_list = [v for v in variables_list if v.get('key') != key]
        
        variables_list.append({
            'key': key,
            'value': value,
            'enabled': enabled,
        })
        
        return self.update_environment(environment_id, {'variables_list': variables_list})


class RequestHistoryStorageService(S3ModelStorage):
    """Storage service for request history using S3 JSON storage."""
    
    def __init__(self):
        """Initialize request history storage service."""
        super().__init__(model_name='request_history')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for history index."""
        return {
            'uuid': data.get('uuid') or data.get('id'),
            'id': data.get('id') or data.get('uuid'),
            'method': data.get('method', ''),
            'url': data.get('url', ''),
            'response_status': data.get('response_status', 0),
            'user': data.get('user'),  # UUID string
            'timestamp': data.get('timestamp', ''),
        }
    
    def create_history(
        self,
        method: str,
        url: str,
        request_headers: Optional[Dict] = None,
        request_body: str = '',
        response_status: int = 0,
        response_headers: Optional[Dict] = None,
        response_body: str = '',
        response_time_ms: int = 0,
        response_size_bytes: int = 0,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new request history entry."""
        history_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        history_data = {
            'id': history_id,
            'user': user,
            'timestamp': now,
            'method': method,
            'url': url,
            'request_headers': request_headers or {},
            'request_body': request_body,
            'response_status': response_status,
            'response_headers': response_headers or {},
            'response_body': response_body,
            'response_time_ms': response_time_ms,
            'response_size_bytes': response_size_bytes,
        }
        
        return self.create(history_data, item_uuid=history_id)
    
    def get_history(self, history_id: str) -> Optional[Dict[str, Any]]:
        """Get history entry by ID."""
        return self.get(history_id)
    
    def delete_history(self, history_id: str) -> bool:
        """Delete a history entry."""
        return self.delete(history_id)
