# Plan to Modify contact360/docsai Codebase

This document summarizes the analysis of the DocsAI documentation app, the current state of canonical JSON models and normalization, and a task-based plan for modifications. It is intended to be read together with the conversation history and the existing unification work (Pydantic schemas, validators, repositories, management commands).

---

## 1. Executive Summary

**Goals**

- Make `normalize_media_files` run cleanly (no validation/parse errors) by handling index/example files and real-world edge cases.
- Keep a single canonical representation for pages, endpoints, relationships, Postman, and n8n across Django and media JSON.
- Optionally improve Media Manager Dashboard UI once the target (DocsAI dashboard vs S3/n8n list vs both) is confirmed.

**Scope**

- **In scope:** Normalization robustness, schema/validator tweaks where needed, tests/health checks, and a clear task breakdown.
- **Out of scope (until confirmed):** Large UI redesign; this plan only references UI as a future phase.

---

## 2. Current State (Learnings & Analysis)

### 2.1 Architecture

- **Schemas / validation:**  
  `apps/documentation/schemas/lambda_models.py` — legacy normalizers + `validate_page_data`, `validate_endpoint_data`, `validate_relationship_data`, `validate_postman_configuration_data`. Each does legacy normalization then Pydantic validation and returns `model_dump(by_alias=True)`.
- **Canonical models:**  
  `apps/documentation/schemas/pydantic/models.py` (PageDocumentation, EndpointDocumentation, EnhancedRelationship), `postman_models.py` (PostmanConfiguration, PostmanCollection, etc.).
- **Repositories:**  
  Pages, endpoints, relationships, postman use local/S3 storage; relationships_repository uses `validate_relationship_data` before write/index.
- **Paths:**  
  `apps/documentation/utils/paths.py` — `get_media_root()` (default `BASE_DIR/media`), `get_pages_dir()`, `get_endpoints_dir()`, `get_relationships_dir()` (supports legacy `retations`), `get_postman_dir()`, `get_n8n_dir()`, `get_project_dir()`.

### 2.2 Normalization Commands

| Command | Purpose |
|--------|--------|
| `normalize_media_files` | Orchestrator: calls the three below + scans `media/project` and media-root JSON for basic validity. |
| `normalize_media_pages_endpoints` | Pages and endpoints: reads via LocalJSONStorage, validates with `validate_page_data` / `validate_endpoint_data`, optional `--write`. Excludes paths containing `index.json`. |
| `normalize_media_relationships` | Relationships: walks `retations`/`relationships`, treats wrapper-with-`endpoints` list or single dict; each item/dict passed to `validate_relationship_data`. |
| `normalize_media_postman_n8n` | Postman: `media/postman/configurations/*.json` via `validate_postman_configuration_data`. n8n: lightweight structural check + optional `workflow_id` from filename. |

### 2.3 Media Layout

- `media/pages/` — per-page JSON + `index.json`, `pages_index.json` (index is list of pages).
- `media/endpoints/` — per-endpoint JSON + index files.
- `media/retations/` (legacy name) — `by-page/*.json`, `by-endpoint/*.json`, `index.json`, `relationships_index.json`. By-page/by-endpoint files are wrappers: `{ "page_path"|"endpoint_path", "endpoints": [ ... ] }`.
- `media/postman/configurations/` — one JSON per config (e.g. `contact360.json`).
- `media/n8n/` — workflow JSON (e.g. `P2PMigration/Work Distributor.json`).
- `media/project/` — analysis/reports (JSON and other); only basic JSON validity is checked.

### 2.4 Known Errors from `normalize_media_files`

From prior runs and code review:

1. **Pages**
   - **Symptom:** “page_type is required” (Pydantic).
   - **Cause:** Some files are index/example (e.g. index with `pages` array or minimal example without `page_type`), not full `PageDocumentation`.
   - **Fix:** Exclude index/example page files from full validation (by name pattern and/or structure).

2. **Relationships**
   - **Symptom:** Missing `_id` / `relationship_id` for `EnhancedRelationship`.
   - **Cause:** By-page/by-endpoint JSON can contain index-style entries (e.g. only `page_path`, `endpoint_path`, `method`) that are not full relationship documents.
   - **Fix:** Detect index-only relationship files (path or structure) and skip full `EnhancedRelationship` validation (or apply light structural check only).

3. **Postman**
   - **Symptom:** “collection is required” for `PostmanConfiguration`.
   - **Cause:** Validator requires `config_id`, `name`, `collection`, `metadata`; Pydantic expects `collection` as `PostmanCollection`. Either a file is metadata-only or the collection shape doesn’t match (e.g. nested `item` with `null` ids).
   - **Fix:** Add conforming `collection`/`metadata` where possible, or relax validation for metadata-only configs (e.g. optional `collection` with a clear contract).

4. **n8n**
   - **Symptom:** JSON parse error (“Expecting ',' delimiter”) in files like `Work Distributor.json`.
   - **Cause:** Invalid JSON syntax in the file.
   - **Fix:** Fix the JSON in the file, or in the command catch parse errors and report them clearly without failing the whole run; optionally skip invalid n8n files with a clear message.

---

## 3. Modification Plan (Phases)

### Phase 1: Normalization Robustness (Priority)

Make `normalize_media_files` complete without validation/parse errors.

- **1.1 Pages & endpoints**
  - In `normalize_media_pages_endpoints` (and any callers that need it), exclude from full entity validation:
    - Files whose path or name indicates an index: e.g. `index.json`, `*_index.json`, `pages_index.json`.
    - Optionally, files that look like examples: e.g. `*example*.json` (if such exist).
  - Optionally detect by structure: if root has a `pages` or `endpoints` array (index), skip or handle separately (e.g. validate each entry in dry-run only, or only check basic structure).

- **1.2 Relationships**
  - In `normalize_media_relationships`:
    - Treat files under `by-page/` and `by-endpoint/` as index views: do not require each entry to be a full `EnhancedRelationship`.
    - Options: (A) Skip full validation for those paths and only ensure valid JSON and optional light structure; (B) Try full validation per entry and on first failure for that file, fall back to “index-only” (report and skip further validation for that file).
  - Keep full validation for standalone relationship documents (e.g. single-doc files that are not under by-page/by-endpoint).

- **1.3 Postman**
  - For `media/postman/configurations/contact360.json` (and similar):
    - If the file has a `collection` object that fails Pydantic (e.g. nested `item` with `null` ids), either fix the JSON to match `PostmanCollection` or relax the model (e.g. allow `None` for optional nested fields) where it’s safe.
    - If the file is intentionally metadata-only (no collection), extend validator/schema to allow missing `collection` and document the contract (e.g. “metadata-only config”).

- **1.4 n8n**
  - Fix JSON syntax in `Work Distributor.json` (or any other file that fails to parse).
  - In `normalize_media_postman_n8n._normalize_n8n`, on `json.loads` failure: log/print a clear message (file path + error) and continue; do not treat a single bad file as a fatal failure. Optionally count parse errors and report in summary.

### Phase 2: Schema and Repositories (As Needed)

- Only if Phase 1 reveals further schema gaps: adjust Pydantic models or validators (e.g. optional fields, relaxed types) and keep repositories and services using the same canonical DTOs.
- No large refactor of services/APIs in this plan; that was already done in the unification work.

### Phase 3: Media Manager Dashboard UI (Optional, Later)

- **Scope when requested:** Confirm which UI to change (DocsAI Media Manager dashboard vs S3/n8n media list vs unified design).
- Then: break UI work into small tasks (e.g. tab content, labels, validation messages, consistency with canonical enums/fields).

### Phase 4: Tests and Health Checks

- Add or extend tests that run normalization (dry-run) and assert no errors on the current media set (or on a fixture set).
- Ensure health-check routines (if any) that validate media JSON use the same canonical validators and report clear errors.

---

## 4. Task Breakdown (Smaller Tasks)

### A. Normalization: Pages & Endpoints

| # | Task | Details |
|---|------|--------|
| A1 | Exclude index/example page files | In `normalize_media_pages_endpoints._normalize_pages`, exclude paths containing `index.json` or matching `*_index.json` (and optionally `*example*.json`). Ensure `pages_index.json` is excluded. |
| A2 | Exclude index/example endpoint files | Same for `_normalize_endpoints`: exclude `index.json`, `*_index.json`, optional `*example*.json`. |
| A3 | Optional: index structure detection | If a page/endpoint file has root keys `pages`/`endpoints` (index), skip full single-entity validation and optionally validate each entry or only check JSON/structure. |

### B. Normalization: Relationships

| # | Task | Details |
|---|------|--------|
| B1 | Detect by-page/by-endpoint paths | In `normalize_media_relationships`, detect files under `by-page` or `by-endpoint` (e.g. by path). |
| B2 | Skip full validation for index views | For those files, do not call `validate_relationship_data` on each entry; optionally validate JSON and light structure only, and report “index-only, skipped full validation”. |
| B3 | Keep full validation for standalone docs | For relationship JSON not under by-page/by-endpoint, keep current behavior (full EnhancedRelationship validation). |

### C. Normalization: Postman

| # | Task | Details |
|---|------|--------|
| C1 | Inspect contact360.json vs PostmanCollection | Confirm exact Pydantic error (e.g. nested `item` with `id: null`). |
| C2 | Fix schema or JSON | Either relax PostmanCollection/PostmanConfiguration (e.g. optional ids) or fix the JSON so it validates. |
| C3 | Optional: metadata-only configs | If needed, allow `collection` to be optional in validator and Pydantic model and document when to use it. |

### D. Normalization: n8n

| # | Task | Details |
|---|------|--------|
| D1 | Fix Work Distributor.json | Locate and fix the “Expecting ',' delimiter” (or similar) parse error in the file. |
| D2 | Graceful parse failure handling | In `_normalize_n8n`, catch `json.loads` exceptions, log/print file path and error, increment error count, continue. Report parse errors in summary. |

### E. Tests & Health

| # | Task | Details |
|---|------|--------|
| E1 | Test normalize_media_* dry-run | Add or extend tests that run `normalize_media_pages_endpoints`, `normalize_media_relationships`, `normalize_media_postman_n8n` (and optionally `normalize_media_files`) in dry-run and assert zero validation/parse errors on current or fixture media. |
| E2 | Health checks | Ensure any health-check code that validates media JSON uses the same validators and returns clear, actionable errors. |

### F. Documentation & UI (Optional)

| # | Task | Details |
|---|------|--------|
| F1 | Update docs | Document index/example exclusion rules and “index-only” relationship handling in this plan or in a README in the management commands. |
| F2 | UI tasks | When scope is confirmed: break Media Manager (and/or S3/n8n list) UI changes into small tasks (labels, validation messages, enums). |

---

## 5. Implementation Order

1. **A1, A2** — Quick wins; prevent index/example pages and endpoints from failing.
2. **D2** — So that one bad n8n file doesn’t obscure the rest of the run.
3. **D1** — Fix the actual JSON so the repo is clean.
4. **B1, B2, B3** — Relationships index handling.
5. **C1, C2 (and C3 if needed)** — Postman validation.
6. **A3** — Optional index-structure detection for pages/endpoints.
7. **E1, E2** — Tests and health checks.
8. **F1, F2** — Docs and UI when needed.

---

## 6. Success Criteria

- `python manage.py normalize_media_files` (dry-run and, where intended, `--write`) completes with no validation errors and no unhandled parse errors.
- All modified code paths use the existing canonical Pydantic models and validators; no duplicate or divergent JSON shapes.
- New or updated tests and health checks reflect the above behavior and are green.

---

## 7. References

- Schemas: `apps/documentation/schemas/lambda_models.py`, `schemas/pydantic/models.py`, `schemas/pydantic/postman_models.py`
- Commands: `apps/documentation/management/commands/normalize_media_*.py`
- Paths: `apps/documentation/utils/paths.py`
- Repositories: `apps/documentation/repositories/relationships_repository.py`, `local_json_storage.py`
- Dashboard: `apps/documentation/views/media_manager_dashboard.py`, `services/media_manager_dashboard_service.py`, `templates/documentation/media_manager_dashboard.html`
