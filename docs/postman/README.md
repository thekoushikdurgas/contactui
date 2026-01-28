# DocsAI Postman

Postman collection and environment for the **DocsAI API v1** (`/api/v1/`). The collection covers **110 Lambda-parity GET endpoints** plus health and dashboard (119 REST API v1 requests total).

## Files

| File | Description |
|------|-------------|
| `DocsAI_API_v1.postman_collection.json` | Collection: Health (6), Pages (20), Endpoints (28), Relationships (38), Postman (14), Index (8), Dashboard (4) |
| `DocsAI_Local.postman_environment.json` | Local environment: `baseUrl` (e.g. `http://localhost:8000`) and path/query variables |

## Import in Postman

1. **Import collection:** File → Import → select `DocsAI_API_v1.postman_collection.json`.
2. **Import environment:** File → Import → select `DocsAI_Local.postman_environment.json`.
3. **Select environment:** In the top-right env dropdown, choose **DocsAI - Local**.
4. **Run:** Ensure the Django server is running (e.g. `python manage.py runserver` on port 8000).

## Collection structure

| Folder | Requests | Description |
|--------|----------|-------------|
| **Health & Info** | 6 | Service info, health (full), health/database, health/cache, health/storage, health/external-api |
| **Pages** | 20 | List, format, statistics, types; by-type (docs, marketing, dashboard, count, published, draft, stats); by-state (list, count); by user type or page detail; page detail + access-control, sections, components, endpoints, versions |
| **Endpoints** | 28 | List, format; api-versions, methods; by-api-version (v1, v4, graphql, count, stats, by-method); by-method (GET, POST, QUERY, MUTATION, count, stats); by-state, by-lambda; detail + pages, access-control, lambda-services, files, methods, used-by-pages, dependencies |
| **Relationships** | 38 | List, format, graph, statistics, usage-types, usage-contexts; by-page, by-endpoint, by-usage-type, by-usage-context, by-state, by-lambda, by-invocation-pattern, by-postman-config; performance/slow, performance/errors; detail + access-control, data-flow, performance, dependencies, postman |
| **Postman** | 14 | List, statistics, format; by-state (list, count); config detail + collection, environments (list + by name), mappings (list + by id), test-suites (list + by id), access-control |
| **Index** | 8 | Read index: pages, endpoints, relationships, postman; Validate: pages, endpoints, relationships, postman |
| **Dashboard** | 4 | dashboard/pages, dashboard/endpoints, dashboard/relationships, dashboard/postman (paginated) |

## Variables

Set in collection or environment:

- **baseUrl** – Server base URL (default `http://localhost:8000`).
- **page_id**, **endpoint_id**, **relationship_id**, **config_id** – IDs for detail and sub-resource requests; fill from list responses.
- **user_type**, **state**, **page_type**, **api_version**, **method**, **usage_type**, **usage_context** – Path/query examples (e.g. `state=published`, `page_type=docs`).
- **service_name**, **pattern** – For by-lambda and by-invocation-pattern.
- **env_name**, **mapping_id**, **suite_id** – For Postman config sub-resources (environment by name, mapping by id, test suite by id).
- **expand** – Optional. Set to `full` to return full documents per item on list endpoints. Default (empty) returns summary list items.

For **detail** requests, set the corresponding ID in the environment after getting IDs from a list or index request.

## API docs

See [../api.md](../api.md) for full request/response shapes, query parameters, and authentication.
