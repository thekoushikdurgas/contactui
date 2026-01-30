"""
Top-level media normalization command.

This command provides a single entry point:

    python manage.py normalize_media_files [--write]

It orchestrates the more granular normalization commands:

    - normalize_media_pages_endpoints
    - normalize_media_relationships
    - normalize_media_postman_n8n

and additionally scans remaining JSON files under:

    - media/project
    - media root (excluding the known subdirectories)

to ensure they are at least valid JSON. By default it runs in dry‑run mode and
only reports issues; use ``--write`` to allow the subcommands to persist
normalized JSON for pages, endpoints, relationships, Postman, and n8n.
"""

import json
from pathlib import Path
from typing import List

from django.core.management import BaseCommand, call_command

from apps.documentation.utils.paths import (
    get_media_root,
    get_project_dir,
)


class Command(BaseCommand):
    help = (
        "Normalize all media JSON: pages, endpoints, relationships, Postman, n8n, "
        "and validate remaining project/root JSON files."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help=(
                "Write normalized JSON back to media files where supported "
                "(pages, endpoints, relationships, postman, n8n). "
                "By default runs in dry‑run mode."
            ),
        )

    def handle(self, *args, **options) -> None:
        write_changes: bool = bool(options.get("write"))

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Running full media normalization (pages, endpoints, relationships, postman, n8n, project/root JSON)"
            )
        )
        if not write_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Running in dry‑run mode; use --write to persist normalized JSON "
                    "for supported resources."
                )
            )

        # 1) Delegate to existing per-domain commands
        self.stdout.write(self.style.NOTICE("Normalizing pages and endpoints..."))
        call_command("normalize_media_pages_endpoints", write=write_changes)

        self.stdout.write(self.style.NOTICE("Normalizing relationships..."))
        call_command("normalize_media_relationships", write=write_changes)

        self.stdout.write(self.style.NOTICE("Normalizing Postman configurations and n8n workflows..."))
        call_command("normalize_media_postman_n8n", write=write_changes)

        # 2) Generic JSON validity scan for project and remaining media files
        self._scan_project_json()
        self._scan_root_media_json()

        self.stdout.write(self.style.SUCCESS("normalize_media_files run completed."))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _scan_project_json(self) -> None:
        """Scan media/project for JSON files and verify they are well‑formed."""
        project_dir = get_project_dir()
        if not project_dir.exists():
            self.stdout.write(
                self.style.NOTICE(f"Project directory does not exist: {project_dir}")
            )
            return

        json_files: List[Path] = list(project_dir.glob("*.json"))
        self.stdout.write(
            self.style.NOTICE(
                f"[project] Scanning {len(json_files)} JSON files for basic validity."
            )
        )

        error_count = 0
        for fp in json_files:
            try:
                raw = fp.read_text(encoding="utf-8")
                if not raw.strip():
                    continue
                json.loads(raw)
            except Exception as exc:  # pragma: no cover - safety net
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(f"[project] Invalid JSON in {fp}: {exc}")
                )

        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS("[project] All scanned JSON files are valid.")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"[project] Completed with {error_count} JSON parse error(s)."
                )
            )

    def _scan_root_media_json(self) -> None:
        """
        Scan media root for JSON files that are not under the main resource
        subdirectories (pages, endpoints, relationships/relationship, postman, n8n, project)
        and verify that they are at least well‑formed JSON.
        """
        media_root = get_media_root()
        if not media_root.exists():
            self.stdout.write(
                self.style.NOTICE(f"Media root does not exist: {media_root}")
            )
            return

        known_dirs = {
            "pages",
            "endpoints",
            "relationships",
            "relationship",  # singular, used in some setups
            "postman",
            "n8n",
            "project",
        }

        json_files: List[Path] = []
        for fp in media_root.rglob("*.json"):
            try:
                rel_parts = fp.relative_to(media_root).parts
            except ValueError:
                # Outside media root; skip
                continue
            # Skip files that live inside known subtrees; those are already handled
            if rel_parts and rel_parts[0] in known_dirs:
                continue
            json_files.append(fp)

        self.stdout.write(
            self.style.NOTICE(
                f"[media-root] Scanning {len(json_files)} additional JSON file(s) for basic validity."
            )
        )

        error_count = 0
        for fp in json_files:
            try:
                raw = fp.read_text(encoding="utf-8")
                if not raw.strip():
                    continue
                json.loads(raw)
            except Exception as exc:  # pragma: no cover - safety net
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(f"[media-root] Invalid JSON in {fp}: {exc}")
                )

        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "[media-root] All additional scanned JSON files are valid."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"[media-root] Completed with {error_count} JSON parse error(s)."
                )
            )

