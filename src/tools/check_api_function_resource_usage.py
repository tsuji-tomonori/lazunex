from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

RESOURCE_FREE_MARKER = "@resource-free"
RESOURCE_FREE_EXACT_NAMES = frozenset({"get_caller_identity"})
RESOURCE_FREE_PREFIXES = ("is_", "has_", "validate_", "build_", "merge_")
RESOURCE_PARAMETER_NAMES = frozenset(
    {
        "api_gateway",
        "api_gateway_control",
        "identity_admin",
        "secret_values",
        "secrets_manager",
    }
)


@dataclass(frozen=True, order=True)
class FunctionResourceUsageIssue:
    path: Path
    line: int
    function_name: str
    message: str


def api_function_files(api_root: Path) -> list[Path]:
    return sorted(api_root.glob("*/*/functions.py"))


def public_functions(tree: ast.AST) -> Iterable[ast.AsyncFunctionDef | ast.FunctionDef]:
    for statement in getattr(tree, "body", []):
        if not isinstance(statement, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if statement.name.startswith("_"):
            continue
        yield statement


def function_source_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def has_resource_free_marker(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    source_lines: Sequence[str],
) -> bool:
    docstring = ast.get_docstring(function) or ""
    if RESOURCE_FREE_MARKER in docstring:
        return True
    start_index = max(function.lineno - 3, 0)
    end_index = min(function.lineno + 1, len(source_lines))
    return any(RESOURCE_FREE_MARKER in line for line in source_lines[start_index:end_index])


def is_name_exempt(function_name: str) -> bool:
    return function_name in RESOURCE_FREE_EXACT_NAMES or function_name.startswith(
        RESOURCE_FREE_PREFIXES
    )


def parameter_names(function: ast.AsyncFunctionDef | ast.FunctionDef) -> set[str]:
    return {argument.arg for argument in function.args.args}


def annotation_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return annotation_name(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = annotation_name(node.left)
        right = annotation_name(node.right)
        return left or right
    return None


def resource_parameter_names(function: ast.AsyncFunctionDef | ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for argument in function.args.args:
        annotation = annotation_name(argument.annotation)
        if argument.arg in RESOURCE_PARAMETER_NAMES:
            names.add(argument.arg)
        if annotation is not None and annotation.endswith(("Port", "Client")):
            names.add(argument.arg)
    return names


def call_base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return call_base_name(node.value)
    return None


def calls_queries(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Attribute) and call_base_name(node.func.value) == "queries"


def calls_resource_parameter(node: ast.Call, resource_names: set[str]) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    return call_base_name(node.func.value) in resource_names


def uses_resource(function: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    resource_names = resource_parameter_names(function)
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if calls_queries(node) or calls_resource_parameter(node, resource_names):
            return True
    return False


def check_api_function_file(path: Path) -> list[FunctionResourceUsageIssue]:
    source_lines = function_source_lines(path)
    tree = ast.parse("\n".join(source_lines), filename=str(path))
    issues: list[FunctionResourceUsageIssue] = []
    for function in public_functions(tree):
        if is_name_exempt(function.name):
            continue
        if has_resource_free_marker(function, source_lines):
            continue
        if uses_resource(function):
            continue
        issues.append(
            FunctionResourceUsageIssue(
                path=path,
                line=function.lineno,
                function_name=function.name,
                message=(
                    "non-validation public function must use queries/integration resources "
                    f"or declare {RESOURCE_FREE_MARKER}"
                ),
            )
        )
    return issues


def check_api_function_resource_usage(api_root: Path) -> list[FunctionResourceUsageIssue]:
    issues: list[FunctionResourceUsageIssue] = []
    for path in api_function_files(api_root):
        issues.extend(check_api_function_file(path))
    return sorted(issues)


def render_issues(issues: Sequence[FunctionResourceUsageIssue]) -> str:
    return "\n".join(
        f"{issue.path}:{issue.line}: {issue.function_name}: {issue.message}" for issue in issues
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check API functions.py public functions use DB/integration resources."
    )
    parser.add_argument(
        "--api-root",
        type=Path,
        default=Path("src/app/apis"),
        help="API root containing {domain}/{api}/functions.py files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    issues = check_api_function_resource_usage(args.api_root)
    if issues:
        print(render_issues(issues))
        return 1
    print("All non-validation API functions use DB/integration resources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
