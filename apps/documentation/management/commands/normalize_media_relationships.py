"""
Management command to normalize local media JSON for relationships.

Depending on deployment and migration strategy, relationships may be stored as:

- Individual relationship JSON documents in an S3 bucket (managed by RelationshipsRepository)
- Index-style JSON under ``media/relationship`` / ``media/relationships`` on disk

This command focuses on the latter: reading relationship JSON files from the
local media directory and validating/normalizing them via the canonical
Pydantic-backed ``validate_relationship_data`` helper.

By default the command runs in dry-run mode and only reports what it would do.
Use ``--write`` to actually persist normalized JSON files.
"""

from pathlib import Path
from typing import List

from django.core.management.base import BaseCommand

from apps.documentation.schemas.lambda_models import validate_relationship_data
from apps.documentation.utils.paths import get_relationships_dir


class Command(BaseCommand):
    help = (
        "Normalize media JSON files for relationships using the canonical "
        "Pydantic-backed validators. By default runs in dry-run mode."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Write normalized JSON back to media files (default: dry-run).",
        )

    def handle(self, *args, **options) -> None:
        write_changes: bool = bool(options.get("write"))

        relationships_dir: Path = get_relationships_dir()
        if not relationships_dir.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Relationships directory does not exist: {relationships_dir}"
                )
            )
            return

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Normalizing relationship JSON under {relationships_dir}"
            )
        )
        if not write_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Running in dry-run mode (no files will be modified). "
                    "Use --write to persist normalized JSON."
                )
            )

        # We treat any *.json that is not an index or result wrapper as a relationship document,
        # including both root-level and nested directories such as by-page/by-endpoint.
        # Skip index files and *_result.json (upload/sync result wrappers, not EnhancedRelationship).
        json_files: List[Path] = [
            p
            for p in relationships_dir.rglob("*.json")
            if p.name not in {"index.json", "relationships_index.json"}
            and not p.name.endswith("_result.json")
        ]

        self.stdout.write(
            self.style.NOTICE(f"Found {len(json_files)} relationship JSON files to check.")
        )

        normalized_count = 0
        error_count = 0

        for fp in json_files:
            try:
                raw = fp.read_text(encoding="utf-8")
                if not raw.strip():
                    continue

                import json

                data = json.loads(raw)

                # Wrapper with "pages" list (by-endpoint): normalize each entry.
                if isinstance(data, dict) and "pages" in data and isinstance(
                    data["pages"], list
                ):
                    changed_items = []
                    for item in data["pages"]:
                        try:
                            normalized = validate_relationship_data(item)
                            changed_items.append(normalized)
                        except Exception as item_exc:  # pragma: no cover - safety net
                            error_count += 1
                            self.stderr.write(
                                self.style.ERROR(
                                    f"[relationships] Failed to normalize entry in {fp}: {item_exc}"
                                )
                            )
                    if write_changes and len(changed_items) == len(data["pages"]):
                        data["pages"] = changed_items
                        fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                    normalized_count += len(changed_items)
                # Wrapper with "endpoints" list (by-page or similar): normalize each entry.
                elif isinstance(data, dict) and "endpoints" in data and isinstance(
                    data["endpoints"], list
                ):
                    changed_items = []
                    for item in data["endpoints"]:
                        try:
                            normalized = validate_relationship_data(item)
                            changed_items.append(normalized)
                        except Exception as item_exc:  # pragma: no cover - safety net
                            error_count += 1
                            self.stderr.write(
                                self.style.ERROR(
                                    f"[relationships] Failed to normalize entry in {fp}: {item_exc}"
                                )
                            )
                    if write_changes and len(changed_items) == len(data["endpoints"]):
                        data["endpoints"] = changed_items
                        fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                    normalized_count += len(changed_items)
                elif isinstance(data, dict):
                    normalized = validate_relationship_data(data)
                    if write_changes:
                        fp.write_text(
                            json.dumps(normalized, indent=2, ensure_ascii=False),
                            encoding="utf-8",
                        )
                    normalized_count += 1
            except Exception as exc:  # pragma: no cover - safety net
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"[relationships] Failed to normalize {fp}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"[relationships] Normalized {normalized_count} items "
                f"({error_count} errors, {'written' if write_changes else 'dry-run'})."
            )
        )

