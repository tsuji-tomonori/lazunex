from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

MUTATION_OPS = frozenset({"C", "U", "D"})


@dataclass(frozen=True, order=True)
class RouterTestAssertIssue:
    api: str
    test_path: Path
    message: str


def read_crud_csv(path: Path) -> dict[str, dict[str, str]]:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    return {
        str(row["api"]): {
            table: value
            for table, value in row.items()
            if table != "api" and isinstance(value, str) and value
        }
        for row in rows
    }


def api_router_dirs(api_root: Path) -> dict[str, Path]:
    return {
        router_path.parent.name: router_path.parent
        for router_path in sorted(api_root.glob("*/*/router.py"))
    }


def test_path_for_api(api: str, api_root: Path, test_root: Path) -> Path:
    api_dir = api_router_dirs(api_root)[api]
    return test_root / api_dir.relative_to(api_root) / "test_router.py"


def mutation_tables(table_ops: dict[str, str]) -> set[str]:
    return {
        table
        for table, ops in table_ops.items()
        if any(operation in MUTATION_OPS for operation in ops)
    }


def router_has_body(router_path: Path) -> bool:
    return "Body" in router_path.read_text(encoding="utf-8")


def check_test_content(
    api: str,
    test_path: Path,
    router_path: Path,
    table_ops: dict[str, str],
) -> list[RouterTestAssertIssue]:
    text = test_path.read_text(encoding="utf-8")
    issues: list[RouterTestAssertIssue] = []

    if "_RESPONSE_SAMPLE" not in text or "assert body == expected" not in text:
        issues.append(
            RouterTestAssertIssue(
                api=api,
                test_path=test_path,
                message="router test must build expected output from *_RESPONSE_SAMPLE",
            )
        )
    if router_has_body(router_path) and "_REQUEST_SAMPLE" not in text:
        issues.append(
            RouterTestAssertIssue(
                api=api,
                test_path=test_path,
                message="body router test must send input from *_REQUEST_SAMPLE",
            )
        )

    tables = mutation_tables(table_ops)
    if not tables and not any(token in text for token in ("router_count_rows", "router_fetch_one")):
        issues.append(
            RouterTestAssertIssue(
                api=api,
                test_path=test_path,
                message="router test must assert DB state for read-only API",
            )
        )
    for table in sorted(tables):
        if table not in text:
            issues.append(
                RouterTestAssertIssue(
                    api=api,
                    test_path=test_path,
                    message=f"router test must assert CRUD table `{table}`",
                )
            )
    return issues


def check_api_router_test_asserts(
    api_root: Path,
    test_root: Path,
    crud_csv: Path,
) -> list[RouterTestAssertIssue]:
    crud = read_crud_csv(crud_csv)
    router_dirs = api_router_dirs(api_root)
    issues: list[RouterTestAssertIssue] = []

    for api, api_dir in sorted(router_dirs.items()):
        test_path = test_root / api_dir.relative_to(api_root) / "test_router.py"
        if not test_path.exists():
            issues.append(
                RouterTestAssertIssue(
                    api=api,
                    test_path=test_path,
                    message="router test file is missing",
                )
            )
            continue
        issues.extend(
            check_test_content(
                api,
                test_path,
                api_dir / "router.py",
                crud.get(api, {}),
            )
        )
    return sorted(issues)


def render_issues(issues: Sequence[RouterTestAssertIssue]) -> str:
    return "\n".join(f"{issue.test_path}: {issue.api}: {issue.message}" for issue in issues)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check router tests use samples and assert CRUD-based DB state."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--test-root", type=Path, default=Path("tests/app/apis"))
    parser.add_argument("--crud-csv", type=Path, default=Path("docs/spec/30.crud/db_crud.gen.csv"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    issues = check_api_router_test_asserts(args.api_root, args.test_root, args.crud_csv)
    if issues:
        print(render_issues(issues))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
