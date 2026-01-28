"""
Management command to normalize local media JSON for pages and endpoints.

This command is the implementation hook for the migration plan that unifies
JSON formats across the Django codebase and the ``media/`` folder. It:

- Reads ``media/pages/*.json`` and ``media/endpoints/*.json`` via LocalJSONStorage
- Validates and normalizes them using the canonical Pydantic-backed validators
  in ``apps.documentation.schemas.lambda_models``
- Optionally writes the normalized JSON back to disk

By default the command runs in dry-run mode and only reports what it would do.
Use ``--write`` to actually persist normalized JSON files.
"""

from pathlib import Path
from typing import List

from django.core.management.base import BaseCommand

from apps.documentation.repositories.local_json_storage import LocalJSONStorage
from apps.documentation.schemas.lambda_models import (
    validate_endpoint_data,
    validate_page_data,
)


class Command(BaseCommand):
    help = (
        "Normalize media JSON files for pages and endpoints using the canonical "
        "Pydantic-backed validators. By default runs in dry-run mode."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Write normalized JSON back to media files (default: dry-run).",
        )
        parser.add_argument(
            "--resources",
            nargs="*",
            choices=["pages", "endpoints"],
            default=["pages", "endpoints"],
            help="Resource types to normalize (default: pages and endpoints).",
        )

    def handle(self, *args, **options) -> None:
        write_changes: bool = bool(options.get("write"))
        resources: List[str] = options.get("resources") or ["pages", "endpoints"]

        storage = LocalJSONStorage()

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Normalizing media JSON for resources: {', '.join(resources)}"
            )
        )
        if not write_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Running in dry-run mode (no files will be modified). "
                    "Use --write to persist normalized JSON."
                )
            )

        if "pages" in resources:
            self._normalize_pages(storage, write_changes)

        if "endpoints" in resources:
            self._normalize_endpoints(storage, write_changes)

        self.stdout.write(self.style.SUCCESS("Normalization run completed."))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_index_or_example_file(rel_path: str) -> bool:
        """Return True if the file is an index or example (skip full entity validation)."""
        name = Path(rel_path).name.lower()
        if name == "index.json":
            return True
        if name.endswith("_index.json"):
            return True
        if "example" in name:
            return True
        return False

    def _normalize_pages(self, storage: LocalJSONStorage, write_changes: bool) -> None:
        page_files = storage.list_files("pages", "*.json")
        page_files = [
            fp for fp in page_files
            if not self._is_index_or_example_file(fp)
        ]

        self.stdout.write(
            self.style.NOTICE(f"Found {len(page_files)} page JSON files to check.")
        )

        normalized_count = 0
        error_count = 0
        skipped_index = 0

        for rel_path in page_files:
            try:
                data = storage.read_json(rel_path)
                if not data:
                    continue
                # Skip index-by-structure: root has "pages" array
                if isinstance(data, dict) and "pages" in data and isinstance(data.get("pages"), list):
                    skipped_index += 1
                    continue

                normalized = validate_page_data(data)

                if write_changes:
                    storage.write_json(rel_path, normalized)
                normalized_count += 1
            except Exception as exc:  # pragma: no cover - safety net
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"[pages] Failed to normalize {rel_path}: {exc}"
                    )
                )

        if skipped_index:
            self.stdout.write(
                self.style.NOTICE(f"[pages] Skipped {skipped_index} index/structure file(s).")
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"[pages] Normalized {normalized_count} files "
                f"({error_count} errors, {'written' if write_changes else 'dry-run'})."
            )
        )

    def _normalize_endpoints(
        self, storage: LocalJSONStorage, write_changes: bool
    ) -> None:
        endpoint_files = storage.list_files("endpoints", "*.json")
        endpoint_files = [
            fp for fp in endpoint_files
            if not self._is_index_or_example_file(fp)
        ]

        self.stdout.write(
            self.style.NOTICE(
                f"Found {len(endpoint_files)} endpoint JSON files to check."
            )
        )

        normalized_count = 0
        error_count = 0
        skipped_index = 0

        for rel_path in endpoint_files:
            try:
                data = storage.read_json(rel_path)
                if not data:
                    continue
                # Skip index-by-structure: root has "endpoints" array
                if isinstance(data, dict) and "endpoints" in data and isinstance(data.get("endpoints"), list):
                    skipped_index += 1
                    continue

                normalized = validate_endpoint_data(data)

                if write_changes:
                    storage.write_json(rel_path, normalized)
                normalized_count += 1
            except Exception as exc:  # pragma: no cover - safety net
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"[endpoints] Failed to normalize {rel_path}: {exc}"
                    )
                )

        if skipped_index:
            self.stdout.write(
                self.style.NOTICE(f"[endpoints] Skipped {skipped_index} index/structure file(s).")
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"[endpoints] Normalized {normalized_count} files "
                f"({error_count} errors, {'written' if write_changes else 'dry-run'})."
            )
        )

