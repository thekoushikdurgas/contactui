# API Gateway

Centralized API configuration and routing for the DocsAI application.

## Purpose

The `apps.api` package provides:
- Centralized API routing
- Common permission classes
- Standardized throttling
- Unified pagination
- Custom exception handling
- Consistent API responses

## Structure

```
apps/api/
├── __init__.py
├── apps.py              # App configuration
├── urls.py              # Central API routing
├── permissions.py       # Common permission classes
├── throttles.py        # Rate limiting classes
├── pagination.py        # Pagination classes
└── exception_handlers.py  # Custom DRF exception handling
```

## Usage

### URL Routing

The API gateway centralizes all API routes:

```python
# docsai/urls.py
urlpatterns = [
    # Option 1: Use API gateway (recommended)
    path('api/', include('apps.api.urls')),
    
    # Option 2: Direct app routing (still supported)
    path('api/v1/', include('apps.documentation.api.v1.urls')),
]
```

### Permissions

Use common permission classes:

```python
from apps.api.permissions import IsAPIAuthenticated, IsAPIAdmin

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAPIAuthenticated]
```

### Throttling

Apply rate limiting:

```python
from apps.api.throttles import BurstRateThrottle, SustainedRateThrottle

class MyViewSet(viewsets.ModelViewSet):
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
```

### Pagination

Use standardized pagination:

```python
from apps.api.pagination import StandardResultsSetPagination

class MyViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
```

### Exception Handling

Custom exceptions are automatically handled:

```python
from apps.core.exceptions import NotFoundError, ValidationError

# In your view/service
if not resource:
    raise NotFoundError("Resource not found", field="id")

# Automatically returns:
# {
#   "success": false,
#   "error": "Resource not found",
#   "error_code": "not_found",
#   "field": "id"
# }
```

## Exception Types

### ValidationError (400)
```python
raise ValidationError("Invalid input", field="email")
```

### NotFoundError (404)
```python
raise NotFoundError("Resource not found")
```

### PermissionDeniedError (403)
```python
raise PermissionDeniedError("Access denied")
```

### AuthenticationError (401)
```python
raise AuthenticationError("Authentication required")
```

### ConflictError (409)
```python
raise ConflictError("Resource already exists")
```

### ServiceUnavailableError (503)
```python
raise ServiceUnavailableError("Service temporarily unavailable")
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "error_code",
  "field": "field_name"  // Optional, for validation errors
}
```

## Configuration

The API gateway is configured in `config/settings/base.py`:

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.api.exception_handlers.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    # ... other settings
}
```

## API Versioning

The gateway supports multiple API versions:

- `/api/v1/` - Version 1 (documentation API)
- `/api/v2/` - Version 2 (alternative version)
- `/api/ai/` - AI agent API
- `/api/knowledge/` - Knowledge API
- `/api/tasks/` - Tasks API
- `/api/durgasflow/` - Workflow API

## Best Practices

1. **Use API gateway routing** - Centralize all API routes
2. **Consistent permissions** - Use common permission classes
3. **Standardized responses** - Follow the response format
4. **Custom exceptions** - Use DRF-compatible exceptions
5. **Rate limiting** - Apply throttling to prevent abuse
6. **Pagination** - Always paginate list endpoints

## Migration

To migrate existing APIs to use the gateway:

1. Update `docsai/urls.py` to include API gateway
2. Move app-specific API routes to gateway
3. Update permission classes to use common classes
4. Replace custom exception handling with gateway handlers
5. Test all endpoints

## Examples

### ViewSet with Gateway Features

```python
from rest_framework import viewsets
from apps.api.permissions import IsAPIAuthenticated
from apps.api.throttles import BurstRateThrottle
from apps.api.pagination import StandardResultsSetPagination
from apps.core.exceptions import NotFoundError

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAPIAuthenticated]
    throttle_classes = [BurstRateThrottle]
    pagination_class = StandardResultsSetPagination
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_active:
            raise NotFoundError("Resource not found")
        return super().retrieve(request, *args, **kwargs)
```

### Custom Exception in Service

```python
from apps.core.exceptions import ValidationError, ServiceError

class MyService:
    def create_resource(self, data):
        if not data.get('name'):
            raise ValidationError("Name is required", field="name")
        
        try:
            # ... create logic
            return resource
        except Exception as e:
            raise ServiceError(
                f"Failed to create resource: {e}",
                service_name="MyService",
                operation="create_resource"
            )
```
