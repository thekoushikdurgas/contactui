# DocsAI API Reference

This document describes all **exposed HTTP JSON APIs** in the contact360/docsai project. The only REST API mounted at project root is **`/api/v1/`**. Additional JSON endpoints used by the Documentation UI live under **`/docs/`**.

**Architecture:** DocsAI exposes **99 GET endpoints** at `/api/v1/` (Lambda documentation.api parity), backed by **UnifiedStorage** (Local → S3 → GraphQL). Response shapes match the Lambda API for compatibility. Seventeen endpoints were removed (format, statistics, graph, index, health/external-api); use `/docs/api/statistics/*` and `/docs/api/dashboard/graph/` instead.

**Interactive API docs:** **[`/api/docs/`](/api/docs/)** – Django-built API reference (all GET endpoints with per-endpoint call counts and last-called times). **[`/api/swagger/`](/api/swagger/)** – Swagger UI. **[`/api/redoc/`](/api/redoc/)** – ReDoc. OpenAPI schema: **[`/api/schema/`](/api/schema/)**. For the full list of GET paths and query params, see the tables below or the Postman collection in `docs/postman/`.

---

## Table of contents

1. [REST API v1 (`/api/v1/`)](#1-rest-api-v1-apiv1)
2. [Documentation internal APIs (`/docs/api/`)](#2-documentation-internal-apis-docsapi)
3. [Response format](#3-response-format)
4. [Authentication](#4-authentication)

---

## 1. REST API v1 (`/api/v1/`)

Base path: **`/api/v1/`**  
Module: `apps.documentation.api.v1`  
All endpoints are **GET** unless noted. No auth required in current implementation.

### 1.1 Service info and health (5 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/` | Service info (name, version, status) |
| GET | `/api/v1/health/` | Full health: application, database, cache, storage |
| GET | `/api/v1/health/database/` | Database health only |
| GET | `/api/v1/health/cache/` | Cache health only |
| GET | `/api/v1/health/storage/` | Storage health only |

### 1.2 Docs / meta (1 endpoint)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/docs/endpoint-stats/` | Per-endpoint request counts and last_called_at (JSON). Used by `/api/docs/` UI. |

**Response (success):**

```json
{
  "success": true,
  "data": { ... }
}
```

**Service info (`GET /api/v1/`):**

```json
{
  "success": true,
  "data": {
    "service": "Documentation API Service",
    "version": "1.0.0",
    "status": "running"
  }
}
```

---

### 1.3 Pages (17 GETs)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/pages/` | List pages |
| GET | `/api/v1/pages/by-type/docs/` | List docs pages |
| GET | `/api/v1/pages/by-type/marketing/` | List marketing pages |
| GET | `/api/v1/pages/by-type/dashboard/` | List dashboard pages |
| GET | `/api/v1/pages/by-type/<page_type>/count/` | Count by type |
| GET | `/api/v1/pages/by-type/<page_type>/published/` | Published by type |
| GET | `/api/v1/pages/by-type/<page_type>/draft/` | Draft by type |
| GET | `/api/v1/pages/by-type/<page_type>/stats/` | Stats by type |
| GET | `/api/v1/pages/by-state/<state>/` | List by state |
| GET | `/api/v1/pages/by-state/<state>/count/` | Count by state |
| GET | `/api/v1/pages/<user_type>/` | List by user type (or page ID if not user_type) |
| GET | `/api/v1/pages/<page_id>/` | Single page (when segment is not user_type) |
| GET | `/api/v1/pages/<page_id>/access-control/` | Page access control |
| GET | `/api/v1/pages/<page_id>/sections/` | Page sections |
| GET | `/api/v1/pages/<page_id>/components/` | Page components |
| GET | `/api/v1/pages/<page_id>/endpoints/` | Endpoints used by page |
| GET | `/api/v1/pages/<page_id>/versions/` | Page versions |

Query params (e.g. `page_type`, `status`, `include_drafts`, `include_deleted`) as per Lambda API.

---

### 1.4 Endpoints (25 GETs)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/endpoints/` | List endpoints |
| GET | `/api/v1/endpoints/by-api-version/v1/` | v1 endpoints |
| GET | `/api/v1/endpoints/by-api-version/v4/` | v4 endpoints |
| GET | `/api/v1/endpoints/by-api-version/graphql/` | GraphQL endpoints |
| GET | `/api/v1/endpoints/by-api-version/<api_version>/count/` | Count by version |
| GET | `/api/v1/endpoints/by-api-version/<api_version>/stats/` | Stats by version |
| GET | `/api/v1/endpoints/by-api-version/<api_version>/by-method/<method>/` | By version and method |
| GET | `/api/v1/endpoints/by-method/GET/`, `POST/`, `QUERY/`, `MUTATION/` | By method |
| GET | `/api/v1/endpoints/by-method/<method>/count/`, `.../stats/` | Count/stats by method |
| GET | `/api/v1/endpoints/by-state/<state>/`, `.../count/` | By state |
| GET | `/api/v1/endpoints/by-lambda/<service_name>/`, `.../count/` | By Lambda service |
| GET | `/api/v1/endpoints/<endpoint_id>/` | Single endpoint |
| GET | `/api/v1/endpoints/<endpoint_id>/pages/`, `access-control/`, `lambda-services/`, `files/`, `methods/`, `used-by-pages/`, `dependencies/` | Sub-resources |

---

### 1.5 Relationships (35 GETs)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/relationships/` | List relationships |
| GET | `/api/v1/relationships/usage-types/`, `usage-contexts/` | Usage types/contexts |
| GET | `/api/v1/relationships/by-page/<page_id>/`, `.../count/`, `.../primary/`, `.../secondary/`, `.../by-usage-type/<usage_type>/` | By page |
| GET | `/api/v1/relationships/by-endpoint/<endpoint_id>/`, `.../count/`, `.../pages/`, `.../by-usage-context/<usage_context>/` | By endpoint |
| GET | `/api/v1/relationships/by-usage-type/primary/`, `secondary/`, `conditional/`, `<usage_type>/count/`, `.../by-usage-context/<usage_context>/` | By usage type |
| GET | `/api/v1/relationships/by-usage-context/data_fetching/`, `data_mutation/`, `authentication/`, `analytics/`, `<usage_context>/count/` | By usage context |
| GET | `/api/v1/relationships/by-state/<state>/`, `.../count/` | By state |
| GET | `/api/v1/relationships/by-lambda/<service_name>/`, `by-invocation-pattern/<pattern>/`, `by-postman-config/<config_id>/` | By Lambda/pattern/config |
| GET | `/api/v1/relationships/performance/slow/`, `performance/errors/` | Performance filters |
| GET | `/api/v1/relationships/<relationship_id>/` | Single relationship |
| GET | `/api/v1/relationships/<relationship_id>/access-control/`, `data-flow/`, `performance/`, `dependencies/`, `postman/` | Sub-resources |

---

### 1.6 Postman (12 GETs)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/postman/` | List configurations |
| GET | `/api/v1/postman/by-state/<state>/`, `.../count/` | By state |
| GET | `/api/v1/postman/<config_id>/` | Single configuration |
| GET | `/api/v1/postman/<config_id>/collection/` | Collection |
| GET | `/api/v1/postman/<config_id>/environments/`, `.../environments/<env_name>/` | Environments |
| GET | `/api/v1/postman/<config_id>/mappings/`, `.../mappings/<mapping_id>/` | Mappings |
| GET | `/api/v1/postman/<config_id>/test-suites/`, `.../test-suites/<suite_id>/` | Test suites |
| GET | `/api/v1/postman/<config_id>/access-control/` | Access control |

---

### 1.7 Index (Removed)

**Note**: Index endpoints have been removed. Use UI routes at `/docs/index/*` instead, which call services directly.

---

### 1.8 Dashboard (4 endpoints)

Used by the Documentation dashboard UI for pagination and filtering.

| Method | Path | Description | Query params |
|--------|------|-------------|--------------|
| GET | `/api/v1/dashboard/pages/` | Dashboard pages tab | `page`, `page_size`, `page_type`, `status`, `search` |
| GET | `/api/v1/dashboard/endpoints/` | Dashboard endpoints tab | `page`, `page_size`, `api_version`, `method`, `search` |
| GET | `/api/v1/dashboard/relationships/` | Dashboard relationships tab | `page`, `page_size`, `page_id`, `endpoint_id`, `usage_type`, `search` |
| GET | `/api/v1/dashboard/postman/` | Dashboard Postman tab | `page`, `page_size`, `state`, `search` |

---

## 2. Documentation internal APIs (`/docs/api/`)

These endpoints are used by the Documentation dashboard and media UI. Many require **login** (`@login_required`). Base path: **`/docs/`**.

### 2.1 Dashboard APIs

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/docs/api/dashboard/pages/` | Paginated pages for dashboard | login |
| GET | `/docs/api/dashboard/endpoints/` | Paginated endpoints for dashboard | login |
| GET | `/docs/api/dashboard/relationships/` | Paginated relationships for dashboard | login |
| GET | `/docs/api/dashboard/postman/` | Paginated Postman for dashboard | login |
| GET | `/docs/api/dashboard/graph/` | Graph data for dashboard | login |
| POST | `/docs/api/dashboard/bulk-delete/` | Bulk delete entities | login |

**Query params (typical):** `page`, `page_size`, and tab-specific filters (`page_type`, `status`, `search`, etc.).

---

### 2.2 Statistics APIs (`/docs/api/statistics/`)

Internal APIs used by the Documentation dashboard for statistics (replacing removed `/api/v1/*` format/statistics/types/graph endpoints). **Login** required.

| Method | Path | Description | Replaces |
|--------|------|-------------|----------|
| GET | `/docs/api/statistics/pages/statistics/` | Pages index statistics | `/api/v1/pages/statistics/` |
| GET | `/docs/api/statistics/pages/types/` | Page types with counts | `/api/v1/pages/types/` |
| GET | `/docs/api/statistics/endpoints/api-versions/` | API versions with counts | `/api/v1/endpoints/api-versions/` |
| GET | `/docs/api/statistics/endpoints/methods/` | Methods with counts | `/api/v1/endpoints/methods/` |
| GET | `/docs/api/statistics/relationships/statistics/` | Relationships statistics | `/api/v1/relationships/statistics/` |
| GET | `/docs/api/statistics/postman/statistics/` | Postman statistics | `/api/v1/postman/statistics/` |

Graph is served by `/docs/api/dashboard/graph/` (replaces `/api/v1/relationships/graph/`).

---

### 2.3 Draft / form APIs

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/docs/api/endpoints/draft/` | Save endpoint draft (e.g. auto-save) | — |
| POST | `/docs/api/pages/draft/` | Save page draft (e.g. auto-save) | — |

---

### 2.4 Media APIs

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/docs/api/media/files/` | List media files | — |
| POST | `/docs/api/media/files/create/` | Create media file | — |
| GET | `/docs/api/media/sync-status/` | Media sync status | — |
| POST | `/docs/api/media/bulk-sync/` | Bulk sync media | — |
| POST | `/docs/api/media/indexes/regenerate/pages/` | Regenerate pages index | — |
| POST | `/docs/api/media/indexes/regenerate/endpoints/` | Regenerate endpoints index | — |
| POST | `/docs/api/media/indexes/regenerate/postman/` | Regenerate Postman index | — |
| POST | `/docs/api/media/indexes/regenerate/relationships/` | Regenerate relationships index | — |
| POST | `/docs/api/media/indexes/regenerate/all/` | Regenerate all indexes | — |
| GET | `/docs/api/media/files/<path:file_path>/` | Get media file metadata/content | — |
| PUT | `/docs/api/media/files/<path:file_path>/update/` | Update media file | — |
| DELETE | `/docs/api/media/files/<path:file_path>/delete/` | Delete media file | — |
| POST | `/docs/api/media/sync/<path:file_path>/` | Sync single file | — |

---

## 3. Response format

- **Success (typical):**
  - `success`: `true`
  - `data`: payload (or `items` for some list endpoints)
  - `meta`: optional (e.g. `pagination` with `total`, `page`, `page_size`, `total_pages`, `has_previous`, `has_next`)
  - `timestamp`, `request_id` (when using `APIResponse`)

- **List response shape (API conventions):**
  - **Lambda-parity list endpoints** under `/api/v1/` (pages, endpoints, relationships, postman): use the Lambda-compatible shape with a **resource-named array** and **total**, e.g. `{ "pages": [...], "total": n }`, `{ "endpoints": [...], "total": n }`, `{ "relationships": [...], "total": n }`, `{ "configurations": [...], "total": n }`. No `meta.pagination`; optional query params such as `limit`/`offset` control the window.
  - **Dashboard list endpoints** under `/docs/api/dashboard/*`: use **`data`** (array of items) and **`meta.pagination`** (`total`, `page`, `page_size`, `total_pages`, `has_previous`, `has_next`).
  - **List item payloads (summary-by-default)**: list endpoints now return **summary items** by default (to avoid returning full details for every item). To get the previous “full document per item” behavior, pass **`?expand=full`**.
    - **Pages list item**: `page_id`, `page_type`, `route`, `title`, `status`, `updated_at`, `created_at`
    - **Endpoints list item**: `endpoint_id`, `method`, `api_version`, `endpoint_path`, `state`, `description`
    - **Relationships list item**: `relationship_id`, `page_id`, `endpoint_path`, `method`, `usage_type`, `usage_context`, `state`
    - **Postman list item**: `config_id`, `name`, `state`, `collection_id`, `updated_at`

- **Error:**
  - `success`: `false`
  - `error`: string (or `errors`: array)
  - HTTP status: 4xx/5xx

- **Index invalidation:** Repository writes (create/update/delete) for pages, endpoints, and relationships update the S3 index incrementally via `S3IndexManager` (e.g. `add_item_to_index` / `remove_item_from_index`). The same `S3IndexManager` is used for **read_index** and **validate_index** for all four resource types (pages, endpoints, relationships, postman); Postman index is regenerated via `/docs/api/media/indexes/regenerate/postman/` or regenerate-all when needed. Cache keys for index data are invalidated on index update so list operations reflect changes.

---

## 4. Authentication

- **`/api/v1/`:** No authentication enforced; all GETs are public.
- **`/docs/api/dashboard/*`:** Protected with `@login_required` (session login).
- **`/docs/api/media/*`** and **draft** endpoints:** Implemented in views; check views for any `@login_required` or permission checks.
- Exceptions: media and draft endpoints may vary; see view code.

---

## Summary: Exposed API count

| Area | Count |
|------|--------|
| REST API v1 – Health & root | 5 |
| REST API v1 – Docs/meta (endpoint-stats) | 1 |
| REST API v1 – Pages (Lambda parity) | 17 |
| REST API v1 – Endpoints (Lambda parity) | 25 |
| REST API v1 – Relationships (Lambda parity) | 35 |
| REST API v1 – Postman (Lambda parity) | 12 |
| REST API v1 – Index | — (removed; use UI at `/docs/index/*`) |
| REST API v1 – Dashboard | 4 |
| **REST API v1 total** | **99** |
| Documentation dashboard APIs (`/docs/api/dashboard/`) | 6 |
| Documentation statistics APIs (`/docs/api/statistics/`) | 6 |
| Documentation draft APIs | 2 |
| Documentation media APIs | 14 |
| **Total documented** | **127** |

*The Lambda-parity GETs (pages, endpoints, relationships, postman) are exposed at the same paths under `/api/v1/`. Seventeen endpoints (format, statistics, graph, index, health/external-api) have been removed; use `/docs/api/statistics/*` and `/docs/api/dashboard/graph/` instead. APIs defined in `apps.api` (v2, ai, knowledge, tasks, durgasflow) are **not** mounted in the project root URLconf and are therefore not exposed. Postman collections in `docs/postman/` updated 27_01_2026.*

```18:48:d:\code\ayan\contact\contact360\docsai\docsai\urls.py
urlpatterns = [
    path('', include('apps.core.urls')),
    path('docs/', include('apps.documentation.urls')),
    path('durgasman/', include('apps.durgasman.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('ai/', include('apps.ai_agent.urls')),
    path('codebase/', include('apps.codebase.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('media/', include('apps.media.urls')),
    path('graph/', include('apps.graph.urls')),
    path('tests/', include('apps.test_runner.urls')),
    path('accessibility/', include('apps.accessibility.urls')),
    path('roadmap/', include('apps.roadmap.urls')),
    path('postman/', include('apps.postman.urls')),
    path('templates/', include('apps.templates.urls')),
    path('architecture/', include('apps.architecture.urls')),
    path('database/', include('apps.database.urls')),
    path('json-store/', include('apps.json_store.urls')),
    path('operations/', include('apps.operations.urls')),
    path('page-builder/', include('apps.page_builder.urls')),
    path('knowledge/', include('apps.knowledge.urls')),
    path('api/v1/', include('apps.documentation.api.v1.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', api_docs_index, name='swagger-ui'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-raw'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('durgasflow/', include('apps.durgasflow.urls')),
]
```

### Important discrepancy vs `apps/api/urls.py` (API gateway)

You *do* have an “API gateway” module at `apps/api/urls.py` (it defines `/api/v1/`, `/api/v2/`, `/api/ai/`, `/api/knowledge/`, `/api/tasks/`, `/api/durgasflow/`), **but it is not included anywhere in root**. So today those gateway paths are **not exposed** unless you mount `apps.api.urls` (you currently don’t).

---

## How many exposed endpoints?

**Total exposed URL patterns (endpoints): 494**  
This count includes UI + JSON endpoints + redirect endpoints, but excludes DEBUG-only static/media serving.

### Breakdown by prefix

- **`/docs/`** (documentation app): **326**
- **`/api/v1/`** (Docs REST API v1): **98**
- **Schema/docs endpoints** (`/api/schema/`, `/api/docs/`, `/api/swagger/`, `/api/redoc/`): **4**
- **Everything else (UI apps)**: **66** (core + ai + codebase + tasks + knowledge + durgasflow + etc.)

---

## Full list of exposed endpoints (grouped)

### Root (`/`)

- `/`
- `/login/`
- `/register/`
- `/logout/`

### API docs (drf-spectacular)

- `/api/schema/`
- `/api/docs/`
- `/api/swagger/`
- `/api/redoc/`

### Docs REST API v1 (`/api/v1/`)

**Health + meta (10 routes at this level, plus included resources):**

- `/api/v1/`
- `/api/v1/health/`
- `/api/v1/health/database/`
- `/api/v1/health/cache/`
- `/api/v1/health/storage/`
- `/api/v1/docs/endpoint-stats/`
- `/api/v1/dashboard/pages/`
- `/api/v1/dashboard/endpoints/`
- `/api/v1/dashboard/relationships/`
- `/api/v1/dashboard/postman/`

**Pages (mounted at `/api/v1/pages/`)**

- `/api/v1/pages/`
- `/api/v1/pages/by-type/docs/`
- `/api/v1/pages/by-type/marketing/`
- `/api/v1/pages/by-type/dashboard/`
- `/api/v1/pages/by-type/<page_type>/count/`
- `/api/v1/pages/by-type/<page_type>/published/`
- `/api/v1/pages/by-type/<page_type>/draft/`
- `/api/v1/pages/by-type/<page_type>/stats/`
- `/api/v1/pages/by-state/<state>/`
- `/api/v1/pages/by-state/<state>/count/`
- `/api/v1/pages/<page_id>/access-control/`
- `/api/v1/pages/<page_id>/sections/`
- `/api/v1/pages/<page_id>/components/`
- `/api/v1/pages/<page_id>/endpoints/`
- `/api/v1/pages/<page_id>/versions/`
- `/api/v1/pages/<segment>/`  (either “user_type list” or page-detail, per code)

**Endpoints (mounted at `/api/v1/endpoints/`)**

- `/api/v1/endpoints/`
- `/api/v1/endpoints/by-api-version/v1/`
- `/api/v1/endpoints/by-api-version/v4/`
- `/api/v1/endpoints/by-api-version/graphql/`
- `/api/v1/endpoints/by-api-version/<api_version>/count/`
- `/api/v1/endpoints/by-api-version/<api_version>/stats/`
- `/api/v1/endpoints/by-api-version/<api_version>/by-method/<method>/`
- `/api/v1/endpoints/by-method/GET/`
- `/api/v1/endpoints/by-method/POST/`
- `/api/v1/endpoints/by-method/QUERY/`
- `/api/v1/endpoints/by-method/MUTATION/`
- `/api/v1/endpoints/by-method/<method>/count/`
- `/api/v1/endpoints/by-method/<method>/stats/`
- `/api/v1/endpoints/by-state/<state>/`
- `/api/v1/endpoints/by-state/<state>/count/`
- `/api/v1/endpoints/by-lambda/<service_name>/`
- `/api/v1/endpoints/by-lambda/<service_name>/count/`
- `/api/v1/endpoints/<endpoint_id>/`
- `/api/v1/endpoints/<endpoint_id>/pages/`
- `/api/v1/endpoints/<endpoint_id>/access-control/`
- `/api/v1/endpoints/<endpoint_id>/lambda-services/`
- `/api/v1/endpoints/<endpoint_id>/files/`
- `/api/v1/endpoints/<endpoint_id>/methods/`
- `/api/v1/endpoints/<endpoint_id>/used-by-pages/`
- `/api/v1/endpoints/<endpoint_id>/dependencies/`

**Relationships (mounted at `/api/v1/relationships/`)**

- `/api/v1/relationships/`
- `/api/v1/relationships/usage-types/`
- `/api/v1/relationships/usage-contexts/`
- `/api/v1/relationships/by-page/<page_id>/`
- `/api/v1/relationships/by-page/<page_id>/count/`
- `/api/v1/relationships/by-page/<page_id>/primary/`
- `/api/v1/relationships/by-page/<page_id>/secondary/`
- `/api/v1/relationships/by-page/<page_id>/by-usage-type/<usage_type>/`
- `/api/v1/relationships/by-endpoint/<endpoint_id>/`
- `/api/v1/relationships/by-endpoint/<endpoint_id>/count/`
- `/api/v1/relationships/by-endpoint/<endpoint_id>/pages/`
- `/api/v1/relationships/by-endpoint/<endpoint_id>/by-usage-context/<usage_context>/`
- `/api/v1/relationships/by-usage-type/primary/`
- `/api/v1/relationships/by-usage-type/secondary/`
- `/api/v1/relationships/by-usage-type/conditional/`
- `/api/v1/relationships/by-usage-type/<usage_type>/count/`
- `/api/v1/relationships/by-usage-type/<usage_type>/by-usage-context/<usage_context>/`
- `/api/v1/relationships/by-usage-context/data_fetching/`
- `/api/v1/relationships/by-usage-context/data_mutation/`
- `/api/v1/relationships/by-usage-context/authentication/`
- `/api/v1/relationships/by-usage-context/analytics/`
- `/api/v1/relationships/by-usage-context/<usage_context>/count/`
- `/api/v1/relationships/by-state/<state>/`
- `/api/v1/relationships/by-state/<state>/count/`
- `/api/v1/relationships/by-lambda/<service_name>/`
- `/api/v1/relationships/by-invocation-pattern/<pattern>/`
- `/api/v1/relationships/by-postman-config/<config_id>/`
- `/api/v1/relationships/performance/slow/`
- `/api/v1/relationships/performance/errors/`
- `/api/v1/relationships/<relationship_id>/`
- `/api/v1/relationships/<relationship_id>/access-control/`
- `/api/v1/relationships/<relationship_id>/data-flow/`
- `/api/v1/relationships/<relationship_id>/performance/`
- `/api/v1/relationships/<relationship_id>/dependencies/`
- `/api/v1/relationships/<relationship_id>/postman/`

**Postman (mounted at `/api/v1/postman/`)**

- `/api/v1/postman/`
- `/api/v1/postman/by-state/<state>/`
- `/api/v1/postman/by-state/<state>/count/`
- `/api/v1/postman/<config_id>/`
- `/api/v1/postman/<config_id>/collection/`
- `/api/v1/postman/<config_id>/environments/`
- `/api/v1/postman/<config_id>/environments/<env_name>/`
- `/api/v1/postman/<config_id>/mappings/`
- `/api/v1/postman/<config_id>/mappings/<mapping_id>/`
- `/api/v1/postman/<config_id>/test-suites/`
- `/api/v1/postman/<config_id>/test-suites/<suite_id>/`
- `/api/v1/postman/<config_id>/access-control/`

> Note: `apps.documentation.api.v1.index_urls.py` exists (8 routes), but **is not currently included** by `apps.documentation.api.v1.urls`, so `/api/v1/index/...` isn’t exposed today.

### Documentation app (`/docs/`)

This is the largest surface: **326 endpoints** inside `apps/documentation/urls.py`, including:

- UI dashboards (`/docs/`, `/docs/pages/`, `/docs/endpoints/`, `/docs/relationships/`)
- JSON “dashboard API” under `/docs/api/...`
- A very large **unified “media manager dashboard” route set** under `/docs/pages/...`, `/docs/endpoints/...`, `/docs/relationships/...`, `/docs/postman/...`, `/docs/index/...`, `/docs/dashboard/...`
- Legacy compatibility routes (`/docs/list/`, `/docs/<page_id>/`, etc.)
- A large set of **redirect aliases** under `/docs/media-manager/...`

Because there are 326, the complete raw list is effectively “every `path(...)` in `apps/documentation/urls.py` with `/docs/` prefixed”. That file is the canonical full list.

### Durgasflow UI (`/durgasflow/`)

21 endpoints (workflow list, CRUD, editor, executions, creds, templates, webhook, import).

### Other UI apps

- `/durgasman/` (3)
- `/analytics/` (1)
- `/ai/` (5, includes `/ai/api/chat/`)
- `/codebase/` (7)
- `/tasks/` (6)
- `/knowledge/` (6)
- `/media/` (1)
- `/graph/` (1)
- `/tests/` (1)
- `/accessibility/` (1)
- `/roadmap/` (1)
- `/postman/` (2)
- `/templates/` (1)
- `/architecture/` (1)
- `/database/` (1)
- `/json-store/` (1)
- `/operations/` (1)
- `/page-builder/` (1)

---

## Endpoints that return “a list of items” (best-effort classification)

I’m interpreting “returns a list of items” as endpoints that are **collection/list** responses (often paginated) — not single-item detail endpoints. This includes “list”, “by-* list”, and “dashboard pagination list” endpoints.

### Definitely list endpoints (high confidence)

**Docs REST API v1**

- `/api/v1/pages/`
- `/api/v1/pages/by-state/<state>/`  *(list)*
- `/api/v1/endpoints/`
- `/api/v1/endpoints/by-state/<state>/` *(list)*
- `/api/v1/endpoints/by-lambda/<service_name>/` *(list)*
- `/api/v1/endpoints/by-api-version/<api_version>/by-method/<method>/` *(list)*
- `/api/v1/relationships/`
- `/api/v1/relationships/by-page/<page_id>/` *(list)*
- `/api/v1/relationships/by-endpoint/<endpoint_id>/` *(list)*
- `/api/v1/relationships/by-state/<state>/` *(list)*
- `/api/v1/postman/`
- `/api/v1/postman/by-state/<state>/` *(list)*

**Docs dashboard pagination lists (API v1)**

- `/api/v1/dashboard/pages/`
- `/api/v1/dashboard/endpoints/`
- `/api/v1/dashboard/relationships/`
- `/api/v1/dashboard/postman/`

**Docs dashboard pagination lists (inside `/docs/`)**

- `/docs/api/dashboard/pages/`
- `/docs/api/dashboard/endpoints/`
- `/docs/api/dashboard/relationships/`
- `/docs/api/dashboard/postman/`

**UI list pages**

- `/docs/pages/list/`
- `/docs/endpoints/list/`
- `/docs/relationships/list/`
- `/tasks/` *(task list UI)*
- `/knowledge/` *(knowledge list UI)*
- `/knowledge/search/` *(search results list)*
- `/media/`
- `/templates/`
- `/json-store/`
- `/durgasflow/workflows/`
- `/durgasflow/executions/`
- `/durgasflow/credentials/`
- `/durgasflow/templates/`

### Likely list endpoints (also return lists, but could be aggregates)

These endpoints often return arrays or grouped results:

- `/api/v1/pages/by-type/*` (published/draft lists)
- `/api/v1/endpoints/by-method/*` (method lists)
- `/api/v1/relationships/usage-types/` and `/api/v1/relationships/usage-contexts/` (lists of distinct values)
- Many `/docs/pages/by-type/...`, `/docs/endpoints/by-method/...`, `/docs/relationships/by-.../...` inside the unified dashboard route set in `apps/documentation/urls.py`
