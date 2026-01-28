"""
Pydantic schemas for API request validation.

These schemas define the structure and validation rules for API requests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============= Common Schemas =============

class PaginationQuery(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items to return")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")


class FilterQuery(BaseModel):
    """Common filter query parameters."""
    search: Optional[str] = Field(default=None, max_length=200, description="Search query")
    status: Optional[str] = Field(default=None, description="Filter by status")
    type: Optional[str] = Field(default=None, description="Filter by type")


# ============= Page Schemas =============

class PageCreateSchema(BaseModel):
    """Schema for creating a page."""
    page_id: str = Field(..., min_length=1, max_length=200, description="Unique page identifier")
    page_type: str = Field(..., description="Page type: docs, marketing, or dashboard")
    title: Optional[str] = Field(default=None, max_length=500, description="Page title")
    description: Optional[str] = Field(default=None, max_length=2000, description="Page description")
    content: Optional[str] = Field(default=None, description="Page content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Page metadata")
    
    @field_validator("page_type")
    @classmethod
    def validate_page_type(cls, v: str) -> str:
        """Validate page type."""
        valid_types = ["docs", "marketing", "dashboard"]
        if v not in valid_types:
            raise ValueError(f"page_type must be one of {valid_types}")
        return v
    
    @field_validator("page_id")
    @classmethod
    def validate_page_id(cls, v: str) -> str:
        """Validate page ID format."""
        if not v or not v.strip():
            raise ValueError("page_id cannot be empty")
        # Allow alphanumeric, underscore, hyphen
        if not all(c.isalnum() or c in ("_", "-") for c in v):
            raise ValueError("page_id can only contain alphanumeric characters, underscores, and hyphens")
        return v.strip()


class PageUpdateSchema(BaseModel):
    """Schema for updating a page."""
    page_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    page_type: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)
    content: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator("page_type")
    @classmethod
    def validate_page_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate page type if provided."""
        if v is None:
            return v
        valid_types = ["docs", "marketing", "dashboard"]
        if v not in valid_types:
            raise ValueError(f"page_type must be one of {valid_types}")
        return v


class PageListQuerySchema(PaginationQuery, FilterQuery):
    """Schema for page list query parameters."""
    page_type: Optional[str] = Field(default=None, description="Filter by page type")
    status: Optional[str] = Field(default=None, description="Filter by status")


class PageDetailPathSchema(BaseModel):
    """Schema for page detail path parameters."""
    page_id: str = Field(..., min_length=1, max_length=200, description="Page ID")
    tab: Optional[str] = Field(default=None, description="Detail tab to show")


# ============= Endpoint Schemas =============

class EndpointCreateSchema(BaseModel):
    """Schema for creating an endpoint."""
    endpoint_id: str = Field(..., min_length=1, max_length=200, description="Unique endpoint identifier")
    endpoint_path: str = Field(..., min_length=1, max_length=500, description="Endpoint path")
    method: str = Field(..., description="HTTP/GraphQL method")
    api_version: str = Field(..., description="API version")
    description: Optional[str] = Field(default=None, max_length=2000, description="Endpoint description")
    request_schema: Optional[Dict[str, Any]] = Field(default=None, description="Request schema")
    response_schema: Optional[Dict[str, Any]] = Field(default=None, description="Response schema")
    
    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate and normalize method."""
        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
        v_upper = v.upper()
        if v_upper not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}")
        return v_upper
    
    @field_validator("endpoint_id")
    @classmethod
    def validate_endpoint_id(cls, v: str) -> str:
        """Validate endpoint ID format."""
        if not v or not v.strip():
            raise ValueError("endpoint_id cannot be empty")
        return v.strip()


class EndpointUpdateSchema(BaseModel):
    """Schema for updating an endpoint."""
    endpoint_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    endpoint_path: Optional[str] = Field(default=None, min_length=1, max_length=500)
    method: Optional[str] = Field(default=None)
    api_version: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=2000)
    request_schema: Optional[Dict[str, Any]] = Field(default=None)
    response_schema: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator("method")
    @classmethod
    def validate_method(cls, v: Optional[str]) -> Optional[str]:
        """Validate method if provided."""
        if v is None:
            return v
        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
        v_upper = v.upper()
        if v_upper not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}")
        return v_upper


class EndpointListQuerySchema(PaginationQuery, FilterQuery):
    """Schema for endpoint list query parameters."""
    method: Optional[str] = Field(default=None, description="Filter by HTTP method")
    api_version: Optional[str] = Field(default=None, description="Filter by API version")


class EndpointDetailPathSchema(BaseModel):
    """Schema for endpoint detail path parameters."""
    endpoint_id: str = Field(..., min_length=1, max_length=200, description="Endpoint ID")
    tab: Optional[str] = Field(default=None, description="Detail tab to show")


# ============= Relationship Schemas =============

class RelationshipCreateSchema(BaseModel):
    """Schema for creating a relationship."""
    relationship_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    page_id: str = Field(..., min_length=1, max_length=200, description="Page ID")
    endpoint_id: str = Field(..., min_length=1, max_length=200, description="Endpoint ID")
    usage_type: str = Field(default="primary", description="Usage type")
    usage_context: str = Field(default="data_fetching", description="Usage context")
    method: Optional[str] = Field(default=None, description="HTTP/GraphQL method")
    
    @field_validator("usage_type")
    @classmethod
    def validate_usage_type(cls, v: str) -> str:
        """Validate usage type."""
        valid_types = ["primary", "secondary", "conditional", "lazy", "prefetch"]
        if v not in valid_types:
            raise ValueError(f"usage_type must be one of {valid_types}")
        return v
    
    @field_validator("usage_context")
    @classmethod
    def validate_usage_context(cls, v: str) -> str:
        """Validate usage context."""
        valid_contexts = ["data_fetching", "data_mutation", "authentication", "analytics", "realtime", "background"]
        if v not in valid_contexts:
            raise ValueError(f"usage_context must be one of {valid_contexts}")
        return v
    
    @field_validator("method")
    @classmethod
    def validate_method(cls, v: Optional[str]) -> Optional[str]:
        """Validate method if provided."""
        if v is None:
            return v
        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
        v_upper = v.upper()
        if v_upper not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}")
        return v_upper


class RelationshipUpdateSchema(BaseModel):
    """Schema for updating a relationship."""
    page_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    endpoint_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    usage_type: Optional[str] = Field(default=None)
    usage_context: Optional[str] = Field(default=None)
    method: Optional[str] = Field(default=None)
    
    @field_validator("usage_type")
    @classmethod
    def validate_usage_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate usage type if provided."""
        if v is None:
            return v
        valid_types = ["primary", "secondary", "conditional", "lazy", "prefetch"]
        if v not in valid_types:
            raise ValueError(f"usage_type must be one of {valid_types}")
        return v
    
    @field_validator("usage_context")
    @classmethod
    def validate_usage_context(cls, v: Optional[str]) -> Optional[str]:
        """Validate usage context if provided."""
        if v is None:
            return v
        valid_contexts = ["data_fetching", "data_mutation", "authentication", "analytics", "realtime", "background"]
        if v not in valid_contexts:
            raise ValueError(f"usage_context must be one of {valid_contexts}")
        return v


class RelationshipListQuerySchema(PaginationQuery, FilterQuery):
    """Schema for relationship list query parameters."""
    usage_type: Optional[str] = Field(default=None, description="Filter by usage type")
    usage_context: Optional[str] = Field(default=None, description="Filter by usage context")


class RelationshipDetailPathSchema(BaseModel):
    """Schema for relationship detail path parameters."""
    relationship_id: str = Field(..., min_length=1, max_length=200, description="Relationship ID")
    tab: Optional[str] = Field(default=None, description="Detail tab to show")


# ============= Media Schemas =============

class MediaFileCreateSchema(BaseModel):
    """Schema for creating a media file."""
    resource_type: str = Field(..., description="Resource type: pages, endpoints, relationships, or postman")
    data: Dict[str, Any] = Field(..., description="File data (JSON object)")
    auto_sync: bool = Field(default=False, description="Automatically sync to S3")
    
    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        """Validate resource type."""
        valid_types = ["pages", "endpoints", "relationships", "postman"]
        if v not in valid_types:
            raise ValueError(f"resource_type must be one of {valid_types}")
        return v


class MediaFileUpdateSchema(BaseModel):
    """Schema for updating a media file."""
    data: Dict[str, Any] = Field(..., description="File data (JSON object)")
    auto_sync: bool = Field(default=False, description="Automatically sync to S3")


class MediaFileSyncSchema(BaseModel):
    """Schema for syncing a media file."""
    direction: str = Field(default="to_lambda", description="Sync direction: to_lambda or from_lambda")
    
    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate sync direction."""
        valid_directions = ["to_lambda", "from_lambda"]
        if v not in valid_directions:
            raise ValueError(f"direction must be one of {valid_directions}")
        return v


# ============= Postman Schemas =============

class PostmanCreateSchema(BaseModel):
    """Schema for creating a Postman configuration."""
    config_id: str = Field(..., min_length=1, max_length=200, description="Configuration ID")
    name: str = Field(..., min_length=1, max_length=500, description="Configuration name")
    state: str = Field(default="draft", description="Configuration state")
    collection: Optional[Dict[str, Any]] = Field(default=None, description="Postman collection")
    environments: Optional[Dict[str, Any]] = Field(default=None, description="Postman environments")
    
    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Validate state."""
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v


class PostmanUpdateSchema(BaseModel):
    """Schema for updating a Postman configuration."""
    config_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    name: Optional[str] = Field(default=None, min_length=1, max_length=500)
    state: Optional[str] = Field(default=None)
    collection: Optional[Dict[str, Any]] = Field(default=None)
    environments: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Validate state if provided."""
        if v is None:
            return v
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v


class PostmanListQuerySchema(PaginationQuery, FilterQuery):
    """Schema for Postman list query parameters."""
    state: Optional[str] = Field(default=None, description="Filter by state")


class PostmanDetailPathSchema(BaseModel):
    """Schema for Postman detail path parameters."""
    postman_id: str = Field(..., min_length=1, max_length=200, description="Postman configuration ID")
    tab: Optional[str] = Field(default=None, description="Detail tab to show")
