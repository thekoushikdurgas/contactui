"""
Pydantic schemas ported from Lambda documentation.api for identical JSON shapes.

Use for request/response validation and API contract parity with Lambda.
"""

from apps.documentation.schemas.pydantic.models import (
    AccessControl,
    PageDocumentation,
    PageMetadata,
    EndpointDocumentation,
    EnhancedRelationship,
)
from apps.documentation.schemas.pydantic.responses import (
    DocumentationPageResponse,
    DocumentationPageListResponse,
    EndpointDocumentationResponse,
    EndpointDocumentationListResponse,
    RelationshipListResponse,
    RelationshipGraphResponse,
)
from apps.documentation.schemas.pydantic.requests import (
    DocumentationPageCreateRequest,
    DocumentationPageUpdateRequest,
    EndpointDocumentationCreateRequest,
)

__all__ = [
    "AccessControl",
    "PageDocumentation",
    "PageMetadata",
    "EndpointDocumentation",
    "EnhancedRelationship",
    "DocumentationPageResponse",
    "DocumentationPageListResponse",
    "EndpointDocumentationResponse",
    "EndpointDocumentationListResponse",
    "RelationshipListResponse",
    "RelationshipGraphResponse",
    "DocumentationPageCreateRequest",
    "DocumentationPageUpdateRequest",
    "EndpointDocumentationCreateRequest",
]
