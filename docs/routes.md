# DocsAI Routes Reference

Complete URL routing for the contact360/docsai Django project. Root URLconf: `docsai/urls.py`; each app is mounted under a prefix.

---

## Table of contents

1. [Route tree (prefix → app)](#1-route-tree-prefix--app)
2. [Core (`/`)](#2-core-)
3. [Documentation (`/docs/`)](#3-documentation-docs)
4. [Durgasman (`/durgasman/`)](#4-durgasman-durgasman)
5. [Analytics, AI, Codebase, Tasks, Media, Graph](#5-analytics-ai-codebase-tasks-media-graph)
6. [Test runner, Accessibility, Roadmap, Postman, Templates](#6-test-runner-accessibility-roadmap-postman-templates)
7. [Architecture, Database, JSON store, Operations, Page builder](#7-architecture-database-json-store-operations-page-builder)
8. [Knowledge (`/knowledge/`)](#8-knowledge-knowledge)
9. [Durgasflow (`/durgasflow/`)](#9-durgasflow-durgasflow)
10. [REST API v1 (`/api/v1/`)](#10-rest-api-v1-apiv1)

---

## 1. Route tree (prefix → app)

| Prefix | App | Main purpose |
|--------|-----|----------------|
| `/` | core | Dashboard, auth (login, register, logout) |
| `/docs/` | documentation | Docs dashboard, pages/endpoints/relationships/postman/media/operations |
| `/durgasman/` | durgasman | API studio (collections, import) |
| `/analytics/` | analytics | Analytics view |
| `/ai/` | ai_agent | AI chat, sessions |
| `/codebase/` | codebase | Codebase scan, analyses |
| `/tasks/` | tasks | Task list, CRUD, start/complete |
| `/media/` | media | Media list |
| `/graph/` | graph | Graph visualization |
| `/tests/` | test_runner | Test runner |
| `/accessibility/` | accessibility | Accessibility |
| `/roadmap/` | roadmap | Roadmap |
| `/postman/` | postman | Postman home and dashboard |
| `/templates/` | templates | Templates list |
| `/architecture/` | architecture | Architecture/blueprint |
| `/database/` | database | Database/schema |
| `/json-store/` | json_store | JSON store list |
| `/operations/` | operations | Operations dashboard |
| `/page-builder/` | page_builder | Page builder/editor |
| `/knowledge/` | knowledge | Knowledge base CRUD, search |
| `/durgasflow/` | durgasflow | Workflows, editor, executions, credentials, webhooks |
| `/api/v1/` | documentation.api.v1 | REST API (health, pages, endpoints, relationships, postman, dashboard) |

**API docs (project root):** `/api/docs/` → Django-built API reference (all GET endpoints + per-endpoint stats). `/api/swagger/` → Swagger UI. `/api/schema/` → OpenAPI schema. `/api/redoc/` → ReDoc.

In **DEBUG**, static and media files are served from `STATIC_URL` and `MEDIA_URL` (see `docsai/urls.py`).

---

## 2. Core (`/`)

| Path | Name | View |
|------|------|------|
| `/` | dashboard | core.views.dashboard_view |
| `/login/` | login | core.views.login_view |
| `/register/` | register | core.views.register_view |
| `/logout/` | logout | core.views.logout_view |

---

## 3. Documentation (`/docs/`)

All paths below are relative to `/docs/`.

### Dashboard (SPA entry)

| Path | Name |
|------|------|
| `` | dashboard |
| `pages/` | dashboard_pages |
| `endpoints/` | dashboard_endpoints |
| `relationships/` | dashboard_relationships |

### Dashboard APIs (JSON)

| Path | Name |
|------|------|
| `api/dashboard/pages/` | api_dashboard_pages |
| `api/dashboard/endpoints/` | api_dashboard_endpoints |
| `api/dashboard/relationships/` | api_dashboard_relationships |
| `api/dashboard/postman/` | api_dashboard_postman |
| `api/dashboard/graph/` | api_dashboard_graph |
| `api/dashboard/bulk-delete/` | api_dashboard_bulk_delete |

### Pages CRUD

| Path | Name |
|------|------|
| `pages/list/` | pages_list |
| `pages/<page_id>/` | page_detail |
| `pages/create/` | page_create |
| `pages/<page_id>/edit/` | page_edit |
| `pages/<page_id>/update/` | page_update |
| `pages/<page_id>/delete/` | page_delete |

### Endpoints CRUD

| Path | Name |
|------|------|
| `endpoints/list/` | endpoints_list |
| `endpoints/<endpoint_id>/` | endpoint_detail |
| `endpoints/create/` | endpoint_create |
| `endpoints/<endpoint_id>/edit/` | endpoint_edit |
| `endpoints/<endpoint_id>/delete/` | endpoint_delete |
| `api/endpoints/draft/` | api_endpoint_draft |
| `api/pages/draft/` | api_page_draft |

### Relationships CRUD

| Path | Name |
|------|------|
| `relationships/list/` | relationships_list |
| `relationships/<relationship_id>/` | relationship_detail |
| `relationships/create/` | relationship_create |
| `relationships/<relationship_id>/edit/` | relationship_edit |

### Postman CRUD

| Path | Name |
|------|------|
| `postman/create/` | postman_create |
| `postman/<postman_id>/edit/` | postman_edit |
| `postman/<postman_id>/` | postman_detail |

### Media (UI + API)

| Path | Name |
|------|------|
| `media-manager/` | media_manager (redirect to dashboard) |
| `media/preview/<path:file_path>` | media_file_preview |
| `media/viewer/<path:file_path>` | media_file_viewer |
| `media/form/create/` | media_file_form |
| `media/form/edit/<path:file_path>` | media_file_form_edit |
| `media/delete/<path:file_path>` | media_file_delete_confirm |
| `media/file/<path:file_path>/analyze/` | media_file_analyze |
| `media/file/<path:file_path>/validate/` | media_file_validate |
| `media/file/<path:file_path>/generate-json/` | media_file_generate_json |
| `media/file/<path:file_path>/upload-s3/` | media_file_upload_s3 |
| `api/media/files/` | api_media_files (list) |
| `api/media/files/create/` | api_media_file_create |
| `api/media/sync-status/` | api_media_sync_status |
| `api/media/bulk-sync/` | api_media_bulk_sync |
| `api/media/indexes/regenerate/pages/` | api_media_regenerate_pages_index |
| `api/media/indexes/regenerate/endpoints/` | api_media_regenerate_endpoints_index |
| `api/media/indexes/regenerate/postman/` | api_media_regenerate_postman_index |
| `api/media/indexes/regenerate/relationships/` | api_media_regenerate_relationships_index |
| `api/media/indexes/regenerate/all/` | api_media_regenerate_all_indexes |
| `api/media/files/<path:file_path>/` | api_media_file (get) |
| `api/media/files/<path:file_path>/update/` | api_media_file_update |
| `api/media/files/<path:file_path>/delete/` | api_media_file_delete |
| `api/media/sync/<path:file_path>/` | api_media_sync_file |

### Operations

| Path | Name |
|------|------|
| `operations/` | operations_dashboard |
| `operations/analyze/` | operations_analyze |
| `operations/validate/` | operations_validate |
| `operations/generate-json/` | operations_generate_json |
| `operations/generate-postman/` | operations_generate_postman |
| `operations/upload/` | operations_upload |
| `operations/seed/` | operations_seed |
| `operations/workflow/` | operations_workflow |
| `operations/status/` | operations_status |
| `operations/tasks/` | operations_tasks |
| `operations/tasks/<task_id>/` | operations_task_detail |

### Legacy (backward compatibility)

| Path | Name |
|------|------|
| `list/` | list |
| `<page_id>/` | detail |
| `create/` | create |
| `<page_id>/update/` | update |
| `<page_id>/delete/` | delete |

---

## 4. Durgasman (`/durgasman/`)

| Path | Name |
|------|------|
| `` | dashboard |
| `collection/<int:collection_id>/` | collection_detail |
| `import/` | import |

---

## 5. Analytics, AI, Codebase, Tasks, Media, Graph

- **Analytics** (`/analytics/`): `` → dashboard.
- **AI agent** (`/ai/`): `` → redirect to chat; `chat/`, `sessions/`, `sessions/<session_id>/`.
- **Codebase** (`/codebase/`): ``, `scan/`, `analyses/<analysis_id>/`, `analyses/<analysis_id>/files/`, `analyses/<analysis_id>/files/<path:file_path>/`, `analyses/<analysis_id>/dependencies/`, `analyses/<analysis_id>/patterns/`.
- **Tasks** (`/tasks/`): ``, `create/`, `<task_id>/`, `<task_id>/start/`, `<task_id>/complete/`, `<task_id>/edit/`.
- **Media** (`/media/`): `` → list.
- **Graph** (`/graph/`): `` → visualization.

---

## 6. Test runner, Accessibility, Roadmap, Postman, Templates

- **Test runner** (`/tests/`): `` → dashboard.
- **Accessibility** (`/accessibility/`): `` → dashboard.
- **Roadmap** (`/roadmap/`): `` → dashboard.
- **Postman** (`/postman/`): ``, `dashboard/`.
- **Templates** (`/templates/`): `` → list.

---

## 7. Architecture, Database, JSON store, Operations, Page builder

- **Architecture** (`/architecture/`): `` → blueprint.
- **Database** (`/database/`): `` → schema.
- **JSON store** (`/json-store/`): `` → list.
- **Operations** (`/operations/`): `` → dashboard.
- **Page builder** (`/page-builder/`): `` → editor.

---

## 8. Knowledge (`/knowledge/`)

| Path | Name |
|------|------|
| `` | list |
| `create/` | create |
| `<uuid:knowledge_id>/` | detail |
| `<uuid:knowledge_id>/edit/` | edit |
| `<uuid:knowledge_id>/delete/` | delete |
| `search/` | search |

---

## 9. Durgasflow (`/durgasflow/`)

| Path | Name |
|------|------|
| `` | dashboard |
| `workflows/` | workflow_list |
| `workflow/create/` | workflow_create |
| `workflow/<workflow_id>/` | workflow_detail |
| `workflow/<workflow_id>/edit/` | workflow_edit |
| `workflow/<workflow_id>/delete/` | workflow_delete |
| `workflow/<workflow_id>/execute/` | workflow_execute |
| `workflow/<workflow_id>/activate/` | workflow_activate |
| `workflow/<workflow_id>/deactivate/` | workflow_deactivate |
| `editor/<workflow_id>/` | editor |
| `editor/new/` | editor_new |
| `executions/` | execution_list |
| `execution/<execution_id>/` | execution_detail |
| `credentials/` | credential_list |
| `credential/create/` | credential_create |
| `credential/<credential_id>/` | credential_detail |
| `credential/<credential_id>/delete/` | credential_delete |
| `templates/` | template_list |
| `template/<template_id>/use/` | template_use |
| `import/n8n/<path:workflow_path>/` | import_n8n |
| `webhook/<workflow_id>/<webhook_path>/` | webhook_handler |

---

## 10. REST API v1 (`/api/v1/`)

URLconf: `apps.documentation.api.v1.urls`. See [api.md](./api.md) for full reference.

- **Health (6):** ``, `health/`, `health/database/`, `health/cache/`, `health/storage/`. (Note: `health/external-api/` removed - Lambda client removed)
- **Pages (18):** `pages/` (include `apps.documentation.api.v1.pages_urls`) – list, by-type, by-state, by user_type/page_id, sub-resources. (Note: `format/`, `statistics/`, `types/` removed - use `/docs/api/statistics/pages/*` instead)
- **Endpoints (26):** `endpoints/` (include `endpoints_urls`) – list, by-api-version, by-method, by-state, by-lambda, detail and sub-resources. (Note: `format/`, `api-versions/`, `methods/` removed - use `/docs/api/statistics/endpoints/*` instead)
- **Relationships (36):** `relationships/` (include `relationships_urls`) – list, usage-types/contexts, by-page, by-endpoint, by-usage-type, by-usage-context, by-state, by-lambda, performance, detail and sub-resources. (Note: `format/`, `graph/`, `statistics/` removed - use `/docs/api/dashboard/graph/` and `/docs/api/statistics/relationships/*` instead)
- **Postman (12):** `postman/` (include `postman_urls`) – list, by-state, detail, collection, environments, mappings, test-suites, access-control. (Note: `statistics/`, `format/` removed - use `/docs/api/statistics/postman/*` instead)
- **Index (Removed):** Index endpoints removed. Use UI routes at `/docs/index/*` instead.
- **Dashboard (4):** `dashboard/pages/`, `dashboard/endpoints/`, `dashboard/relationships/`, `dashboard/postman/`.

All listed above are GET. Total 93 Lambda-parity GETs plus health, docs/endpoint-stats, and dashboard. (17 endpoints removed: format, statistics, graph, index, health/external-api)
