"""Response schemas for documentation API (ported from Lambda documentation.api)."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from apps.documentation.schemas.pydantic.models import PageDocumentation, EndpointDocumentation


class DocumentationPageResponse(PageDocumentation):
    """Documentation page response. Extends PageDocumentation."""
    model_config = ConfigDict(populate_by_name=True)


class DocumentationPageListResponse(BaseModel):
    """List of documentation pages response."""
    pages: List[DocumentationPageResponse]
    total: int


class EndpointDocumentationResponse(EndpointDocumentation):
    """Endpoint documentation response. Uses EndpointDocumentation model."""
    model_config = ConfigDict(populate_by_name=True)


class EndpointDocumentationListResponse(BaseModel):
    """List of endpoint documentation response."""
    endpoints: List[EndpointDocumentationResponse]
    total: int


class RelationshipGraphResponse(BaseModel):
    """Relationship graph response."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class RelationshipStatisticsResponse(BaseModel):
    """Relationship statistics response."""
    total_relationships: int
    unique_pages: int
    unique_endpoints: int
    by_api_version: Dict[str, int]
    total_endpoints_documented: int
    total_pages_documented: int
    endpoints_with_pages: int
    pages_with_endpoints: int


class ValidationResponse(BaseModel):
    """Validation response."""
    total_relationships: int
    issues: List[Dict[str, Any]]
    issue_count: int
    valid: bool


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class PageTypeListResponse(BaseModel):
    """Page type list with counts response."""
    types: List[Dict[str, Any]] = Field(..., description="List of page types with counts")
    total: int = Field(..., description="Total number of pages across all types")


class ApiVersionListResponse(BaseModel):
    """API version list with counts response."""
    versions: List[Dict[str, Any]] = Field(..., description="List of API versions with counts")
    total: int = Field(..., description="Total number of endpoints across all versions")


class MethodListResponse(BaseModel):
    """Method list with counts response."""
    methods: List[Dict[str, Any]] = Field(..., description="List of HTTP/GraphQL methods with counts")
    total: int = Field(..., description="Total number of endpoints across all methods")


class UsageTypeListResponse(BaseModel):
    """Usage type list with counts response."""
    usage_types: List[Dict[str, Any]] = Field(..., description="List of usage types with counts")
    total: int = Field(..., description="Total number of relationships across all usage types")


class UsageContextListResponse(BaseModel):
    """Usage context list with counts response."""
    usage_contexts: List[Dict[str, Any]] = Field(..., description="List of usage contexts with counts")
    total: int = Field(..., description="Total number of relationships across all usage contexts")


class TypeStatisticsResponse(BaseModel):
    """Page type statistics response."""
    page_type: str = Field(..., description="Page type")
    total: int = Field(..., description="Total pages of this type")
    published: int = Field(..., description="Published pages")
    draft: int = Field(..., description="Draft pages")
    deleted: int = Field(..., description="Deleted pages")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")


class RelationshipResponse(BaseModel):
    """Single relationship response."""
    relationship_id: str = Field(..., description="Relationship ID")
    page_path: str = Field(..., description="Page route")
    endpoint_path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP/GraphQL method")
    api_version: str = Field(..., description="API version")
    via_service: str = Field(..., description="Service name")
    via_hook: Optional[str] = Field(None, description="React hook name")
    usage_type: str = Field(..., description="Usage type")
    usage_context: str = Field(..., description="Usage context")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last updated timestamp")


class RelationshipListResponse(BaseModel):
    """List of relationships response."""
    relationships: List[RelationshipResponse]
    total: int


class EnhancedRelationshipResponse(BaseModel):
    """Enhanced relationship response with full context."""
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="_id", description="Unique identifier")
    relationship_id: str = Field(..., description="Composite relationship ID")
    page_path: Optional[str] = Field(None, description="Page route")
    endpoint_path: Optional[str] = Field(None, description="Endpoint path")
    method: Optional[str] = Field(None, description="HTTP/GraphQL method")
    api_version: Optional[str] = Field(None, description="API version")
    via_service: Optional[str] = Field(None, description="Service name")
    via_hook: Optional[str] = Field(None, description="React hook name")
    usage_type: Optional[str] = Field(None, description="Usage type")
    usage_context: Optional[str] = Field(None, description="Usage context")
    state: Optional[str] = Field(None, description="Relationship state")
    access_control: Optional[Dict[str, Any]] = Field(None, description="Access control")
    page_reference: Optional[Dict[str, Any]] = Field(None, description="Page reference")
    endpoint_reference: Optional[Dict[str, Any]] = Field(None, description="Endpoint reference")
    connection: Optional[Dict[str, Any]] = Field(None, description="Connection details")
    files: Optional[Dict[str, Any]] = Field(None, description="File references")
    data_flow: Optional[Dict[str, Any]] = Field(None, description="Data flow")
    postman_reference: Optional[Dict[str, Any]] = Field(None, description="Postman reference")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Dependencies")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last updated timestamp")


class PostmanConfigurationResponse(BaseModel):
    """Postman configuration response."""
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="_id", description="Unique configuration ID")
    config_id: str = Field(..., description="Configuration identifier")
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Description")
    state: str = Field(..., description="Configuration state")
    collection: Dict[str, Any] = Field(..., description="Postman collection")
    environments: List[Dict[str, Any]] = Field(default_factory=list, description="Environments")
    endpoint_mappings: List[Dict[str, Any]] = Field(default_factory=list, description="Endpoint mappings")
    test_suites: List[Dict[str, Any]] = Field(default_factory=list, description="Test suites")
    access_control: Optional[Dict[str, Any]] = Field(None, description="Access control")
    metadata: Dict[str, Any] = Field(..., description="Configuration metadata")


class PostmanStatisticsResponse(BaseModel):
    """Postman statistics response."""
    total_configurations: int = Field(..., description="Total configurations")
    by_state: Dict[str, int] = Field(..., description="Configurations by state")
    updated_at: str = Field(..., description="Last updated timestamp")


class StateStatisticsResponse(BaseModel):
    """Statistics by state response."""
    state: str = Field(..., description="State name")
    count: int = Field(..., description="Count of items in this state")
