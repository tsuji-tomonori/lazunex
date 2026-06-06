#!/usr/bin/env python3
"""Check router api_functions calls do not discard meaningful return values."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

SIDE_EFFECT_PREFIXES = (
    "add_",
    "append_",
    "create_",
    "delete_",
    "insert_",
    "remove_",
    "save_",
    "update_",
)
MUST_USE_PREFIXES = (
    "apply_",
    "build_",
    "get_",
    "has_",
    "hash_",
    "is_",
    "merge_",
    "validate_",
    "verify_",
)
READ_ONLY_PREFIXES = MUST_USE_PREFIXES
MUTATING_QUERY_METHOD_PREFIXES = ("insert_", "update_", "delete_")
MUTATING_INTEGRATION_METHOD_PREFIXES = (
    "add_",
    "create_",
    "delete_",
    "patch_",
    "put_",
    "remove_",
    "set_",
    "update_",
)


@dataclass(frozen=True, order=True)
class ApiRouterIgnoredReturnIssue:
    path: Path
    line: int
    function_name: str
    message: str

    def display(self) -> str:
        return f"{self.path}:{self.line}: {self.function_name}: {self.message}"


def check_api_router_ignored_returns(
    api_root: Path = Path("src/app/apis"),
) -> list[ApiRouterIgnoredReturnIssue]:
    issues: list[ApiRouterIgnoredReturnIssue] = []
    for router_path in sorted(api_root.glob("*/*/router.py")):
        functions_path = router_path.with_name("functions.py")
        return_annotations = _return_annotations(functions_path)
        tree = ast.parse(router_path.read_text(encoding="utf-8"), filename=str(router_path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Expr):
                continue
            call = _awaited_api_function_call(node.value)
            if call is None:
                continue
            function_name = _api_function_name(call)
            if function_name is None:
                continue
            if _can_ignore_return(function_name, return_annotations.get(function_name)):
                continue
            issues.append(
                ApiRouterIgnoredReturnIssue(
                    router_path,
                    node.lineno,
                    function_name,
                    "api_functions return value must be used or the function must be "
                    "side-effect-only",
                )
            )

    for functions_path in sorted(
        [*api_root.glob("*/*/functions.py"), *api_root.glob("projects/common.py")]
    ):
        issues.extend(_function_side_effect_issues(functions_path))
    return sorted(issues)


def _return_annotations(functions_path: Path) -> dict[str, str | None]:
    if not functions_path.exists():
        return {}
    tree = ast.parse(functions_path.read_text(encoding="utf-8"), filename=str(functions_path))
    annotations: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            annotations[node.name] = ast.unparse(node.returns) if node.returns is not None else None
    return annotations


def _awaited_api_function_call(node: ast.AST) -> ast.Call | None:
    if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
        return node.value
    return None


def _api_function_name(call: ast.Call) -> str | None:
    if not isinstance(call.func, ast.Attribute):
        return None
    if not isinstance(call.func.value, ast.Name) or call.func.value.id != "api_functions":
        return None
    return call.func.attr


def _can_ignore_return(function_name: str, return_annotation: str | None) -> bool:
    if return_annotation in {None, "None", "NoReturn"}:
        return True
    if function_name.startswith(SIDE_EFFECT_PREFIXES):
        return True
    return not function_name.startswith(MUST_USE_PREFIXES)


def _function_side_effect_issues(functions_path: Path) -> list[ApiRouterIgnoredReturnIssue]:
    tree = ast.parse(functions_path.read_text(encoding="utf-8"), filename=str(functions_path))
    issues: list[ApiRouterIgnoredReturnIssue] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.name.startswith(READ_ONLY_PREFIXES):
            continue
        for call in (child for child in ast.walk(node) if isinstance(child, ast.Call)):
            if _is_mutating_call(call):
                issues.append(
                    ApiRouterIgnoredReturnIssue(
                        functions_path,
                        call.lineno,
                        node.name,
                        "read/check/build function must not perform mutating side effects",
                    )
                )
    return issues


def _is_mutating_call(call: ast.Call) -> bool:
    if not isinstance(call.func, ast.Attribute):
        return False
    method_name = call.func.attr
    if isinstance(call.func.value, ast.Name) and call.func.value.id == "queries":
        return method_name.startswith(MUTATING_QUERY_METHOD_PREFIXES)
    return method_name.startswith(MUTATING_INTEGRATION_METHOD_PREFIXES)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check router api_functions return values are used and read/check functions "
            "do not mutate resources."
        )
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues = check_api_router_ignored_returns(args.api_root)
    if not issues:
        print("All router api_functions return values are handled.")
        return 0
    for issue in issues:
        print(issue.display())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
