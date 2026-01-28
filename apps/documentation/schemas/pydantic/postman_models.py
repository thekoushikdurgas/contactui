"""Postman Collection v2.1.0 and Configuration models (ported from Lambda documentation.api)."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class PostmanEnvironmentValue(BaseModel):
    """A single environment variable."""
    key: str = Field(..., description="Variable name")
    value: str = Field(..., description="Variable value")
    enabled: bool = Field(True, description="Is variable enabled")
    type: str = Field("default", description="Variable type: default or secret")
    description: Optional[str] = Field(None, description="Variable description")


class PostmanEnvironment(BaseModel):
    """Postman environment definition."""
    id: Optional[str] = Field(None, description="Environment ID")
    name: str = Field(..., description="Environment name")
    values: List[PostmanEnvironmentValue] = Field(default_factory=list, description="Environment variables")
    timestamp: Optional[int] = Field(None, description="Last modified timestamp")
    is_active: bool = Field(False, description="Is this the active environment")


class PostmanCollectionInfo(BaseModel):
    """Collection info block."""
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    schema_url: str = Field(
        "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        alias="schema",
        description="Collection schema URL",
    )
    version: Optional[str] = Field(None, description="Collection version")


class PostmanAuthParam(BaseModel):
    """Authentication parameter."""
    key: str = Field(..., description="Parameter key")
    value: Any = Field(..., description="Parameter value")
    type: str = Field("string", description="Parameter type")


class PostmanAuth(BaseModel):
    """Authentication configuration."""
    type: str = Field(..., description="Auth type: noauth, bearer, apikey, basic, oauth2, etc.")
    apikey: Optional[List[PostmanAuthParam]] = Field(None, description="API Key auth params")
    bearer: Optional[List[PostmanAuthParam]] = Field(None, description="Bearer token params")
    basic: Optional[List[PostmanAuthParam]] = Field(None, description="Basic auth params")
    oauth2: Optional[List[PostmanAuthParam]] = Field(None, description="OAuth2 params")


class PostmanQueryParam(BaseModel):
    """URL query parameter."""
    key: str = Field(..., description="Parameter key")
    value: Optional[str] = Field(None, description="Parameter value")
    description: Optional[str] = Field(None, description="Parameter description")
    disabled: bool = Field(False, description="Is parameter disabled")


class PostmanUrlVariable(BaseModel):
    """URL path variable."""
    key: str = Field(..., description="Variable key")
    value: Optional[str] = Field(None, description="Variable value")
    description: Optional[str] = Field(None, description="Variable description")


class PostmanUrl(BaseModel):
    """Request URL definition."""
    raw: str = Field(..., description="Raw URL string")
    protocol: Optional[str] = Field(None, description="URL protocol")
    host: Optional[List[str]] = Field(None, description="Host parts")
    path: Optional[List[str]] = Field(None, description="Path segments")
    query: Optional[List[PostmanQueryParam]] = Field(None, description="Query parameters")
    variable: Optional[List[PostmanUrlVariable]] = Field(None, description="Path variables")


class PostmanFormDataItem(BaseModel):
    """Form data item."""
    key: str = Field(..., description="Field key")
    value: Optional[str] = Field(None, description="Field value")
    type: str = Field("text", description="Field type: text or file")
    src: Optional[str] = Field(None, description="File source path")
    disabled: bool = Field(False, description="Is field disabled")
    description: Optional[str] = Field(None, description="Field description")


class PostmanGraphQL(BaseModel):
    """GraphQL request body."""
    query: str = Field(..., description="GraphQL query")
    variables: Optional[str] = Field(None, description="GraphQL variables as JSON string")


class PostmanBody(BaseModel):
    """Request body definition."""
    mode: str = Field(..., description="Body mode: raw, urlencoded, formdata, file, graphql")
    raw: Optional[str] = Field(None, description="Raw body content")
    urlencoded: Optional[List[PostmanFormDataItem]] = Field(None, description="URL encoded data")
    formdata: Optional[List[PostmanFormDataItem]] = Field(None, description="Form data")
    graphql: Optional[PostmanGraphQL] = Field(None, description="GraphQL body")
    options: Optional[Dict[str, Any]] = Field(None, description="Body options")


class PostmanHeader(BaseModel):
    """Request header."""
    key: str = Field(..., description="Header name")
    value: str = Field(..., description="Header value")
    description: Optional[str] = Field(None, description="Header description")
    disabled: bool = Field(False, description="Is header disabled")


class PostmanRequest(BaseModel):
    """Request definition."""
    method: str = Field(..., description="HTTP method")
    header: Optional[List[PostmanHeader]] = Field(None, description="Request headers")
    body: Optional[PostmanBody] = Field(None, description="Request body")
    url: Union[str, PostmanUrl] = Field(..., description="Request URL")
    auth: Optional[PostmanAuth] = Field(None, description="Request auth")
    description: Optional[str] = Field(None, description="Request description")


class PostmanScript(BaseModel):
    """Script definition for pre-request or test."""
    id: Optional[str] = Field(None, description="Script ID")
    type: str = Field("text/javascript", description="Script type")
    exec: List[str] = Field(default_factory=list, description="Script lines")


class PostmanEvent(BaseModel):
    """Event definition (pre-request or test script)."""
    listen: str = Field(..., description="Event type: prerequest or test")
    script: PostmanScript = Field(..., description="Event script")


class PostmanResponse(BaseModel):
    """Saved response example."""
    id: Optional[str] = Field(None, description="Response ID")
    name: str = Field(..., description="Response name")
    originalRequest: Optional[PostmanRequest] = Field(None, description="Original request")
    status: Optional[str] = Field(None, description="Response status text")
    code: Optional[int] = Field(None, description="Response status code")
    header: Optional[List[PostmanHeader]] = Field(None, description="Response headers")
    body: Optional[str] = Field(None, description="Response body")


class PostmanItem(BaseModel):
    """Collection item (request or folder)."""
    id: Optional[str] = Field(None, description="Item ID")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    request: Optional[PostmanRequest] = Field(None, description="Request (if this is a request)")
    response: Optional[List[PostmanResponse]] = Field(None, description="Saved responses")
    event: Optional[List[PostmanEvent]] = Field(None, description="Item events")
    item: Optional[List["PostmanItem"]] = Field(None, description="Nested items (if this is a folder)")


PostmanItem.model_rebuild()


class PostmanCollection(BaseModel):
    """Complete Postman Collection v2.1.0."""
    info: PostmanCollectionInfo = Field(..., description="Collection info")
    item: List[PostmanItem] = Field(default_factory=list, description="Collection items")
    auth: Optional[PostmanAuth] = Field(None, description="Collection-level auth")
    event: Optional[List[PostmanEvent]] = Field(None, description="Collection-level events")
    variable: Optional[List[PostmanEnvironmentValue]] = Field(None, description="Collection variables")


class PostmanRoleAccess(BaseModel):
    """Access control for a role on Postman configuration."""
    model_config = ConfigDict(populate_by_name=True)
    can_view: bool = Field(True, description="Can view the configuration")
    can_run: bool = Field(False, alias="can_run_tests", description="Can run test suites")
    can_edit: bool = Field(False, description="Can edit the configuration")
    can_delete: bool = Field(False, description="Can delete the configuration")
    can_export: bool = Field(False, description="Can export/download the configuration")


class PostmanAccessControl(BaseModel):
    """Access control for all user types on Postman configuration."""
    super_admin: PostmanRoleAccess = Field(
        default_factory=lambda: PostmanRoleAccess(can_view=True, can_run=True, can_edit=True, can_delete=True, can_export=True)
    )
    admin: PostmanRoleAccess = Field(
        default_factory=lambda: PostmanRoleAccess(can_view=True, can_run=True, can_edit=True, can_delete=False, can_export=True)
    )
    pro_user: PostmanRoleAccess = Field(
        default_factory=lambda: PostmanRoleAccess(can_view=True, can_run=True, can_edit=False, can_delete=False, can_export=False)
    )
    free_user: PostmanRoleAccess = Field(
        default_factory=lambda: PostmanRoleAccess(can_view=True, can_run=False, can_edit=False, can_delete=False, can_export=False)
    )
    guest: PostmanRoleAccess = Field(
        default_factory=lambda: PostmanRoleAccess(can_view=False, can_run=False, can_edit=False, can_delete=False, can_export=False)
    )


class PostmanConfigurationMetadata(BaseModel):
    """Metadata for Postman configuration."""
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator")
    last_updated_by: Optional[str] = Field(None, description="Last updater")
    last_synced_at: Optional[str] = Field(None, description="Last sync timestamp")
    sync_source: Optional[str] = Field(None, description="Sync source (manual/ci/import/etc)")
    version: str = Field("1.0.0", description="Configuration version")
    tags: List[str] = Field(default_factory=list, description="Tags")
    notes: Optional[str] = Field(None, description="Notes")


class EndpointMapping(BaseModel):
    """Maps a Postman request to a documentation endpoint."""
    mapping_id: str = Field(..., description="Unique mapping ID")
    endpoint_id: str = Field(..., description="Documentation endpoint ID")
    postman_request_id: str = Field(..., description="Postman request ID")
    postman_folder_path: List[str] = Field(default_factory=list, description="Folder path in collection")
    sync_status: str = Field("synced", description="Sync status: synced, pending, error")
    last_synced_at: Optional[str] = Field(None, description="Last sync timestamp")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")
    test_config: Optional[Dict[str, Any]] = Field(None, description="Test configuration")


class TestSuite(BaseModel):
    """Test suite definition."""
    suite_id: str = Field(..., description="Unique suite ID")
    name: str = Field(..., description="Suite name")
    description: Optional[str] = Field(None, description="Suite description")
    endpoint_mapping_ids: List[str] = Field(default_factory=list, description="Endpoint mappings to test")
    environment_name: Optional[str] = Field(None, description="Environment to use")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Execution schedule")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class PostmanConfiguration(BaseModel):
    """Root model for Postman configuration with collection, environments, and mappings."""
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="_id", description="Unique configuration ID")
    config_id: str = Field(..., description="Configuration identifier")
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    state: str = Field("development", description="Configuration state: coming_soon, published, draft, development, test")
    collection: PostmanCollection = Field(..., description="Postman collection")
    environments: List[PostmanEnvironment] = Field(default_factory=list, description="Available environments")
    endpoint_mappings: List[EndpointMapping] = Field(default_factory=list, description="Endpoint mappings")
    test_suites: List[TestSuite] = Field(default_factory=list, description="Test suites")
    access_control: Optional[PostmanAccessControl] = Field(None, description="Access control settings")
    metadata: PostmanConfigurationMetadata = Field(..., description="Configuration metadata")

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v
