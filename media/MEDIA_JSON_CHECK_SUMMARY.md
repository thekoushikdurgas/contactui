# Media JSON Check – Task Breakdown & Summary

This document summarizes the **check and modify** of all JSON files under `media/` (pages, endpoints, postman, relationship, n8n, project) and the smaller tasks used to do it.

---

## Scope

| Folder | Resource | Count (approx) | Schema / Action |
|--------|----------|----------------|-----------------|
| **media/pages** | Page docs + index + pages_index | 52 | Pydantic PageDocumentation; add missing keys with null |
| **media/endpoints** | Endpoint docs + index + endpoints_index | 156 | Pydantic EndpointDocumentation; add missing keys with null |
| **media/postman** | Configs + collection + environment + index | 7 | PostmanConfiguration for configs; index canonical |
| **media/relationship** | by-page, by-endpoint, index, relationships_index | 107 | EnhancedRelationship; add missing keys with null |
| **media/n8n** | Workflows + index | 48 | workflow_id if missing; index minimal structure |
| **media/project** | Inventories + validation JSON | 6 | Valid JSON; 07_validation_errors issue keys per doc |

**Total:** 421 JSON files checked.

---

## Smaller Tasks (Breakdown)

1. **media/pages** – Check and normalize page docs + index  
   - Run `normalize_media_pages_endpoints` (validates/normalizes each page JSON).  
   - Run `normalize_media_indexes` (regenerates `index.json`, normalizes `pages_index.json`).

2. **media/endpoints** – Check and normalize endpoint docs + index  
   - Same `normalize_media_pages_endpoints` (endpoint JSON).  
   - Same `normalize_media_indexes` (regenerates `index.json`, normalizes `endpoints_index.json`).

3. **media/postman** – Check and normalize configs + index  
   - Run `normalize_media_postman_n8n` (Postman configuration JSON).  
   - Run `normalize_media_indexes` (regenerates postman `index.json`).  
   - Collection/environment JSON: not PostmanConfiguration; left as-is (valid JSON).

4. **media/relationship** – Check and normalize by-page, by-endpoint, index  
   - Run `normalize_media_relationships` (each relationship object via `validate_relationship_data`).  
   - Run `normalize_media_indexes` (relationship `index.json` + `relationships_index.json`).

5. **media/n8n** – Check and normalize workflows + index  
   - Run `normalize_media_postman_n8n` (add `workflow_id` if missing).  
   - Run `normalize_media_indexes` (ensure n8n `index.json` minimal structure).

6. **media/project** – Check valid JSON + doc keys  
   - Run `normalize_media_files` (scans project JSON for validity).  
   - Manually add missing doc keys to `07_validation_errors.json` issue objects (e.g. `affected_pages`, `schema_expects` with null where missing).

7. **Validate all JSON** – Ensure every file parses  
   - Iterate all `media/**/*.json`; `json.load()`; report parse errors.  
   - Result: 421 files, 0 parse errors.

---

## Commands Used

```bash
# Full resource normalization (pages, endpoints, relationships, postman, n8n)
python manage.py normalize_media_files --write

# Index normalization (lightweight + full indexes + n8n index)
python manage.py normalize_media_indexes --write
```

Dry-run (no writes):

```bash
python manage.py normalize_media_files
python manage.py normalize_media_indexes --write --skip-regenerate
```

---

## Result

- **Pages:** 50 page docs normalized; `index.json` regenerated; `pages_index.json` normalized (50 items).  
- **Endpoints:** 154 endpoint docs normalized; `index.json` regenerated; `endpoints_index.json` normalized (154 items).  
- **Postman:** 1 configuration normalized; `index.json` regenerated.  
- **Relationship:** 125 relationship files processed (220 relationship objects normalized); `index.json` and `relationships_index.json` normalized (110 items with full EnhancedRelationship keys).  
- **n8n:** 47 workflow files checked (`workflow_id` added if missing); `index.json` minimal structure ensured.  
- **Project:** 6 JSON files valid; `07_validation_errors.json` issue objects aligned with doc (missing keys added with null).  
- **Parse check:** All 421 JSON files parse successfully.

---

## References

- JSON models: `docs/json_models/` (pages, endpoints, postman, project, relationship, n8n).  
- Paths: `apps/documentation/utils/paths.py`.  
- Validators: `apps/documentation/schemas/lambda_models.py` (`validate_page_data`, `validate_endpoint_data`, `validate_relationship_data`, `validate_postman_configuration_data`).
