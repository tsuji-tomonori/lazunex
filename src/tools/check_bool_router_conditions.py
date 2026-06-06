from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class BoolRouterConditionIssue:
    router_path: Path
    line: int
    function_name: str
    message: str


def _returns_bool(function: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    annotation = function.returns
    if isinstance(annotation, ast.Name):
        return annotation.id == "bool"
    if isinstance(annotation, ast.Constant):
        return annotation.value == "bool"
    return False


def _bool_function_names(functions_path: Path) -> set[str]:
    tree = ast.parse(functions_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if _returns_bool(node):
            names.add(node.name)
    return names


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _called_api_function(node: ast.AST) -> str | None:
    if isinstance(node, ast.Await):
        node = node.value
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute):
        return None
    if not isinstance(node.func.value, ast.Name):
        return None
    if node.func.value.id != "api_functions":
        return None
    return node.func.attr


def _is_inside_if_test(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    child = node
    while child in parents:
        parent = parents[child]
        if isinstance(parent, ast.If):
            return parent.test is child or _contains(parent.test, child)
        child = parent
    return False


def _contains(root: ast.AST, target: ast.AST) -> bool:
    return any(node is target for node in ast.walk(root))


def check_bool_router_conditions(
    api_root: Path = Path("src/app/apis"),
) -> list[BoolRouterConditionIssue]:
    issues: list[BoolRouterConditionIssue] = []
    for functions_path in sorted(api_root.glob("*/*/functions.py")):
        router_path = functions_path.with_name("router.py")
        if not router_path.exists():
            continue
        bool_names = _bool_function_names(functions_path)
        if not bool_names:
            continue

        tree = ast.parse(router_path.read_text(encoding="utf-8"))
        parents = _parent_map(tree)
        reported: set[tuple[int, str]] = set()
        for node in ast.walk(tree):
            function_name = _called_api_function(node)
            if function_name not in bool_names:
                continue
            if _is_inside_if_test(node, parents):
                continue
            key = (getattr(node, "lineno", 0), function_name)
            if key in reported:
                continue
            reported.add(key)
            issues.append(
                BoolRouterConditionIssue(
                    router_path=router_path,
                    line=getattr(node, "lineno", 0),
                    function_name=function_name,
                    message="bool function call must be used in an if condition",
                )
            )
    return sorted(issues)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check router.py uses bool-returning api_functions calls in if conditions."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    args = parser.parse_args()

    issues = check_bool_router_conditions(args.api_root)
    if not issues:
        print("All router bool function calls are used in if conditions.")
        return 0

    for issue in issues:
        print(f"{issue.router_path}:{issue.line}: {issue.function_name}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
