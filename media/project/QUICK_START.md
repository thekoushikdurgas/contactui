# Quick Start Guide

## Overview

This guide provides quick reference for working with the Documentation Collections.

## Collections at a Glance

| Collection | Purpose | Storage | Index |
|------------|---------|---------|-------|
| **Pages** | Frontend page metadata | `data/pages/{id}.json` | By type, by route |
| **Endpoints** | API endpoint documentation | `data/endpoints/{id}.json` | By version, by method, by path+method |
| **Relationships** | Page-endpoint connections | `data/relationships/by-{page\|endpoint}/` | By API version (stats) |

## Common Operations

### Pages

#### List All Pages
```bash
GET /docs
```

#### Get Page by ID
```bash
GET /docs/companies_page
```

#### Get Page by Route
```bash
# Uses index lookup
GET /docs?route=/companies
```

#### Filter by Type
```bash
GET /docs?page_type=dashboard
```

### Endpoints

#### List All Endpoints
```bash
GET /endpoint-docs
```

#### Get Endpoint by ID
```bash
GET /endpoint-docs/get_companies_v4
```

#### Get by Path and Method
```bash
# Uses index lookup
GET /endpoint-docs?path=/api/v4/companies&method=GET
```

#### Filter by API Version
```bash
GET /endpoint-docs?api_version=v4
```

### Relationships

#### Get Endpoints for a Page
```bash
GET /docs/relationships/page/companies
```

#### Get Pages for an Endpoint
```bash
GET /docs/relationships/endpoint/api/v4/companies?method=GET
```

#### Get Relationship Graph
```bash
GET /docs/relationships/graph
```

#### Get Statistics
```bash
GET /docs/relationships/statistics
```

## JSON Structure Quick Reference

### Page Structure
```json
{
  "_id": "uuid",
  "page_id": "companies_page",
  "page_type": "dashboard",
  "metadata": {
    "route": "/companies",
    "file_path": "frontent/app/(dashboard)/companies/page.tsx",
    "purpose": "Description",
    "s3_key": "documentation/companies_page.md",
    "status": "published",
    "authentication": "Required",
    "authorization": null,
    "uses_endpoints": [],
    "ui_components": []
  },
  "created_at": "ISO timestamp"
}
```

### Endpoint Structure
```json
{
  "_id": "uuid",
  "endpoint_id": "get_companies_v4",
  "endpoint_path": "/api/v4/companies",
  "method": "GET",
  "api_version": "v4",
  "router_file": "app/api/v4/routers/companies.py",
  "service_methods": ["list_companies"],
  "repository_methods": ["get_all_companies"],
  "authentication": "Bearer token (JWT)",
  "authorization": "User role required",
  "rate_limit": "100 requests/minute",
  "description": "Description",
  "used_by_pages": [],
  "page_count": 0,
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

### Relationship Structure (By-Page)
```json
{
  "page_path": "/companies",
  "endpoints": [
    {
      "endpoint_path": "/api/v4/companies",
      "method": "GET",
      "api_version": "v4",
      "via_service": "companyService",
      "via_hook": "useCompanies",
      "usage_type": "primary",
      "usage_context": "data_fetching"
    }
  ],
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

## Field Quick Reference

### Page Fields
- `page_id`: Unique identifier (snake_case)
- `page_type`: "docs", "marketing", or "dashboard"
- `metadata.route`: Frontend route path
- `metadata.status`: "published", "draft", or "deleted"

### Endpoint Fields
- `endpoint_id`: Format `{method}_{path}_{version}`
- `endpoint_path`: API path (e.g., "/api/v4/companies")
- `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
- `api_version`: API version (e.g., "v4")

### Relationship Fields
- `page_path`: Frontend route
- `endpoint_path`: API path
- `method`: HTTP method
- `usage_type`: "primary" or "secondary"
- `usage_context`: "data_fetching", "data_mutation", etc.

## Common Patterns

### Finding All Pages Using an Endpoint
1. Get endpoint: `GET /endpoint-docs/{endpoint_id}`
2. Check `used_by_pages` array
3. Or use: `GET /docs/relationships/endpoint/{path}?method={method}`

### Finding All Endpoints Used by a Page
1. Get page: `GET /docs/{page_id}`
2. Check `metadata.uses_endpoints` array
3. Or use: `GET /docs/relationships/page/{page_path}`

### Creating a Complete Relationship
1. Create/update page with endpoint references
2. Create/update endpoint with page references
3. Sync relationships: `POST /docs/relationships/sync`

## Troubleshooting

### Page Not Found
- Check `page_id` spelling (snake_case)
- Verify page exists in index
- Check status (deleted pages may be filtered)

### Endpoint Not Found
- Check `endpoint_id` format: `{method}_{path}_{version}`
- Verify endpoint exists in index
- Check API version

### Relationship Missing
- Verify both page and endpoint exist
- Check relationship files exist
- Run validation: `GET /docs/relationships/validate`

## Next Steps

- Read collection-specific README files for detailed documentation
- Review schema files for complete field reference
- Examine example JSON files for structure
- Check ARCHITECTURE.md for system design
