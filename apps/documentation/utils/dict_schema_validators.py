"""Dict-based schema validators for documentation data structures.

Ported from Lambda documentation.api. Uses SchemaValidationError (not Django
ValidationError) so these validators can be used alongside core validation.
Use for dict validation in services/views when Lambda-compatible error
shapes are needed.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple


class SchemaValidationError:
    """Represents a single validation error (field, message, optional value)."""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
        }


class PageSchemaValidator:
    """Validator for page documentation schema."""

    REQUIRED_FIELDS = ["_id", "page_id", "page_type", "metadata", "created_at"]
    REQUIRED_METADATA_FIELDS = [
        "route", "file_path", "purpose", "s3_key", "status",
        "authentication", "last_updated",
    ]
    VALID_PAGE_TYPES = ["docs", "marketing", "dashboard"]
    VALID_STATUSES = ["published", "draft", "deleted"]

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[SchemaValidationError]]:
        errors: List[SchemaValidationError] = []
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(SchemaValidationError(field, f"Required field '{field}' is missing"))
        if errors:
            return False, errors

        page_id = data.get("page_id")
        if page_id:
            if not isinstance(page_id, str):
                errors.append(SchemaValidationError("page_id", "page_id must be a string", page_id))
            elif not page_id.replace("_", "").replace("-", "").isalnum():
                errors.append(SchemaValidationError(
                    "page_id", "page_id must be alphanumeric with underscores/hyphens only", page_id
                ))

        page_type = data.get("page_type")
        if page_type and page_type not in self.VALID_PAGE_TYPES:
            errors.append(SchemaValidationError(
                "page_type", f"page_type must be one of {self.VALID_PAGE_TYPES}", page_type
            ))

        metadata = data.get("metadata")
        if metadata:
            if not isinstance(metadata, dict):
                errors.append(SchemaValidationError("metadata", "metadata must be an object", metadata))
            else:
                for field in self.REQUIRED_METADATA_FIELDS:
                    if field not in metadata:
                        errors.append(SchemaValidationError(
                            f"metadata.{field}", f"Required metadata field '{field}' is missing"
                        ))
                route = metadata.get("route")
                if route:
                    if not isinstance(route, str):
                        errors.append(SchemaValidationError("metadata.route", "route must be a string", route))
                    elif not route.startswith("/") and route != "/":
                        errors.append(SchemaValidationError("metadata.route", "route must start with '/'", route))
                status = metadata.get("status")
                if status and status not in self.VALID_STATUSES:
                    errors.append(SchemaValidationError(
                        "metadata.status", f"status must be one of {self.VALID_STATUSES}", status
                    ))
                uses_endpoints = metadata.get("uses_endpoints", [])
                if uses_endpoints:
                    if not isinstance(uses_endpoints, list):
                        errors.append(SchemaValidationError(
                            "metadata.uses_endpoints", "uses_endpoints must be an array", uses_endpoints
                        ))
                    else:
                        valid_usage_types = ["primary", "secondary", "conditional"]
                        valid_contexts = ["data_fetching", "data_mutation", "authentication", "analytics"]
                        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
                        required_endpoint_fields = [
                            "endpoint_path", "method", "api_version",
                            "via_service", "usage_type", "usage_context",
                        ]
                        for idx, endpoint in enumerate(uses_endpoints):
                            if not isinstance(endpoint, dict):
                                errors.append(SchemaValidationError(
                                    f"metadata.uses_endpoints[{idx}]", "Endpoint must be an object", endpoint
                                ))
                            else:
                                for f in required_endpoint_fields:
                                    if f not in endpoint:
                                        errors.append(SchemaValidationError(
                                            f"metadata.uses_endpoints[{idx}].{f}", f"Required field '{f}' is missing"
                                        ))
                                ut = endpoint.get("usage_type")
                                if ut and ut not in valid_usage_types:
                                    errors.append(SchemaValidationError(
                                        f"metadata.uses_endpoints[{idx}].usage_type",
                                        f"usage_type must be one of {valid_usage_types}, got {ut}",
                                    ))
                                uc = endpoint.get("usage_context")
                                if uc and uc not in valid_contexts:
                                    errors.append(SchemaValidationError(
                                        f"metadata.uses_endpoints[{idx}].usage_context",
                                        f"usage_context must be one of {valid_contexts}, got {uc}",
                                    ))
                                method = endpoint.get("method")
                                if method and method.upper() not in valid_methods:
                                    errors.append(SchemaValidationError(
                                        f"metadata.uses_endpoints[{idx}].method",
                                        f"method must be one of {valid_methods}, got {method}",
                                    ))
                ui_components = metadata.get("ui_components", [])
                if ui_components:
                    if not isinstance(ui_components, list):
                        errors.append(SchemaValidationError(
                            "metadata.ui_components", "ui_components must be an array", ui_components
                        ))
                    else:
                        for idx, component in enumerate(ui_components):
                            if not isinstance(component, dict):
                                errors.append(SchemaValidationError(
                                    f"metadata.ui_components[{idx}]", "Component must be an object", component
                                ))
                            else:
                                if "name" not in component:
                                    errors.append(SchemaValidationError(
                                        f"metadata.ui_components[{idx}].name", "Component name is required"
                                    ))
                                if "file_path" not in component:
                                    errors.append(SchemaValidationError(
                                        f"metadata.ui_components[{idx}].file_path", "Component file_path is required"
                                    ))
                for opt_field, opt_type in (
                    ("content_sections", dict),
                    ("fallback_data", list),
                    ("mock_data", list),
                    ("demo_data", list),
                ):
                    val = metadata.get(opt_field)
                    if val is not None and not isinstance(val, opt_type):
                        errors.append(SchemaValidationError(
                            f"metadata.{opt_field}",
                            f"{opt_field} must be {'a dictionary' if opt_type is dict else 'an array'} if present",
                            val,
                        ))
                endpoint_count = metadata.get("endpoint_count", 0)
                if isinstance(uses_endpoints, list) and endpoint_count != len(uses_endpoints):
                    errors.append(SchemaValidationError(
                        "metadata.endpoint_count",
                        f"endpoint_count ({endpoint_count}) should match uses_endpoints length ({len(uses_endpoints)})",
                        endpoint_count,
                    ))
                api_versions = metadata.get("api_versions", [])
                if api_versions:
                    if not isinstance(api_versions, list):
                        errors.append(SchemaValidationError(
                            "metadata.api_versions", "api_versions must be an array", api_versions
                        ))
                    else:
                        for idx, version in enumerate(api_versions):
                            if not isinstance(version, str):
                                errors.append(SchemaValidationError(
                                    f"metadata.api_versions[{idx}]", "api_versions item must be a string", version
                                ))

        created_at = data.get("created_at")
        if created_at:
            if not isinstance(created_at, str):
                errors.append(SchemaValidationError("created_at", "created_at must be an ISO 8601 string", created_at))
            else:
                try:
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(SchemaValidationError(
                        "created_at", "created_at must be a valid ISO 8601 timestamp", created_at
                    ))

        return len(errors) == 0, errors


class EndpointSchemaValidator:
    """Validator for endpoint documentation schema."""

    REQUIRED_FIELDS = [
        "_id", "endpoint_id", "endpoint_path", "method", "api_version",
        "authentication", "description", "created_at", "updated_at",
    ]
    VALID_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "QUERY", "MUTATION"]

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[SchemaValidationError]]:
        errors: List[SchemaValidationError] = []
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(SchemaValidationError(field, f"Required field '{field}' is missing"))
        if errors:
            return False, errors

        endpoint_id = data.get("endpoint_id")
        if endpoint_id and not isinstance(endpoint_id, str):
            errors.append(SchemaValidationError("endpoint_id", "endpoint_id must be a string", endpoint_id))
        endpoint_path = data.get("endpoint_path")
        if endpoint_path and not isinstance(endpoint_path, str):
            errors.append(SchemaValidationError("endpoint_path", "endpoint_path must be a string", endpoint_path))
        method = data.get("method")
        if method and method not in self.VALID_METHODS:
            errors.append(SchemaValidationError("method", f"method must be one of {self.VALID_METHODS}", method))
        api_version = data.get("api_version")
        if api_version and not isinstance(api_version, str):
            errors.append(SchemaValidationError("api_version", "api_version must be a string", api_version))

        service_file = data.get("service_file")
        router_file = data.get("router_file")
        if not service_file and not router_file:
            errors.append(SchemaValidationError(
                "service_file/router_file", "At least one of 'service_file' or 'router_file' must be provided"
            ))

        graphql_operation = data.get("graphql_operation")
        if graphql_operation and not isinstance(graphql_operation, str):
            errors.append(SchemaValidationError(
                "graphql_operation", "graphql_operation must be a string", graphql_operation
            ))
        for list_field, item_desc in (
            ("service_methods", "Service method"),
            ("repository_methods", "Repository method"),
        ):
            items = data.get(list_field, [])
            if items:
                if not isinstance(items, list):
                    errors.append(SchemaValidationError(list_field, f"{list_field} must be an array", items))
                else:
                    for idx, item in enumerate(items):
                        if not isinstance(item, str):
                            errors.append(SchemaValidationError(
                                f"{list_field}[{idx}]", f"{item_desc} must be a string", item
                            ))
        used_by_pages = data.get("used_by_pages", [])
        if used_by_pages:
            if not isinstance(used_by_pages, list):
                errors.append(SchemaValidationError("used_by_pages", "used_by_pages must be an array", used_by_pages))
            else:
                for idx, page in enumerate(used_by_pages):
                    if not isinstance(page, dict):
                        errors.append(SchemaValidationError(
                            f"used_by_pages[{idx}]", "Page reference must be an object", page
                        ))
                    elif "page_path" not in page:
                        errors.append(SchemaValidationError(
                            f"used_by_pages[{idx}].page_path", "page_path is required"
                        ))
        page_count = data.get("page_count", 0)
        if isinstance(used_by_pages, list) and page_count != len(used_by_pages):
            errors.append(SchemaValidationError(
                "page_count", f"page_count ({page_count}) should match used_by_pages length ({len(used_by_pages)})",
                page_count,
            ))

        for field in ["created_at", "updated_at"]:
            if field in data:
                value = data[field]
                if not isinstance(value, str):
                    errors.append(SchemaValidationError(field, f"{field} must be an ISO 8601 string", value))
                else:
                    try:
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        errors.append(SchemaValidationError(
                            field, f"{field} must be a valid ISO 8601 timestamp", value
                        ))

        return len(errors) == 0, errors


class RelationshipSchemaValidator:
    """Validator for relationship documentation schema (by-page and by-endpoint)."""

    VALID_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "QUERY", "MUTATION"]
    VALID_USAGE_TYPES = ["primary", "secondary", "conditional"]
    VALID_USAGE_CONTEXTS = ["data_fetching", "data_mutation", "authentication", "analytics"]

    def _check_timestamps(self, data: Dict[str, Any], errors: List[SchemaValidationError]) -> None:
        for field in ["created_at", "updated_at"]:
            if field in data:
                value = data[field]
                if not isinstance(value, str):
                    errors.append(SchemaValidationError(field, f"{field} must be an ISO 8601 string", value))
                else:
                    try:
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        errors.append(SchemaValidationError(
                            field, f"{field} must be a valid ISO 8601 timestamp", value
                        ))

    def validate_by_page(self, data: Dict[str, Any]) -> Tuple[bool, List[SchemaValidationError]]:
        errors: List[SchemaValidationError] = []
        if "page_path" not in data:
            errors.append(SchemaValidationError("page_path", "Required field 'page_path' is missing"))
        if "endpoints" not in data:
            errors.append(SchemaValidationError("endpoints", "Required field 'endpoints' is missing"))
        if errors:
            return False, errors

        page_path = data.get("page_path")
        if page_path:
            if not isinstance(page_path, str):
                errors.append(SchemaValidationError("page_path", "page_path must be a string", page_path))
            elif not page_path.startswith("/") and page_path != "/":
                errors.append(SchemaValidationError("page_path", "page_path must start with '/'", page_path))

        endpoints = data.get("endpoints", [])
        if endpoints:
            if not isinstance(endpoints, list):
                errors.append(SchemaValidationError("endpoints", "endpoints must be an array", endpoints))
            else:
                required = ["page_path", "endpoint_path", "method", "api_version", "via_service", "usage_type", "usage_context"]
                for idx, endpoint in enumerate(endpoints):
                    if not isinstance(endpoint, dict):
                        errors.append(SchemaValidationError(
                            f"endpoints[{idx}]", "Endpoint must be an object", endpoint
                        ))
                    else:
                        for f in required:
                            if f not in endpoint:
                                errors.append(SchemaValidationError(
                                    f"endpoints[{idx}].{f}", f"Required field '{f}' is missing"
                                ))
                        method = endpoint.get("method")
                        if method and method not in self.VALID_METHODS:
                            errors.append(SchemaValidationError(
                                f"endpoints[{idx}].method", f"method must be one of {self.VALID_METHODS}", method
                            ))
                        ut = endpoint.get("usage_type")
                        if ut and ut not in self.VALID_USAGE_TYPES:
                            errors.append(SchemaValidationError(
                                f"endpoints[{idx}].usage_type",
                                f"usage_type must be one of {self.VALID_USAGE_TYPES}", ut
                            ))
                        uc = endpoint.get("usage_context")
                        if uc and uc not in self.VALID_USAGE_CONTEXTS:
                            errors.append(SchemaValidationError(
                                f"endpoints[{idx}].usage_context",
                                f"usage_context must be one of {self.VALID_USAGE_CONTEXTS}", uc
                            ))

        self._check_timestamps(data, errors)
        return len(errors) == 0, errors

    def validate_by_endpoint(self, data: Dict[str, Any]) -> Tuple[bool, List[SchemaValidationError]]:
        errors: List[SchemaValidationError] = []
        if "endpoint_path" not in data:
            errors.append(SchemaValidationError("endpoint_path", "Required field 'endpoint_path' is missing"))
        if "method" not in data:
            errors.append(SchemaValidationError("method", "Required field 'method' is missing"))
        if "pages" not in data:
            errors.append(SchemaValidationError("pages", "Required field 'pages' is missing"))
        if errors:
            return False, errors

        endpoint_path = data.get("endpoint_path")
        if endpoint_path and not isinstance(endpoint_path, str):
            errors.append(SchemaValidationError("endpoint_path", "endpoint_path must be a string", endpoint_path))
        method = data.get("method")
        if method and method not in self.VALID_METHODS:
            errors.append(SchemaValidationError("method", f"method must be one of {self.VALID_METHODS}", method))

        pages = data.get("pages", [])
        if pages:
            if not isinstance(pages, list):
                errors.append(SchemaValidationError("pages", "pages must be an array", pages))
            else:
                required = ["page_path", "page_title", "via_service", "usage_type", "usage_context"]
                for idx, page in enumerate(pages):
                    if not isinstance(page, dict):
                        errors.append(SchemaValidationError(
                            f"pages[{idx}]", "Page must be an object", page
                        ))
                    else:
                        for f in required:
                            if f not in page:
                                errors.append(SchemaValidationError(
                                    f"pages[{idx}].{f}", f"Required field '{f}' is missing"
                                ))
                        ut = page.get("usage_type")
                        if ut and ut not in self.VALID_USAGE_TYPES:
                            errors.append(SchemaValidationError(
                                f"pages[{idx}].usage_type",
                                f"usage_type must be one of {self.VALID_USAGE_TYPES}, got {ut}", ut
                            ))
                        uc = page.get("usage_context")
                        if uc and uc not in self.VALID_USAGE_CONTEXTS:
                            errors.append(SchemaValidationError(
                                f"pages[{idx}].usage_context",
                                f"usage_context must be one of {self.VALID_USAGE_CONTEXTS}, got {uc}", uc
                            ))
                        updated_at = page.get("updated_at")
                        if updated_at:
                            if not isinstance(updated_at, str):
                                errors.append(SchemaValidationError(
                                    f"pages[{idx}].updated_at", "updated_at must be an ISO 8601 string", updated_at
                                ))
                            else:
                                try:
                                    datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                                except ValueError:
                                    errors.append(SchemaValidationError(
                                        f"pages[{idx}].updated_at",
                                        "updated_at must be a valid ISO 8601 timestamp", updated_at
                                    ))

        self._check_timestamps(data, errors)
        return len(errors) == 0, errors
