"""
Test fixtures and factories for documentation app tests.

Provides:
- Test data factories
- Mock services
- Mock API clients
- Test data generators
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# Test Data Factories
# ============================================================================

class PageFactory:
    """Factory for creating test page data."""
    
    @staticmethod
    def create(
        page_id: Optional[str] = None,
        page_type: str = "docs",
        page_state: str = "draft",
        status: str = "active",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test page dictionary."""
        page_id = page_id or f"test-page-{hash(str(kwargs)) % 10000}"
        
        default_page = {
            "page_id": page_id,
            "page_type": page_type,
            "page_state": page_state,
            "status": status,
            "metadata": {
                "route": f"/{page_id}",
                "title": f"Test Page {page_id}",
                "description": f"Test description for {page_id}",
            },
            "content": {
                "sections": [
                    {
                        "type": "heading",
                        "level": 1,
                        "text": f"Test Heading for {page_id}"
                    }
                ]
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        default_page.update(kwargs)
        return default_page
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple test pages."""
        return [PageFactory.create(page_id=f"test-page-{i}", **kwargs) for i in range(count)]


class EndpointFactory:
    """Factory for creating test endpoint data."""
    
    @staticmethod
    def create(
        endpoint_id: Optional[str] = None,
        method: str = "GET",
        route: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test endpoint dictionary."""
        endpoint_id = endpoint_id or f"test-endpoint-{hash(str(kwargs)) % 10000}"
        route = route or f"/api/v1/{endpoint_id}"
        
        default_endpoint = {
            "endpoint_id": endpoint_id,
            "method": method,
            "route": route,
            "api_version": "v1",
            "metadata": {
                "summary": f"Test endpoint {endpoint_id}",
                "description": f"Test description for {endpoint_id}",
            },
            "request": {
                "headers": {},
                "query_params": {},
                "body": {}
            },
            "response": {
                "status_code": 200,
                "headers": {},
                "body": {}
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        default_endpoint.update(kwargs)
        return default_endpoint
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple test endpoints."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        return [
            EndpointFactory.create(
                endpoint_id=f"test-endpoint-{i}",
                method=methods[i % len(methods)],
                **kwargs
            )
            for i in range(count)
        ]


class RelationshipFactory:
    """Factory for creating test relationship data."""
    
    @staticmethod
    def create(
        relationship_id: Optional[str] = None,
        source_type: str = "page",
        target_type: str = "page",
        relationship_type: str = "references",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test relationship dictionary."""
        relationship_id = relationship_id or f"test-rel-{hash(str(kwargs)) % 10000}"
        
        default_relationship = {
            "relationship_id": relationship_id,
            "source_type": source_type,
            "source_id": f"source-{relationship_id}",
            "target_type": target_type,
            "target_id": f"target-{relationship_id}",
            "relationship_type": relationship_type,
            "metadata": {
                "description": f"Test relationship {relationship_id}",
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        default_relationship.update(kwargs)
        return default_relationship
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple test relationships."""
        return [
            RelationshipFactory.create(
                relationship_id=f"test-rel-{i}",
                **kwargs
            )
            for i in range(count)
        ]


# ============================================================================
# Mock Services
# ============================================================================

class MockPagesService:
    """Mock PagesService for testing."""
    
    def __init__(self):
        self.pages = {}
        self._next_id = 1
    
    def list_pages(self, **filters) -> Dict[str, Any]:
        """List pages with optional filters."""
        pages = list(self.pages.values())
        
        # Apply filters
        if "page_type" in filters:
            pages = [p for p in pages if p.get("page_type") == filters["page_type"]]
        if "page_state" in filters:
            pages = [p for p in pages if p.get("page_state") == filters["page_state"]]
        if "status" in filters:
            pages = [p for p in pages if p.get("status") == filters["status"]]
        
        return {
            "pages": pages,
            "total": len(pages)
        }
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a single page."""
        return self.pages.get(page_id)
    
    def create_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new page."""
        page_id = page_data.get("page_id", f"page-{self._next_id}")
        self._next_id += 1
        
        page = {
            **page_data,
            "page_id": page_id,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        self.pages[page_id] = page
        return page
    
    def update_page(self, page_id: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing page."""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        self.pages[page_id].update(page_data)
        self.pages[page_id]["updated_at"] = "2024-01-01T00:00:00Z"
        return self.pages[page_id]
    
    def delete_page(self, page_id: str) -> bool:
        """Delete a page."""
        if page_id not in self.pages:
            return False
        del self.pages[page_id]
        return True


class MockUnifiedStorage:
    """Mock UnifiedStorage for testing."""
    
    def __init__(self):
        self.pages = {}
        self.endpoints = {}
        self.relationships = {}
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a page."""
        return self.pages.get(page_id)
    
    def list_pages(self, **filters) -> Dict[str, Any]:
        """List pages."""
        pages = list(self.pages.values())
        if "page_type" in filters:
            pages = [p for p in pages if p.get("page_type") == filters["page_type"]]
        return {"pages": pages, "total": len(pages)}
    
    def create_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a page."""
        page_id = page_data.get("page_id")
        self.pages[page_id] = page_data
        return page_data
    
    def update_page(self, page_id: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a page."""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        self.pages[page_id].update(page_data)
        return self.pages[page_id]
    
    def delete_page(self, page_id: str) -> bool:
        """Delete a page."""
        if page_id in self.pages:
            del self.pages[page_id]
            return True
        return False


# ============================================================================
# Mock API Clients
# ============================================================================

class MockLambdaAPIClient:
    """Mock LambdaAPIClient for testing."""
    
    def __init__(self):
        self.responses = {}
        self.requests = []
    
    def set_response(self, endpoint: str, method: str, response: Dict[str, Any], status_code: int = 200):
        """Set a mock response for an endpoint."""
        key = f"{method}:{endpoint}"
        self.responses[key] = {
            "status_code": status_code,
            "data": response
        }
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a mock request."""
        key = f"{method}:{endpoint}"
        self.requests.append({
            "method": method,
            "endpoint": endpoint,
            "data": data,
            **kwargs
        })
        
        if key in self.responses:
            response = self.responses[key]
            if response["status_code"] >= 400:
                from apps.core.exceptions import LambdaAPIError
                raise LambdaAPIError(
                    f"Mock error: {response['status_code']}",
                    endpoint=endpoint,
                    status_code=response["status_code"]
                )
            return response["data"]
        
        # Default response
        return {"success": True, "data": {}}


class MockGraphQLService:
    """Mock GraphQLDocumentationService for testing."""
    
    def __init__(self):
        self.responses = {}
        self.queries = []
    
    def set_response(self, query: str, response: Dict[str, Any]):
        """Set a mock response for a query."""
        self.responses[query] = response
    
    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a mock GraphQL query."""
        self.queries.append({"query": query, "variables": variables})
        
        if query in self.responses:
            return self.responses[query]
        
        # Default response
        return {"data": {}}


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_random_page_data(**overrides) -> Dict[str, Any]:
    """Generate random page data for testing."""
    import random
    import string
    
    page_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    page_type = random.choice(["docs", "marketing", "dashboard"])
    page_state = random.choice(["draft", "published", "archived"])
    status = random.choice(["active", "inactive"])
    
    return PageFactory.create(
        page_id=page_id,
        page_type=page_type,
        page_state=page_state,
        status=status,
        **overrides
    )


def generate_random_endpoint_data(**overrides) -> Dict[str, Any]:
    """Generate random endpoint data for testing."""
    import random
    import string
    
    endpoint_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    method = random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])
    
    return EndpointFactory.create(
        endpoint_id=endpoint_id,
        method=method,
        **overrides
    )


def generate_random_relationship_data(**overrides) -> Dict[str, Any]:
    """Generate random relationship data for testing."""
    import random
    
    relationship_type = random.choice([
        "references",
        "depends_on",
        "related_to",
        "includes"
    ])
    
    return RelationshipFactory.create(
        relationship_type=relationship_type,
        **overrides
    )
