"""
Management command to normalize all index JSON files under media/.

- Regenerates lightweight index.json (pages, endpoints, postman, relationships) via IndexGeneratorService.
- Normalizes full index files (pages_index.json, endpoints_index.json) so each item has all optional keys with null.
- Normalizes relationship/index.json so each relationship entry's pages[] items have all EnhancedRelationship keys.
- Normalizes relationships_index.json so each flat item has all optional EnhancedRelationship keys with null.
- Ensures n8n/index.json has a minimal canonical structure when empty.

By default runs in dry-run mode. Use --write to persist changes.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.documentation.schemas.lambda_models import (
    validate_endpoint_data,
    validate_page_data,
    validate_relationship_data,
)
from apps.documentation.services.index_generator_service import IndexGeneratorService
from apps.documentation.utils.paths import (
    get_endpoints_dir,
    get_n8n_dir,
    get_pages_dir,
    get_postman_dir,
    get_relationships_dir,
)

# All EnhancedRelationship keys (by alias) for adding missing keys with null to flat index items.
ENHANCED_RELATIONSHIP_KEYS = [
    "_id",
    "relationship_id",
    "state",
    "access_control",
    "page_reference",
    "endpoint_reference",
    "connection",
    "files",
    "data_flow",
    "postman_reference",
    "dependencies",
    "performance",
    "metadata",
    "page_path",
    "endpoint_path",
    "method",
    "api_version",
    "via_service",
    "via_hook",
    "usage_type",
    "usage_context",
    "created_at",
    "updated_at",
]

N8N_INDEX_MINIMAL = {
    "version": "2.0",
    "last_updated": None,
    "total": 0,
    "workflows": [],
    "indexes": {},
    "statistics": {},
}


class Command(BaseCommand):
    help = (
        "Normalize all index JSON files (index.json, *_index.json) under media/. "
        "Regenerates lightweight indexes and adds missing keys with null to full indexes. "
        "By default runs in dry-run mode."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Persist normalized index JSON files (default: dry-run).",
        )
        parser.add_argument(
            "--skip-regenerate",
            action="store_true",
            help="Skip regenerating lightweight index.json files; only normalize full indexes.",
        )

    def handle(self, *args, **options) -> None:
        write_changes = bool(options.get("write"))
        skip_regenerate = bool(options.get("skip_regenerate"))

        self.stdout.write(
            self.style.MIGRATE_HEADING("Normalizing media index JSON files")
        )
        if not write_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Running in dry-run mode; use --write to persist changes."
                )
            )

        # 1) Regenerate lightweight index.json files (canonical structure)
        if not skip_regenerate:
            self._regenerate_lightweight_indexes(write_changes)

        # 2) Normalize full index files (add missing keys with null per item)
        self._normalize_pages_index(write_changes)
        self._normalize_endpoints_index(write_changes)
        self._normalize_relationship_index(write_changes)
        self._normalize_relationships_index(write_changes)

        # 3) Ensure n8n/index.json has minimal structure
        self._ensure_n8n_index(write_changes)

        self.stdout.write(self.style.SUCCESS("Index normalization run completed."))

    def _regenerate_lightweight_indexes(self, write_changes: bool) -> None:
        """Regenerate pages, endpoints, postman, relationships index.json via IndexGeneratorService."""
        if not write_changes:
            self.stdout.write(
                self.style.NOTICE(
                    "Dry-run: skip regenerating lightweight index.json (run with --write to regenerate)."
                )
            )
            return
        self.stdout.write(
            self.style.NOTICE("Regenerating lightweight index.json files...")
        )
        gen = IndexGeneratorService()
        out = gen.generate_all_indexes(parallel=True)
        if not out.get("success"):
            self.stderr.write(
                self.style.ERROR(
                    f"Index regeneration had failures: {out.get('results', {})}"
                )
            )
            return
        self.stdout.write(
            self.style.SUCCESS(
                "Lightweight index.json files regenerated."
            )
        )

    def _normalize_pages_index(self, write_changes: bool) -> None:
        """Normalize pages_index.json: each item through validate_page_data (all keys with null)."""
        pages_dir = get_pages_dir()
        fp = pages_dir / "pages_index.json"
        if not fp.exists():
            self.stdout.write(
                self.style.NOTICE(f"[pages_index] File not found: {fp}")
            )
            return
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"[pages_index] Failed to load {fp}: {e}")
            )
            return
        if not isinstance(data, dict) or "pages" not in data:
            self.stdout.write(
                self.style.NOTICE(
                    "[pages_index] Skip: not a dict with 'pages' array."
                )
            )
            return
        pages = data.get("pages") or []
        if not isinstance(pages, list):
            return
        normalized = []
        errors = 0
        for i, item in enumerate(pages):
            try:
                normalized.append(validate_page_data(item))
            except Exception as e:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"[pages_index] Item {i} ({item.get('page_id', '?')}): {e}"
                    )
                )
        if errors:
            self.stderr.write(
                self.style.WARNING(
                    f"[pages_index] {errors} item(s) failed validation."
                )
            )
            return
        data["pages"] = normalized
        if write_changes:
            fp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[pages_index] Normalized {len(normalized)} items, written to {fp.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"[pages_index] Would normalize {len(normalized)} items (dry-run)."
                )
            )

    def _normalize_endpoints_index(self, write_changes: bool) -> None:
        """Normalize endpoints_index.json: each item through validate_endpoint_data."""
        endpoints_dir = get_endpoints_dir()
        fp = endpoints_dir / "endpoints_index.json"
        if not fp.exists():
            self.stdout.write(
                self.style.NOTICE(f"[endpoints_index] File not found: {fp}")
            )
            return
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"[endpoints_index] Failed to load {fp}: {e}")
            )
            return
        if not isinstance(data, dict) or "endpoints" not in data:
            self.stdout.write(
                self.style.NOTICE(
                    "[endpoints_index] Skip: not a dict with 'endpoints' array."
                )
            )
            return
        endpoints = data.get("endpoints") or []
        if not isinstance(endpoints, list):
            return
        normalized = []
        errors = 0
        for i, item in enumerate(endpoints):
            try:
                normalized.append(validate_endpoint_data(item))
            except Exception as e:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"[endpoints_index] Item {i} ({item.get('endpoint_id', '?')}): {e}"
                    )
                )
        if errors:
            self.stderr.write(
                self.style.WARNING(
                    f"[endpoints_index] {errors} item(s) failed validation."
                )
            )
            return
        data["endpoints"] = normalized
        if write_changes:
            fp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[endpoints_index] Normalized {len(normalized)} items, written to {fp.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"[endpoints_index] Would normalize {len(normalized)} items (dry-run)."
                )
            )

    def _normalize_relationship_index(self, write_changes: bool) -> None:
        """Normalize relationship/index.json: each relationships[].pages[] item through validate_relationship_data."""
        rel_dir = get_relationships_dir()
        fp = rel_dir / "index.json"
        if not fp.exists():
            self.stdout.write(
                self.style.NOTICE(f"[relationship/index] File not found: {fp}")
            )
            return
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"[relationship/index] Failed to load {fp}: {e}"
                )
            )
            return
        if not isinstance(data, dict) or "relationships" not in data:
            self.stdout.write(
                self.style.NOTICE(
                    "[relationship/index] Skip: not a dict with 'relationships' array."
                )
            )
            return
        relationships = data.get("relationships") or []
        if not isinstance(relationships, list):
            return
        total_inner = 0
        errors = 0
        for entry in relationships:
            if not isinstance(entry, dict):
                continue
            # By-endpoint: entry has "pages" array
            if "pages" in entry:
                pages = entry.get("pages") or []
                if isinstance(pages, list):
                    normalized_pages = []
                    for item in pages:
                        try:
                            normalized_pages.append(
                                validate_relationship_data(item)
                            )
                            total_inner += 1
                        except Exception as e:
                            errors += 1
                            self.stderr.write(
                                self.style.ERROR(
                                    f"[relationship/index] pages item: {e}"
                                )
                            )
                    entry["pages"] = normalized_pages
            # By-page: entry has "endpoints" array
            if "endpoints" in entry:
                endpoints = entry.get("endpoints") or []
                if isinstance(endpoints, list):
                    normalized_endpoints = []
                    for item in endpoints:
                        try:
                            normalized_endpoints.append(
                                validate_relationship_data(item)
                            )
                            total_inner += 1
                        except Exception as e:
                            errors += 1
                            self.stderr.write(
                                self.style.ERROR(
                                    f"[relationship/index] endpoints item: {e}"
                                )
                            )
                    entry["endpoints"] = normalized_endpoints
        if errors:
            self.stderr.write(
                self.style.WARNING(
                    f"[relationship/index] {errors} inner item(s) failed."
                )
            )
            return
        if write_changes:
            fp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[relationship/index] Normalized {total_inner} pages items, written to {fp.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"[relationship/index] Would normalize {total_inner} pages items (dry-run)."
                )
            )

    def _normalize_relationships_index(self, write_changes: bool) -> None:
        """Normalize relationships_index.json: add missing EnhancedRelationship keys with null to each item."""
        rel_dir = get_relationships_dir()
        fp = rel_dir / "relationships_index.json"
        if not fp.exists():
            self.stdout.write(
                self.style.NOTICE(
                    f"[relationships_index] File not found: {fp}"
                )
            )
            return
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"[relationships_index] Failed to load {fp}: {e}"
                )
            )
            return
        if not isinstance(data, dict) or "relationships" not in data:
            self.stdout.write(
                self.style.NOTICE(
                    "[relationships_index] Skip: not a dict with 'relationships' array."
                )
            )
            return
        relationships = data.get("relationships") or []
        if not isinstance(relationships, list):
            return
        for item in relationships:
            if not isinstance(item, dict):
                continue
            for key in ENHANCED_RELATIONSHIP_KEYS:
                if key not in item:
                    item[key] = None
        if write_changes:
            fp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[relationships_index] Added missing keys to {len(relationships)} items, written to {fp.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"[relationships_index] Would add missing keys to {len(relationships)} items (dry-run)."
                )
            )

    def _ensure_n8n_index(self, write_changes: bool) -> None:
        """Ensure n8n/index.json has minimal canonical structure when empty or missing keys."""
        n8n_dir = get_n8n_dir()
        fp = n8n_dir / "index.json"
        if not n8n_dir.exists():
            self.stdout.write(
                self.style.NOTICE("[n8n/index] n8n directory does not exist.")
            )
            return
        try:
            raw = fp.read_text(encoding="utf-8").strip() if fp.exists() else ""
            if not raw:
                data = None
            else:
                data = json.loads(raw)
        except Exception:
            data = None
        if data is None or not isinstance(data, dict):
            if write_changes:
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(
                    json.dumps(N8N_INDEX_MINIMAL, indent=2),
                    encoding="utf-8",
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[n8n/index] Wrote minimal structure to {fp.name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        "[n8n/index] Would write minimal structure (dry-run)."
                    )
                )
            return
        # Ensure root keys exist
        for key, default in N8N_INDEX_MINIMAL.items():
            if key not in data:
                data[key] = default
        if write_changes:
            fp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[n8n/index] Ensured root keys, written to {fp.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    "[n8n/index] Would ensure root keys (dry-run)."
                )
            )
