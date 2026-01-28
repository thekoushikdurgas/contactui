"""Detailed Pydantic models matching the docs structure exactly (ported from Lambda documentation.api)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============= SHARED ACCESS CONTROL MODELS =============

class UserRoleAccess(BaseModel):
    """Access control for a user role on pages."""
    can_view: bool = Field(True, description="Can view the resource")
    can_edit: bool = Field(False, description="Can edit the resource")
    can_delete: bool = Field(False, description="Can delete the resource")
    restricted_components: List[str] = Field(default_factory=list, description="Components this role cannot access")


class RoleAccess(UserRoleAccess):
    """Backward-compatible alias for page role access."""
    pass


class AccessControl(BaseModel):
    """Access control for all user types on pages."""
    super_admin: UserRoleAccess = Field(
        default_factory=lambda: UserRoleAccess(can_view=True, can_edit=True, can_delete=True)
    )
    admin: UserRoleAccess = Field(
        default_factory=lambda: UserRoleAccess(can_view=True, can_edit=True, can_delete=False)
    )
    pro_user: UserRoleAccess = Field(
        default_factory=lambda: UserRoleAccess(can_view=True, can_edit=False, can_delete=False)
    )
    free_user: UserRoleAccess = Field(
        default_factory=lambda: UserRoleAccess(can_view=True, can_edit=False, can_delete=False)
    )
    guest: UserRoleAccess = Field(
        default_factory=lambda: UserRoleAccess(can_view=False, can_edit=False, can_delete=False)
    )


# ============= PAGE SECTION MODELS =============

class HeadingElement(BaseModel):
    """Heading element in page sections."""
    id: str = Field(..., description="Unique heading ID")
    text: str = Field(..., description="Heading text")
    level: int = Field(..., ge=1, le=6, description="Heading level 1-6")


class TabElement(BaseModel):
    """Tab element in page sections."""
    id: str = Field(..., description="Unique tab ID")
    label: str = Field(..., description="Tab label")
    content_ref: str = Field(..., description="Reference to tab content")


class ButtonElement(BaseModel):
    """Button element in page sections."""
    id: str = Field(..., description="Unique button ID")
    label: str = Field(..., description="Button label")
    action: str = Field(..., description="Button action")
    variant: str = Field("primary", description="Button variant style")


class InputBoxElement(BaseModel):
    """Input box element in page sections."""
    id: str = Field(..., description="Unique input ID")
    label: str = Field(..., description="Input label")
    input_type: str = Field("text", description="Input type")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    required: bool = Field(False, description="Is input required")


class TextBlockElement(BaseModel):
    """Text block element in page sections."""
    id: str = Field(..., description="Unique text block ID")
    content: str = Field(..., description="Text content")
    format: str = Field("markdown", description="Content format")


class ComponentReference(BaseModel):
    """Reference to a component."""
    name: str = Field(..., description="Component name")
    file_path: str = Field(..., description="Component file path")
    props: Dict[str, Any] = Field(default_factory=dict, description="Component props")


class ServiceReference(BaseModel):
    """Reference to a service."""
    name: str = Field(..., description="Service name")
    file_path: str = Field(..., description="Service file path")
    methods: List[str] = Field(default_factory=list, description="Service methods used")


class HookReference(BaseModel):
    """Reference to a React hook."""
    name: str = Field(..., description="Hook name")
    file_path: str = Field(..., description="Hook file path")
    dependencies: List[str] = Field(default_factory=list, description="Hook dependencies")


class ContextReference(BaseModel):
    """Reference to a React context."""
    name: str = Field(..., description="Context name")
    file_path: str = Field(..., description="Context file path")
    provider: Optional[str] = Field(None, description="Context provider component")


class UtilityReference(BaseModel):
    """Reference to a utility function."""
    name: str = Field(..., description="Utility name")
    file_path: str = Field(..., description="Utility file path")
    functions: List[str] = Field(default_factory=list, description="Functions used")


class EndpointReferenceInSection(BaseModel):
    """Reference to an endpoint in page sections."""
    endpoint_id: str = Field(..., description="Endpoint ID")
    endpoint_path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP/GraphQL method")
    file_path: Optional[str] = Field(None, description="File where endpoint is used")


class PageSections(BaseModel):
    """All section elements for a page."""
    headings: List[HeadingElement] = Field(default_factory=list, description="Heading elements")
    subheadings: List[HeadingElement] = Field(default_factory=list, description="Subheading elements")
    tabs: List[TabElement] = Field(default_factory=list, description="Tab elements")
    buttons: List[ButtonElement] = Field(default_factory=list, description="Button elements")
    input_boxes: List[InputBoxElement] = Field(default_factory=list, description="Input box elements")
    text_blocks: List[TextBlockElement] = Field(default_factory=list, description="Text block elements")
    components: List[ComponentReference] = Field(default_factory=list, description="Component references")
    utilities: List[UtilityReference] = Field(default_factory=list, description="Utility references")
    services: List[ServiceReference] = Field(default_factory=list, description="Service references")
    hooks: List[HookReference] = Field(default_factory=list, description="Hook references")
    contexts: List[ContextReference] = Field(default_factory=list, description="Context references")
    ui_components: List[ComponentReference] = Field(default_factory=list, description="UI component references")
    endpoints: List[EndpointReferenceInSection] = Field(default_factory=list, description="Endpoint references")


class DataReference(BaseModel):
    """Reference to data files (fallback, mock, demo)."""
    name: str = Field(..., description="Data name")
    file_path: str = Field(..., description="Data file path")
    description: Optional[str] = Field(None, description="Data description")


# ============= PAGE MODELS =============

class PageEndpointUsage(BaseModel):
    """Represents endpoint usage in a page's metadata."""
    endpoint_path: str = Field(..., description="Endpoint path (e.g., 'graphql/GetUserStats')")
    method: str = Field(..., description="HTTP/GraphQL method (QUERY, MUTATION, GET, POST, etc.)")
    api_version: str = Field(..., description="API version (e.g., 'graphql')")
    via_service: str = Field(..., description="Service name that uses this endpoint")
    via_hook: Optional[str] = Field(None, description="React hook name that uses this endpoint")
    usage_type: str = Field(..., description="Usage type: primary, secondary, or conditional")
    usage_context: str = Field(..., description="Usage context: data_fetching, data_mutation, authentication, or analytics")
    description: Optional[str] = Field(None, description="Description of how this endpoint is used")

    @field_validator("usage_type")
    @classmethod
    def validate_usage_type(cls, v: str) -> str:
        valid_types = ["primary", "secondary", "conditional", "lazy", "prefetch"]
        if v not in valid_types:
            raise ValueError(f"usage_type must be one of {valid_types}, got {v}")
        return v

    @field_validator("usage_context")
    @classmethod
    def validate_usage_context(cls, v: str) -> str:
        valid_contexts = ["data_fetching", "data_mutation", "authentication", "analytics", "realtime", "background"]
        if v not in valid_contexts:
            raise ValueError(f"usage_context must be one of {valid_contexts}, got {v}")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
        if v.upper() not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}, got {v}")
        return v.upper()


class UIComponent(BaseModel):
    """Represents a UI component reference in page metadata."""
    name: str = Field(..., description="Component name")
    file_path: str = Field(..., description="Component file path")


class PageMetadata(BaseModel):
    """Complete page metadata structure matching docs format."""
    route: str = Field(..., description="Page route (e.g., '/dashboard')")
    file_path: str = Field(..., description="Source file path")
    purpose: str = Field(..., description="Page purpose/description")
    s3_key: str = Field(..., description="S3 key for JSON file (format: data/pages/{page_id}.json)")
    status: str = Field("published", description="Status: draft, published, archived, deleted")
    authentication: str = Field("Not required", description="Authentication requirement/notes")
    authorization: Optional[str] = Field(None, description="Authorization requirement/notes")
    page_state: str = Field("development", description="Page state: coming_soon, published, draft, development, test")
    last_updated: str = Field(..., description="Last updated timestamp (ISO 8601)")
    uses_endpoints: List[PageEndpointUsage] = Field(default_factory=list, description="List of endpoints used by this page")
    ui_components: List[UIComponent] = Field(default_factory=list, description="List of UI components used by this page")
    versions: List[str] = Field(default_factory=list, description="Page version history")
    endpoint_count: int = Field(default=0, description="Number of endpoints used (should match uses_endpoints.length)")
    api_versions: List[str] = Field(default_factory=list, description="List of API versions used (derived from uses_endpoints)")
    content_sections: Optional[Dict[str, Any]] = Field(None, description="Content sections structure")

    @field_validator("page_state")
    @classmethod
    def validate_page_state(cls, v: str) -> str:
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if v not in valid_states:
            raise ValueError(f"page_state must be one of {valid_states}, got {v}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["draft", "published", "archived", "deleted"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}, got {v}")
        return v

    @field_validator("route", mode="before")
    @classmethod
    def validate_route(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "/"
        v = v.strip()
        if not v or v == "/":
            return "/"
        if not v.startswith("/"):
            if len(v) > 50 or "error" in v.lower() or "boundary" in v.lower():
                return "/"
            return "/" + v.lstrip("/")
        return v

    @field_validator("file_path", mode="before")
    @classmethod
    def validate_file_path(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v) if v else ""

    @field_validator("purpose", mode="before")
    @classmethod
    def validate_purpose(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v) if v else ""

    @field_validator("authentication", mode="before")
    @classmethod
    def validate_authentication(cls, v: Any) -> str:
        if v is None:
            return "Not required"
        return str(v) if v else "Not required"

    @model_validator(mode="after")
    def validate_computed_fields(self) -> "PageMetadata":
        if self.endpoint_count != len(self.uses_endpoints):
            self.endpoint_count = len(self.uses_endpoints)
        api_versions_set = set()
        for endpoint in self.uses_endpoints:
            api_versions_set.add(endpoint.api_version)
        self.api_versions = sorted(list(api_versions_set))
        return self


class PageDocumentation(BaseModel):
    """Complete page documentation structure matching docs format."""
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="_id", description="Unique identifier (format: '{page_id}-001')")
    page_id: str = Field(..., description="Page identifier")
    page_type: str = Field(..., description="Page type: dashboard, marketing, or docs")
    metadata: PageMetadata = Field(..., description="Page metadata")
    content: Optional[str] = Field(None, description="Page content (markdown format, stored in JSON)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    access_control: Optional[AccessControl] = Field(None, description="Access control settings")
    sections: Optional[PageSections] = Field(None, description="Page section elements")
    fallback_data: List[DataReference] = Field(default_factory=list, description="Fallback data references")
    mock_data: List[DataReference] = Field(default_factory=list, description="Mock data references")
    demo_data: List[DataReference] = Field(default_factory=list, description="Demo data references")

    @field_validator("page_type")
    @classmethod
    def validate_page_type(cls, v: str) -> str:
        valid_types = ["dashboard", "marketing", "docs"]
        if v not in valid_types:
            raise ValueError(f"page_type must be one of {valid_types}, got {v}")
        return v

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        return v


# ============= ENDPOINT MODELS =============

class EndpointRoleAccess(BaseModel):
    """Access control for a user role on endpoints."""
    can_access: bool = Field(True, description="Can access the endpoint")
    can_execute: bool = Field(True, description="Can execute the endpoint")
    rate_limit: Optional[str] = Field(None, description="Rate limit for this role")
    restricted_fields: List[str] = Field(default_factory=list, description="Fields this role cannot access")


class EndpointAccessControl(BaseModel):
    """Access control for all user types on endpoints."""
    super_admin: EndpointRoleAccess = Field(default_factory=lambda: EndpointRoleAccess(can_access=True, can_execute=True))
    admin: EndpointRoleAccess = Field(default_factory=lambda: EndpointRoleAccess(can_access=True, can_execute=True))
    pro_user: EndpointRoleAccess = Field(default_factory=lambda: EndpointRoleAccess(can_access=True, can_execute=True, rate_limit="100/hour"))
    free_user: EndpointRoleAccess = Field(default_factory=lambda: EndpointRoleAccess(can_access=True, can_execute=True, rate_limit="20/hour"))
    guest: EndpointRoleAccess = Field(default_factory=lambda: EndpointRoleAccess(can_access=False, can_execute=False))


class DependencyLambdaService(BaseModel):
    """A Lambda service dependency."""
    service_name: str = Field(..., description="Service name")
    function_name: str = Field(..., description="Lambda function name")
    invocation_type: str = Field("sync", description="Invocation type: sync or async")
    purpose: str = Field(..., description="Purpose of this dependency")


class PrimaryLambdaService(BaseModel):
    """Primary Lambda service for an endpoint."""
    service_name: str = Field(..., description="Service name")
    function_name: str = Field(..., description="Lambda function name")
    runtime: str = Field("python3.11", description="Lambda runtime")
    memory_mb: int = Field(256, description="Memory allocation in MB")
    timeout_seconds: int = Field(30, description="Timeout in seconds")


class LambdaServices(BaseModel):
    """Lambda services configuration for an endpoint."""
    primary: Optional[PrimaryLambdaService] = Field(None, description="Primary Lambda service")
    dependencies: List[DependencyLambdaService] = Field(default_factory=list, description="Dependent Lambda services")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class EndpointFiles(BaseModel):
    """File references for an endpoint."""
    service_file: Optional[str] = Field(None, description="Service file path")
    router_file: Optional[str] = Field(None, description="Router file path")
    repository_file: Optional[str] = Field(None, description="Repository file path")
    schema_file: Optional[str] = Field(None, description="Schema file path")
    test_file: Optional[str] = Field(None, description="Test file path")
    graphql_file: Optional[str] = Field(None, description="GraphQL file path")
    sql_file: Optional[str] = Field(None, description="SQL file path")


class EndpointMethods(BaseModel):
    """Method references for an endpoint."""
    service_methods: List[str] = Field(default_factory=list, description="Service methods")
    repository_methods: List[str] = Field(default_factory=list, description="Repository methods")
    validation_methods: List[str] = Field(default_factory=list, description="Validation methods")
    middleware_methods: List[str] = Field(default_factory=list, description="Middleware methods")


class EndpointPageUsage(BaseModel):
    """Represents page usage in an endpoint's used_by_pages array."""
    page_path: str = Field(..., description="Page route (e.g., '/login')")
    page_title: str = Field(..., description="Page title")
    via_service: str = Field(..., description="Service name")
    via_hook: Optional[str] = Field(None, description="React hook name")
    usage_type: str = Field(..., description="Usage type: primary, secondary, or conditional")
    usage_context: str = Field(..., description="Usage context")
    updated_at: Optional[str] = Field(None, description="Last updated timestamp (ISO 8601)")

    @field_validator("usage_type")
    @classmethod
    def validate_usage_type(cls, v: str) -> str:
        valid_types = ["primary", "secondary", "conditional", "lazy", "prefetch"]
        if v not in valid_types:
            raise ValueError(f"usage_type must be one of {valid_types}, got {v}")
        return v

    @field_validator("usage_context")
    @classmethod
    def validate_usage_context(cls, v: str) -> str:
        valid_contexts = ["data_fetching", "data_mutation", "authentication", "analytics", "realtime", "background"]
        if v not in valid_contexts:
            raise ValueError(f"usage_context must be one of {valid_contexts}, got {v}")
        return v


class EndpointDocumentation(BaseModel):
    """Complete endpoint documentation structure matching docs format.
    Note: validate_file_reference omitted for response parsing (S3 payloads may lack file refs).
    """
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="_id", description="Unique identifier (format: '{endpoint_id}-001')")
    endpoint_id: str = Field(..., description="Endpoint identifier")
    endpoint_path: str = Field(..., description="Endpoint path (e.g., 'graphql/Login' or 'Login')")
    method: str = Field(..., description="HTTP/GraphQL method")
    api_version: str = Field(..., description="API version (e.g., 'graphql')")
    description: str = Field(..., description="Endpoint description")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Update timestamp (ISO 8601)")
    endpoint_state: str = Field("development", description="Endpoint state: coming_soon, published, draft, development, test")
    service_file: Optional[str] = Field(None, description="Service file path")
    router_file: Optional[str] = Field(None, description="Router file path")
    service_methods: List[str] = Field(default_factory=list, description="Service methods")
    repository_methods: List[str] = Field(default_factory=list, description="Repository methods")
    used_by_pages: List[EndpointPageUsage] = Field(default_factory=list, description="List of pages using this endpoint")
    rate_limit: Optional[str] = Field(None, description="Rate limit information")
    graphql_operation: Optional[str] = Field(None, description="GraphQL operation string")
    sql_file: Optional[str] = Field(None, description="SQL file reference")
    page_count: int = Field(default=0, description="Number of pages using this endpoint (should match used_by_pages.length)")
    access_control: Optional[EndpointAccessControl] = Field(None, description="Access control settings")
    lambda_services: Optional[LambdaServices] = Field(None, description="Lambda services configuration")
    files: Optional[EndpointFiles] = Field(None, description="File references")
    methods: Optional[EndpointMethods] = Field(None, description="Method references")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
        if v.upper() not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}, got {v}")
        return v.upper()

    @field_validator("endpoint_state")
    @classmethod
    def validate_endpoint_state(cls, v: str) -> str:
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if v not in valid_states:
            raise ValueError(f"endpoint_state must be one of {valid_states}, got {v}")
        return v

    @model_validator(mode="after")
    def validate_page_count(self) -> "EndpointDocumentation":
        if self.page_count != len(self.used_by_pages):
            self.page_count = len(self.used_by_pages)
        return self


# ============= RELATIONSHIP MODELS =============

class RelationshipRoleAccess(BaseModel):
    """Access control for a user role on relationships."""
    can_view: bool = Field(True, description="Can view the relationship")
    can_edit: bool = Field(False, description="Can edit the relationship")
    can_delete: bool = Field(False, description="Can delete the relationship")


class RelationshipAccessControl(BaseModel):
    """Access control for all user types on relationships."""
    super_admin: RelationshipRoleAccess = Field(default_factory=lambda: RelationshipRoleAccess(can_view=True, can_edit=True, can_delete=True))
    admin: RelationshipRoleAccess = Field(default_factory=lambda: RelationshipRoleAccess(can_view=True, can_edit=True, can_delete=False))
    pro_user: RelationshipRoleAccess = Field(default_factory=lambda: RelationshipRoleAccess(can_view=True, can_edit=False, can_delete=False))
    free_user: RelationshipRoleAccess = Field(default_factory=lambda: RelationshipRoleAccess(can_view=True, can_edit=False, can_delete=False))
    guest: RelationshipRoleAccess = Field(default_factory=lambda: RelationshipRoleAccess(can_view=False, can_edit=False, can_delete=False))


class PageReference(BaseModel):
    """Reference to a page in a relationship."""
    page_id: str = Field(..., description="Page ID")
    page_path: str = Field(..., description="Page route")
    page_title: str = Field(..., description="Page title")
    page_type: str = Field(..., description="Page type")
    page_state: str = Field(..., description="Page state")
    file_path: str = Field(..., description="Page component file path")


class EndpointRef(BaseModel):
    """Reference to an endpoint in a relationship."""
    endpoint_id: str = Field(..., description="Endpoint ID")
    endpoint_path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP/GraphQL method")
    api_version: str = Field(..., description="API version")
    endpoint_state: str = Field(..., description="Endpoint state")
    description: Optional[str] = Field(None, description="Endpoint description")
    lambda_service: Optional[str] = Field(None, description="Lambda service name")


class RelationshipConnection(BaseModel):
    """Connection details between page and endpoint."""
    via_service: str = Field(..., description="Service name")
    via_hook: Optional[str] = Field(None, description="React hook name")
    usage_type: str = Field("primary", description="Usage type")
    usage_context: str = Field("data_fetching", description="Usage context")
    invocation_pattern: str = Field("on_mount", description="When API is called")
    caching_strategy: Optional[str] = Field(None, description="Caching approach")
    retry_policy: Optional[Dict[str, Any]] = Field(None, description="Retry configuration")


class RelationshipMetadata(BaseModel):
    """Metadata for a relationship."""
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator")
    last_updated_by: Optional[str] = Field(None, description="Last updater")
    version: str = Field("1.0.0", description="Relationship version")
    tags: List[str] = Field(default_factory=list, description="Tags")
    notes: Optional[str] = Field(None, description="Notes")


class EnhancedRelationship(BaseModel):
    """Enhanced relationship model with full context."""
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="_id", description="Unique identifier")
    relationship_id: str = Field(..., description="Composite relationship ID")
    state: str = Field("development", description="Relationship state")
    access_control: Optional[RelationshipAccessControl] = Field(None, description="Access control")
    page_reference: Optional[PageReference] = Field(None, description="Page reference")
    endpoint_reference: Optional[EndpointRef] = Field(None, description="Endpoint reference")
    connection: Optional[RelationshipConnection] = Field(None, description="Connection details")
    files: Optional[Dict[str, Any]] = Field(None, description="File references")
    data_flow: Optional[Dict[str, Any]] = Field(None, description="Data flow")
    postman_reference: Optional[Dict[str, Any]] = Field(None, description="Postman reference")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Dependencies")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    metadata: Optional[RelationshipMetadata] = Field(None, description="Metadata")
    page_path: Optional[str] = Field(None, description="Page route")
    endpoint_path: Optional[str] = Field(None, description="Endpoint path")
    method: Optional[str] = Field(None, description="HTTP/GraphQL method")
    api_version: Optional[str] = Field(None, description="API version")
    via_service: Optional[str] = Field(None, description="Service name")
    via_hook: Optional[str] = Field(None, description="React hook name")
    usage_type: Optional[str] = Field(None, description="Usage type")
    usage_context: Optional[str] = Field(None, description="Usage context")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v
