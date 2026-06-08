#!/usr/bin/env python3
"""Fail fast check for Lazunex operational logging policy.

This is a thin CI-friendly wrapper around the static analysis contained in
``generate_api_message_catalog.py``.  Use this when you want a small command that
only validates logger usage and does not touch generated Markdown.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.generate_api_message_catalog import (
    DEFAULT_ALLOWED_DIRECT_LOGGER_FILES,
    DEFAULT_API_ROOT,
    DEFAULT_SCAN_ROOT,
    build_api_catalogs,
    find_direct_logger_violations,
    validate_catalogs,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Lazunex operational logger usage.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--api-root", type=Path, default=DEFAULT_API_ROOT, help="API root relative to --root."
    )
    parser.add_argument(
        "--scan-root",
        type=Path,
        default=DEFAULT_SCAN_ROOT,
        help="Python source root relative to --root.",
    )
    parser.add_argument(
        "--allowed-direct-logger-file",
        action="append",
        default=list(DEFAULT_ALLOWED_DIRECT_LOGGER_FILES),
        help="Repo-relative file allowed to call stdlib logging directly. Can be repeated.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also validate WARNING/ERROR/CRITICAL catalog-required fields.",
    )
    parser.add_argument(
        "--fail-on-undocumented-emits",
        action="store_true",
        help="Require every wrapper message_id to exist in message_catalog.py.",
    )
    parser.add_argument(
        "--fail-on-missing-catalog-id",
        action="store_true",
        help="Require every wrapper call to contain a literal catalog_id.",
    )
    parser.add_argument(
        "--require-api-wrapper-calls",
        action="store_true",
        help="Require each API directory to contain at least one wrapper call.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    api_root = args.api_root if args.api_root.is_absolute() else root / args.api_root
    scan_root = args.scan_root if args.scan_root.is_absolute() else root / args.scan_root

    errors: list[str] = []
    direct_logger_violations = find_direct_logger_violations(
        root=root,
        scan_root=scan_root,
        allowed_files=args.allowed_direct_logger_file,
    )
    errors.extend(violation.display(root) for violation in direct_logger_violations)

    catalogs = build_api_catalogs(root=root, api_root=api_root, include_http_defaults=True)
    if not catalogs:
        errors.append(f"no API router.py found under {api_root}")
    else:
        errors.extend(
            validate_catalogs(
                catalogs,
                strict=args.strict,
                fail_on_undocumented_emits=args.fail_on_undocumented_emits,
                fail_on_missing_message_id=True,
                fail_on_missing_catalog_id=args.fail_on_missing_catalog_id,
                fail_on_level_mismatch=True,
                require_api_wrapper_calls=args.require_api_wrapper_calls,
            )
        )

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print("[OK] operational logger policy is satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
