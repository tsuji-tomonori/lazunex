#!/usr/bin/env python3
"""Check router error logs are asserted through sample-based API calls."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.generate_api_message_catalog import MessageDefinition, build_api_catalogs

DEFAULT_ROOT = Path(".")
DEFAULT_API_ROOT = Path("src/app/apis")
DEFAULT_TEST_ROOT = Path("tests/app/apis")
ASSERT_HELPER = "assert_router_error_log"


@dataclass(frozen=True)
class RouterLoggingTestIssue:
    path: Path
    message: str

    def display(self) -> str:
        return f"{self.path}: {self.message}"


def check_api_router_logging_tests(
    root: Path = DEFAULT_ROOT,
    api_root: Path | None = None,
    test_root: Path | None = None,
) -> list[RouterLoggingTestIssue]:
    api_root = api_root or root / DEFAULT_API_ROOT
    test_root = test_root or root / DEFAULT_TEST_ROOT
    issues: list[RouterLoggingTestIssue] = []
    issues.extend(_shared_helper_issues(test_root / "helpers.py"))
    for api_dir in sorted(api_root.glob("*/*")):
        router_path = api_dir / "router.py"
        if not router_path.exists():
            continue
        api_ref = api_dir.relative_to(api_root).as_posix()
        contract = _router_error_contract(root, api_root, api_ref)
        if contract is None:
            issues.append(
                RouterLoggingTestIssue(router_path, "router error log contract is missing")
            )
            continue
        test_path = test_root / api_dir.relative_to(api_root) / "test_router.py"
        if not test_path.exists():
            issues.append(
                RouterLoggingTestIssue(test_path, "sample-based router test file is missing")
            )
            continue
        issues.extend(_test_file_issues(test_path, contract))
    return issues


def _shared_helper_issues(helper_path: Path) -> list[RouterLoggingTestIssue]:
    if not helper_path.exists():
        return [RouterLoggingTestIssue(helper_path, "router logging test helper is missing")]
    text = helper_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(helper_path))
    issues: list[RouterLoggingTestIssue] = []
    if "_expected_router_error_catalog" not in text:
        issues.append(
            RouterLoggingTestIssue(
                helper_path,
                "router logging helper must compare logs with generated message catalog values",
            )
        )
    if not _compares_message_catalog_to_expected(tree):
        issues.append(
            RouterLoggingTestIssue(
                helper_path,
                "router logging helper must assert event['messageCatalog'] == expected catalog",
            )
        )
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and _is_truthy_event_assert(node.test):
            issues.append(
                RouterLoggingTestIssue(
                    helper_path,
                    "router logging helper must not use truthy-only event[...] asserts",
                )
            )
    return issues


def _compares_message_catalog_to_expected(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        compare = node.test
        if not isinstance(compare, ast.Compare) or len(compare.ops) != 1:
            continue
        if not isinstance(compare.ops[0], ast.Eq) or len(compare.comparators) != 1:
            continue
        if _is_event_subscript(compare.left, "messageCatalog"):
            return True
    return False


def _is_truthy_event_assert(node: ast.AST) -> bool:
    return _is_event_subscript(node, None)


def _is_event_subscript(node: ast.AST, key: str | None) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if not isinstance(node.value, ast.Name) or node.value.id != "event":
        return False
    if key is None:
        return True
    slice_node = node.slice
    return isinstance(slice_node, ast.Constant) and slice_node.value == key


def _router_error_contract(
    root: Path, api_root: Path, api_ref: str
) -> MessageDefinition | None:
    catalogs = build_api_catalogs(root=root, api_root=api_root, include_http_defaults=True)
    for catalog in catalogs:
        current_ref = f"{catalog.meta.domain}/{catalog.meta.api}"
        if current_ref != api_ref:
            continue
        for message in catalog.messages:
            if message.message_id.endswith(".router_error"):
                return message
        return None
    return None


def _test_file_issues(
    test_path: Path, contract: MessageDefinition
) -> list[RouterLoggingTestIssue]:
    text = test_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(test_path))
    issues: list[RouterLoggingTestIssue] = []
    if ASSERT_HELPER not in text:
        issues.append(
            RouterLoggingTestIssue(
                test_path,
                f"{ASSERT_HELPER} fixture must be called from the sample-based API test",
            )
        )
    if "_STATUS_SAMPLES" not in text:
        issues.append(
            RouterLoggingTestIssue(
                test_path,
                "router logging test must pass this API's *_STATUS_SAMPLES",
            )
        )
    for required_text, message in {
        "capsys": "router logging test must capture stdio with capsys",
        "monkeypatch": "router logging test must force a router-handled error",
        "path_template": "router logging test must call the API path built from the sample",
        "patch_target": "router logging test must declare the patched function target",
        "success_status": "router logging test must choose the sample success request",
    }.items():
        if required_text not in text:
            issues.append(RouterLoggingTestIssue(test_path, message))
    if not _has_helper_call_for_contract(tree, contract):
        issues.append(
            RouterLoggingTestIssue(
                test_path,
                "router logging test must assert "
                f"message_id={contract.message_id!r} and catalog_id={contract.catalog_id!r}",
            )
        )
    if test_path.name != "test_router.py":
        issues.append(
            RouterLoggingTestIssue(
                test_path, "router logging assertions must live in test_router.py"
            )
        )
    return issues


def _has_helper_call_for_contract(tree: ast.Module, contract: MessageDefinition) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != ASSERT_HELPER:
            continue
        values: dict[str, object] = {}
        for keyword in node.keywords:
            if keyword.arg not in {"message_id", "catalog_id"}:
                continue
            if isinstance(keyword.value, ast.Constant):
                values[keyword.arg] = keyword.value.value
        if (
            values.get("message_id") == contract.message_id
            and values.get("catalog_id") == contract.catalog_id
        ):
            return True
    return False


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check API router error logs are asserted by calling sample requests and "
            "validating stdio JSON logs."
        )
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--api-root", type=Path, default=DEFAULT_API_ROOT)
    parser.add_argument("--test-root", type=Path, default=DEFAULT_TEST_ROOT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    api_root = args.api_root if args.api_root.is_absolute() else root / args.api_root
    test_root = args.test_root if args.test_root.is_absolute() else root / args.test_root
    issues = check_api_router_logging_tests(root=root, api_root=api_root, test_root=test_root)
    if issues:
        for issue in issues:
            print(issue.display())
        return 1
    print("All API router error logs are asserted through sample-based API calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
