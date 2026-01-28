"""Request schemas for documentation API (ported from Lambda documentation.api)."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from apps.documentation.schemas.pydantic.models import (
    PageMetadata,
    AccessControl,
    PageSections,
    DataReference,
    EndpointAccessControl,
    LambdaServices,
    EndpointFiles,
    EndpointMethods,
)


class DocumentationPageCreateRequest(BaseModel):
    """Create documentation page request."""
    page_id: str = Field(..., description="Unique page ID")
    metadata: PageMetadata = Field(..., description="Page metadata")
    content: str = Field(..., description="Markdown content")
    page_type: Optional[str] = Field(None, description="Page type: 'marketing', 'dashboard', or 'docs' (default)")


class DocumentationPageUpdateRequest(BaseModel):
    """Update documentation page request."""
    metadata: Optional[PageMetadata] = Field(None, description="Updated metadata (partial updates supported)")
    content: Optional[str] = Field(None, description="Updated markdown content")


class EndpointDocumentationCreateRequest(BaseModel):
    """Create endpoint documentation request."""
    endpoint_id: str = Field(..., description="Unique endpoint ID")
    endpoint_path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP/GraphQL method")
    api_version: str = Field(..., description="API version")
    service_file: Optional[str] = Field(None, description="Service file path (at least one of service_file or router_file required)")
    router_file: Optional[str] = Field(None, description="Router file path (at least one of service_file or router_file required)")
    service_methods: List[str] = Field(default_factory=list)
    repository_methods: List[str] = Field(default_factory=list)
    authentication: str = Field(default="Not specified")
    authorization: Optional[str] = None
    rate_limit: Optional[str] = None
    description: str = Field(..., description="Endpoint description")
    graphql_operation: Optional[str] = Field(None, description="GraphQL operation string")
    sql_file: Optional[str] = None
    used_by_pages: Optional[List[Dict[str, Any]]] = Field(None, description="List of pages using this endpoint")
    page_count: Optional[int] = Field(None, description="Number of pages (auto-calculated if not provided)")

    @model_validator(mode="after")
    def validate_file_reference(self) -> "EndpointDocumentationCreateRequest":
        if not self.service_file and not self.router_file:
            raise ValueError("At least one of 'service_file' or 'router_file' must be provided")
        return self


class RelationshipCreateRequest(BaseModel):
    """Create relationship request."""
    page_path: str = Field(..., description="Page route")
    endpoint_path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP/GraphQL method")
    api_version: str = Field(..., description="API version")
    via_service: str = Field(..., description="Service name")
    via_hook: Optional[str] = Field(None, description="React hook name")
    usage_type: str = Field(default="primary", description="Usage type: primary, secondary, or conditional")
    usage_context: str = Field(default="data_fetching", description="Usage context")


class PostmanConfigurationCreateRequest(BaseModel):
    """Create Postman configuration request."""
    config_id: str = Field(..., description="Unique configuration ID")
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Description")
    state: str = Field(default="development", description="Configuration state")
    collection: Dict[str, Any] = Field(..., description="Postman collection")
    environments: List[Dict[str, Any]] = Field(default_factory=list, description="Environments")
    access_control: Optional[Dict[str, Any]] = Field(None, description="Access control")
