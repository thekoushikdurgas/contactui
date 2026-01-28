# Real-World Usage Examples

## Example 1: Companies Page with Endpoints

### Page Document
```json
{
  "_id": "9d775e1f-f818-44da-8cc6-50373279b19c",
  "page_id": "companies_page",
  "page_type": "dashboard",
  "metadata": {
    "route": "/companies",
    "file_path": "frontent/app/(dashboard)/companies/page.tsx",
    "purpose": "Company listing and management page",
    "s3_key": "documentation/companies_page.md",
    "status": "published",
    "authentication": "Required (protected by AuthGuard)",
    "authorization": null,
    "uses_endpoints": [
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
    "ui_components": [
      {"name": "CompanyTable", "file_path": "components/CompanyTable.tsx"}
    ],
    "endpoint_count": 1,
    "api_versions": ["v4"]
  },
  "created_at": "2026-01-19T06:31:10.724128+00:00"
}
```

### Related Endpoint Document
```json
{
  "_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "endpoint_id": "get_companies_v4",
  "endpoint_path": "/api/v4/companies",
  "method": "GET",
  "api_version": "v4",
  "router_file": "app/api/v4/routers/companies.py",
  "service_methods": ["list_companies"],
  "repository_methods": ["get_all_companies"],
  "authentication": "Bearer token (JWT)",
  "authorization": "User role required",
  "description": "List all companies with filtering and pagination",
  "used_by_pages": [
    {
      "page_path": "/companies",
      "via_service": "companyService",
      "via_hook": "useCompanies",
      "usage_type": "primary",
      "usage_context": "data_fetching"
    }
  ],
  "page_count": 1,
  "created_at": "2026-01-19T06:31:10.724128+00:00",
  "updated_at": "2026-01-19T08:15:30.123456+00:00"
}
```

### Relationship Files

#### By-Page Relationship
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
  "created_at": "2026-01-19T06:31:10.724128+00:00",
  "updated_at": "2026-01-19T08:15:30.123456+00:00"
}
```

#### By-Endpoint Relationship
```json
{
  "endpoint_path": "/api/v4/companies",
  "method": "GET",
  "pages": [
    {
      "page_path": "/companies",
      "via_service": "companyService",
      "via_hook": "useCompanies",
      "usage_type": "primary",
      "usage_context": "data_fetching"
    }
  ],
  "created_at": "2026-01-19T06:31:10.724128+00:00",
  "updated_at": "2026-01-19T08:15:30.123456+00:00"
}
```

## Example 2: Marketing Page (No Endpoints)

### Page Document
```json
{
  "_id": "dce7d505-af83-4ea2-88f1-cc20a585c4a9",
  "page_id": "about_page",
  "page_type": "marketing",
  "metadata": {
    "route": "/about",
    "file_path": "frontent/app/(marketing)/about/page.tsx",
    "purpose": "Marketing page that tells the story of Contact360",
    "s3_key": "documentation/about_page.md",
    "status": "published",
    "authentication": "Not required (public marketing page)",
    "authorization": null,
    "last_updated": "2026-01-19T06:47:22.596018+00:00",
    "uses_endpoints": [],
    "ui_components": [],
    "endpoint_count": 0,
    "api_versions": []
  },
  "created_at": "2026-01-19T06:47:22.596018+00:00"
}
```

**Note**: Marketing pages typically don't use API endpoints, so `uses_endpoints` is empty.

## Example 3: Admin Page with Authorization

### Page Document
```json
{
  "_id": "aaecd8de-861c-4ad1-b953-2bf840d55ba9",
  "page_id": "admin_users_page",
  "page_type": "dashboard",
  "metadata": {
    "route": "/admin/users",
    "file_path": "frontent/app/(dashboard)/admin/users/page.tsx",
    "purpose": "User management interface for Super Admins",
    "s3_key": "documentation/admin_users_page.md",
    "status": "published",
    "authentication": "Required (protected by AuthGuard)",
    "authorization": "Super Admin only (protected by RoleGuard)",
    "last_updated": "2026-01-19T06:47:22.620841+00:00",
    "uses_endpoints": [],
    "ui_components": [],
    "endpoint_count": 0,
    "api_versions": []
  },
  "created_at": "2026-01-19T06:47:22.620841+00:00"
}
```

**Note**: Admin pages have `authorization` field set to role requirements.

## Example 4: Multi-Endpoint Page

### Page with Multiple Endpoints
```json
{
  "page_id": "dashboard_page",
  "page_type": "dashboard",
  "metadata": {
    "route": "/dashboard",
    "uses_endpoints": [
      {
        "endpoint_path": "/api/v4/companies",
        "method": "GET",
        "api_version": "v4",
        "via_service": "companyService",
        "via_hook": "useCompanyStats",
        "usage_type": "secondary",
        "usage_context": "analytics"
      },
      {
        "endpoint_path": "/api/v4/contacts",
        "method": "GET",
        "api_version": "v4",
        "via_service": "contactService",
        "via_hook": "useContactStats",
        "usage_type": "secondary",
        "usage_context": "analytics"
      },
      {
        "endpoint_path": "/api/v4/activities",
        "method": "GET",
        "api_version": "v4",
        "via_service": "activityService",
        "via_hook": "useRecentActivities",
        "usage_type": "primary",
        "usage_context": "data_fetching"
      }
    ],
    "endpoint_count": 3,
    "api_versions": ["v4"]
  }
}
```

## Example 5: Endpoint Used by Multiple Pages

### Endpoint Document
```json
{
  "endpoint_id": "get_companies_v4",
  "endpoint_path": "/api/v4/companies",
  "method": "GET",
  "used_by_pages": [
    {
      "page_path": "/companies",
      "via_service": "companyService",
      "via_hook": "useCompanies",
      "usage_type": "primary",
      "usage_context": "data_fetching"
    },
    {
      "page_path": "/dashboard",
      "via_service": "companyService",
      "via_hook": "useCompanyStats",
      "usage_type": "secondary",
      "usage_context": "analytics"
    },
    {
      "page_path": "/analytics",
      "via_service": "analyticsService",
      "via_hook": "useCompanyAnalytics",
      "usage_type": "secondary",
      "usage_context": "reporting"
    }
  ],
  "page_count": 3
}
```

## Example 6: CRUD Endpoint Set

### Complete CRUD Operations
```json
[
  {
    "endpoint_id": "get_companies_v4",
    "endpoint_path": "/api/v4/companies",
    "method": "GET",
    "description": "List companies"
  },
  {
    "endpoint_id": "post_companies_v4",
    "endpoint_path": "/api/v4/companies",
    "method": "POST",
    "description": "Create company"
  },
  {
    "endpoint_id": "put_companies_v4",
    "endpoint_path": "/api/v4/companies/{id}",
    "method": "PUT",
    "description": "Update company"
  },
  {
    "endpoint_id": "delete_companies_v4",
    "endpoint_path": "/api/v4/companies/{id}",
    "method": "DELETE",
    "description": "Delete company"
  }
]
```

## Example 7: Index File Structure

### Pages Index
```json
{
  "version": "1.0",
  "last_updated": "2026-01-19T06:31:11.119879+00:00",
  "total": 52,
  "pages": [
    {"page_id": "companies_page", "page_type": "dashboard", "route": "/companies"},
    {"page_id": "contacts_page", "page_type": "dashboard", "route": "/contacts"}
  ],
  "indexes": {
    "by_type": {
      "docs": ["home_page", "login_page"],
      "marketing": ["about_page", "careers_page"],
      "dashboard": ["companies_page", "contacts_page"]
    },
    "by_route": {
      "/companies": "companies_page",
      "/contacts": "contacts_page"
    }
  }
}
```

## Example 8: API Usage Flow

### Complete Flow Example

1. **User visits** `/companies` page
2. **Page loads** and calls `useCompanies()` hook
3. **Hook uses** `companyService.getCompanies()`
4. **Service calls** `GET /api/v4/companies` endpoint
5. **Endpoint documented** in Endpoints collection
6. **Relationship tracked** in Relationships collection

### Query Flow
```
GET /docs/companies_page
  → Returns page metadata
  → Includes uses_endpoints array
  → Shows endpoint relationships

GET /endpoint-docs/get_companies_v4
  → Returns endpoint metadata
  → Includes used_by_pages array
  → Shows page relationships

GET /docs/relationships/page/companies
  → Returns all endpoints for /companies page
  → Shows usage context and types
```

## Example 9: Sync Operation

### Syncing Relationships
```json
{
  "relationships": {
    "page_to_endpoints": {
      "/companies": [
        {
          "endpoint_path": "/api/v4/companies",
          "method": "GET",
          "api_version": "v4",
          "via_service": "companyService",
          "via_hook": "useCompanies",
          "usage_type": "primary",
          "usage_context": "data_fetching"
        }
      ]
    },
    "endpoint_to_pages": {
      "GET:/api/v4/companies": [
        {
          "page_path": "/companies",
          "via_service": "companyService",
          "via_hook": "useCompanies",
          "usage_type": "primary",
          "usage_context": "data_fetching"
        }
      ]
    }
  }
}
```

## Example 10: Validation Results

### Relationship Validation
```json
{
  "total_relationships": 150,
  "issues": [
    {
      "type": "missing_page",
      "page_path": "/old-page",
      "endpoint_path": "/api/v4/companies",
      "method": "GET"
    },
    {
      "type": "missing_endpoint",
      "page_path": "/companies",
      "endpoint_path": "/api/v4/old-endpoint",
      "method": "GET"
    }
  ],
  "issue_count": 2,
  "valid": false
}
```
