#!/usr/bin/env python3
"""Check API sequence functions use the right exception style."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

RUNTIME_DEPENDENCY_NAMES = {
    "session",
    "api_gateway_control",
    "identity_admin",
    "secret_values",
}
RUNTIME_DEPENDENCY_SUFFIXES = (
    "_client",
    "_control",
    "_admin",
    "_values",
)


@dataclass(frozen=True, order=True)
class ApiFunctionExceptionPolicyIssue:
    path: Path
    line: int
    function_name: str
    message: str

    def display(self) -> str:
        return f"{self.path}:{self.line}: {self.function_name}: {self.message}"


def check_api_function_exception_policy(
    api_root: Path = Path("src/app/apis"),
) -> list[ApiFunctionExceptionPolicyIssue]:
    issues: list[ApiFunctionExceptionPolicyIssue] = []
    for path in _target_paths(api_root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = _parent_map(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                issues.extend(_check_function(path, node, parents))
    return sorted(issues)


def _target_paths(api_root: Path) -> list[Path]:
    return sorted([*api_root.glob("*/*/functions.py"), *api_root.glob("projects/common.py")])


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _check_function(
    path: Path,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[ast.AST, ast.AST],
) -> list[ApiFunctionExceptionPolicyIssue]:
    issues: list[ApiFunctionExceptionPolicyIssue] = []
    missing_dependency_calls = [
        call for call in ast.walk(function) if isinstance(call, ast.Call) and _is_missing_call(call)
    ]
    optional_dependencies = _optional_runtime_dependencies(function)

    if _uses_runtime_resource(function, optional_dependencies) and not missing_dependency_calls:
        issues.append(
            ApiFunctionExceptionPolicyIssue(
                path,
                function.lineno,
                function.name,
                "runtime dependency function must call raise_missing_runtime_dependency",
            )
        )

    for call in missing_dependency_calls:
        issues.extend(_check_missing_dependency_call(path, function, call, parents))

    for raise_node in (node for node in ast.walk(function) if isinstance(node, ast.Raise)):
        issues.extend(_check_raise(path, function, raise_node))
    return issues


def _optional_runtime_dependencies(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    parameters = list(function.args.posonlyargs) + list(function.args.args)
    defaults = list(function.args.defaults)
    dependencies: set[str] = set()
    default_offset = len(parameters) - len(defaults)
    for index, parameter in enumerate(parameters):
        if index < default_offset:
            continue
        default = defaults[index - default_offset]
        if not _is_none(default):
            continue
        if _is_runtime_dependency_name(parameter.arg) or _annotation_mentions_runtime_dependency(
            parameter.annotation
        ):
            dependencies.add(parameter.arg)
    return dependencies


def _is_runtime_dependency_name(name: str) -> bool:
    return name in RUNTIME_DEPENDENCY_NAMES or name.endswith(RUNTIME_DEPENDENCY_SUFFIXES)


def _annotation_mentions_runtime_dependency(annotation: ast.AST | None) -> bool:
    if annotation is None:
        return False
    text = ast.unparse(annotation)
    return any(
        marker in text
        for marker in (
            "AsyncSession",
            "Port",
            "Client",
            "Admin",
        )
    )


def _uses_runtime_resource(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    optional_dependencies: set[str],
) -> bool:
    if not optional_dependencies:
        return False
    for node in ast.walk(function):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "queries":
                return True
            if isinstance(node.value, ast.Name) and node.value.id in optional_dependencies:
                return True
    return False


def _check_missing_dependency_call(
    path: Path,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
    parents: dict[ast.AST, ast.AST],
) -> list[ApiFunctionExceptionPolicyIssue]:
    issues: list[ApiFunctionExceptionPolicyIssue] = []
    if not isinstance(parents.get(call), ast.Return):
        issues.append(
            ApiFunctionExceptionPolicyIssue(
                path,
                call.lineno,
                function.name,
                "raise_missing_runtime_dependency must be returned directly",
            )
        )
    function_name = _literal_string(call.args[0]) if call.args else None
    if function_name != function.name:
        issues.append(
            ApiFunctionExceptionPolicyIssue(
                path,
                call.lineno,
                function.name,
                "raise_missing_runtime_dependency argument must match the function name",
            )
        )
    return issues


def _check_raise(
    path: Path,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    raise_node: ast.Raise,
) -> list[ApiFunctionExceptionPolicyIssue]:
    issues: list[ApiFunctionExceptionPolicyIssue] = []
    raised = raise_node.exc
    if not isinstance(raised, ast.Call):
        return issues
    if _is_http_exception_call(raised):
        issues.append(
            ApiFunctionExceptionPolicyIssue(
                path,
                raise_node.lineno,
                function.name,
                "API functions must not raise HTTPException directly",
            )
        )
    if _is_api_function_error_call(raised) and _looks_like_runtime_dependency_error(raised):
        issues.append(
            ApiFunctionExceptionPolicyIssue(
                path,
                raise_node.lineno,
                function.name,
                "runtime dependency errors must use raise_missing_runtime_dependency",
            )
        )
    return issues


def _is_missing_call(call: ast.Call) -> bool:
    return _call_name(call) == "raise_missing_runtime_dependency"


def _is_http_exception_call(call: ast.Call) -> bool:
    return _call_name(call) == "HTTPException"


def _is_api_function_error_call(call: ast.Call) -> bool:
    return _call_name(call) == "ApiFunctionError"


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _looks_like_runtime_dependency_error(call: ast.Call) -> bool:
    values: list[str] = []
    for arg in call.args:
        if value := _literal_string(arg):
            values.append(value)
    for keyword in call.keywords:
        if value := _literal_string(keyword.value):
            values.append(value)
    return any("runtime dependenc" in value or "requires runtime" in value for value in values)


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_none(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check API functions use ApiFunctionError for business errors and "
            "raise_missing_runtime_dependency for missing runtime dependencies."
        )
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues = check_api_function_exception_policy(args.api_root)
    if not issues:
        print("All API function exception policies are valid.")
        return 0
    for issue in issues:
        print(issue.display())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
