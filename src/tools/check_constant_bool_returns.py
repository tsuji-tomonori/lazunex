from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class ConstantBoolReturnIssue:
    path: Path
    line: int
    function_name: str
    constant_value: bool


def _returns_bool(function: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    annotation = function.returns
    if isinstance(annotation, ast.Name):
        return annotation.id == "bool"
    if isinstance(annotation, ast.Constant):
        return annotation.value == "bool"
    return False


def _bool_return_values(function: ast.AsyncFunctionDef | ast.FunctionDef) -> tuple[set[bool], bool]:
    values: set[bool] = set()
    has_dynamic_return = False
    for node in ast.walk(function):
        if not isinstance(node, ast.Return):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool):
            values.add(node.value.value)
            continue
        if node.value is not None:
            has_dynamic_return = True
    return values, has_dynamic_return


def check_constant_bool_returns(path: Path) -> list[ConstantBoolReturnIssue]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    issues: list[ConstantBoolReturnIssue] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if not _returns_bool(node):
            continue
        values, has_dynamic_return = _bool_return_values(node)
        if has_dynamic_return or len(values) != 1:
            continue
        issues.append(
            ConstantBoolReturnIssue(
                path=path,
                line=node.lineno,
                function_name=node.name,
                constant_value=next(iter(values)),
            )
        )
    return issues


def check_constant_bool_return_roots(roots: list[Path]) -> list[ConstantBoolReturnIssue]:
    issues: list[ConstantBoolReturnIssue] = []
    for root in roots:
        paths = [root] if root.is_file() else sorted(root.glob("**/*.py"))
        for path in paths:
            issues.extend(check_constant_bool_returns(path))
    return sorted(issues)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find bool-annotated functions that only return one bool literal value."
    )
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("src"), Path("tests")])
    args = parser.parse_args()

    issues = check_constant_bool_return_roots(args.paths)
    if not issues:
        print("No constant bool return issues found.")
        return 0

    for issue in issues:
        value = "True" if issue.constant_value else "False"
        print(f"{issue.path}:{issue.line}: {issue.function_name} only returns {value}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
