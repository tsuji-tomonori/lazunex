from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class ExceptionRouterHandlerIssue:
    router_path: Path
    line: int
    function_name: str
    message: str


def _public_functions(tree: ast.AST) -> dict[str, ast.AsyncFunctionDef | ast.FunctionDef]:
    functions: dict[str, ast.AsyncFunctionDef | ast.FunctionDef] = {}
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        functions[node.name] = node
    return functions


def _called_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _contains_external_method_call(function: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            return True
    return False


def _exception_prone_function_names(functions_path: Path) -> set[str]:
    tree = ast.parse(functions_path.read_text(encoding="utf-8"))
    functions = _public_functions(tree)
    prone: set[str] = set()

    for name, function in functions.items():
        if any(isinstance(node, ast.Raise) for node in ast.walk(function)):
            prone.add(name)
            continue
        if _contains_external_method_call(function):
            prone.add(name)

    changed = True
    while changed:
        changed = False
        for name, function in functions.items():
            if name in prone:
                continue
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                called_name = _called_name(node)
                if called_name in prone:
                    prone.add(name)
                    changed = True
                    break
    return prone


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


def _is_inside_try(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    child = node
    while child in parents:
        parent = parents[child]
        if isinstance(parent, ast.Try) and any(
            _contains(statement, child) for statement in parent.body
        ):
            return True
        child = parent
    return False


def _contains(root: ast.AST, target: ast.AST) -> bool:
    return any(node is target for node in ast.walk(root))


def check_exception_router_handlers(
    api_root: Path = Path("src/app/apis"),
) -> list[ExceptionRouterHandlerIssue]:
    issues: list[ExceptionRouterHandlerIssue] = []
    for functions_path in sorted(api_root.glob("*/*/functions.py")):
        router_path = functions_path.with_name("router.py")
        if not router_path.exists():
            continue
        exception_prone_names = _exception_prone_function_names(functions_path)
        if not exception_prone_names:
            continue

        tree = ast.parse(router_path.read_text(encoding="utf-8"))
        parents = _parent_map(tree)
        reported: set[tuple[int, str]] = set()
        for node in ast.walk(tree):
            function_name = _called_api_function(node)
            if function_name not in exception_prone_names:
                continue
            if _is_inside_try(node, parents):
                continue
            key = (getattr(node, "lineno", 0), function_name)
            if key in reported:
                continue
            reported.add(key)
            issues.append(
                ExceptionRouterHandlerIssue(
                    router_path=router_path,
                    line=getattr(node, "lineno", 0),
                    function_name=function_name,
                    message="exception-prone function call must be inside a try block",
                )
            )
    return sorted(issues)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check router.py catches api_functions calls that may raise exceptions."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    args = parser.parse_args()

    issues = check_exception_router_handlers(args.api_root)
    if not issues:
        print("All exception-prone router function calls are inside try blocks.")
        return 0

    for issue in issues:
        print(f"{issue.router_path}:{issue.line}: {issue.function_name}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
