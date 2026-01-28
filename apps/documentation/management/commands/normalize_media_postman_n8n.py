"""
Management command to normalize local media JSON for Postman and n8n resources.

This command is part of the unified JSON model migration plan. It provides
hooks to:

- Load Postman configuration JSON under ``media/postman`` and validate/normalize
  them against the canonical Pydantic PostmanConfiguration model.
- Load n8n workflow JSON under ``media/n8n`` and (optionally) validate/normalize
  them once a canonical Pydantic model is introduced.

At present, n8n normalization is implemented as a structural sanity check
without a strict Pydantic model, to avoid over-constraining existing workflows.
You can tighten this later once a stable schema is agreed.

By default the command runs in dry-run mode and only reports what it would do.
Use ``--write`` to actually persist normalized JSON files.
"""

from pathlib import Path
from typing import List

from django.core.management.base import BaseCommand

from apps.documentation.schemas.lambda_models import validate_postman_configuration_data
from apps.documentation.utils.paths import get_n8n_dir, get_postman_dir


class Command(BaseCommand):
    help = (
        "Normalize media JSON files for Postman configurations and n8n workflows. "
        "By default runs in dry-run mode."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Write normalized JSON back to media files (default: dry-run).",
        )
        parser.add_argument(
            "--skip-postman",
            action="store_true",
            help="Skip Postman configuration normalization.",
        )
        parser.add_argument(
            "--skip-n8n",
            action="store_true",
            help="Skip n8n workflow normalization.",
        )

    def handle(self, *args, **options) -> None:
        write_changes: bool = bool(options.get("write"))
        skip_postman: bool = bool(options.get("skip_postman"))
        skip_n8n: bool = bool(options.get("skip_n8n"))

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Normalizing media JSON for Postman configurations and n8n workflows"
            )
        )
        if not write_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Running in dry-run mode (no files will be modified). "
                    "Use --write to persist normalized JSON."
                )
            )

        if not skip_postman:
            self._normalize_postman(write_changes)
        else:
            self.stdout.write(self.style.NOTICE("Skipping Postman normalization."))

        if not skip_n8n:
            self._normalize_n8n(write_changes)
        else:
            self.stdout.write(self.style.NOTICE("Skipping n8n normalization."))

        self.stdout.write(self.style.SUCCESS("Postman/n8n normalization run completed."))

    # ------------------------------------------------------------------ #
    # Postman normalization
    # ------------------------------------------------------------------ #

    def _normalize_postman(self, write_changes: bool) -> None:
        postman_dir: Path = get_postman_dir()
        if not postman_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Postman directory does not exist: {postman_dir}")
            )
            return

        # We treat configuration JSONs as primary normalization target.
        config_dir = postman_dir / "configurations"
        if not config_dir.exists():
            self.stdout.write(
                self.style.NOTICE(
                    f"No Postman configurations directory found at {config_dir}, skipping."
                )
            )
            return

        json_files: List[Path] = list(config_dir.glob("*.json"))
        self.stdout.write(
            self.style.NOTICE(
                f"[postman] Found {len(json_files)} configuration JSON files to check."
            )
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
                normalized = validate_postman_configuration_data(data)

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
                        f"[postman] Failed to normalize {fp}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"[postman] Normalized {normalized_count} files "
                f"({error_count} errors, {'written' if write_changes else 'dry-run'})."
            )
        )

    # ------------------------------------------------------------------ #
    # n8n normalization (lightweight structural check)
    # ------------------------------------------------------------------ #

    def _normalize_n8n(self, write_changes: bool) -> None:
        """
        Perform a lightweight structural sanity-check over n8n workflow JSON.

        We intentionally avoid enforcing a strict schema here to prevent
        accidentally breaking existing workflows. Instead, we:

        - Ensure files are valid JSON objects
        - Optionally add a ``workflow_id`` field if missing (derived from filename)
        """
        n8n_dir: Path = get_n8n_dir()
        if not n8n_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"n8n directory does not exist: {n8n_dir}")
            )
            return

        json_files: List[Path] = list(n8n_dir.rglob("*.json"))
        self.stdout.write(
            self.style.NOTICE(
                f"[n8n] Found {len(json_files)} workflow JSON files to check."
            )
        )

        updated_count = 0
        error_count = 0
        parse_error_count = 0

        for fp in json_files:
            try:
                raw = fp.read_text(encoding="utf-8")
                if not raw.strip():
                    continue

                import json

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as parse_exc:
                    parse_error_count += 1
                    error_count += 1
                    self.stderr.write(
                        self.style.ERROR(
                            f"[n8n] Invalid JSON in {fp}: {parse_exc.msg} "
                            f"(line {parse_exc.lineno}, col {parse_exc.colno})"
                        )
                    )
                    continue

                if not isinstance(data, dict):
                    # Normalize non-dict payloads into a wrapper
                    data = {"workflow": data}

                # Ensure a stable workflow_id field derived from filename if missing
                if "workflow_id" not in data:
                    data["workflow_id"] = fp.stem

                if write_changes:
                    fp.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                updated_count += 1
            except Exception as exc:  # pragma: no cover - safety net
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(f"[n8n] Failed to normalize {fp}: {exc}")
                )

        if parse_error_count:
            self.stdout.write(
                self.style.WARNING(
                    f"[n8n] {parse_error_count} file(s) had JSON parse errors and were skipped."
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"[n8n] Updated {updated_count} files "
                f"({error_count} errors, {'written' if write_changes else 'dry-run'})."
            )
        )

