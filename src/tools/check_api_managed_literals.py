from __future__ import annotations

import argparse
import ast
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

MANAGED_LITERALS = frozenset(
    {
        "hub-admin",
        "PUBLIC_PKCE",
        "PUBLIC",
        "CONFIDENTIAL_CLIENT_CREDENTIALS",
        "CONFIDENTIAL",
        "CALLBACK",
        "LOGOUT",
    }
)

ALLOWED_LITERAL_PATHS = {
    "hub-admin": frozenset({Path("common.py")}),
    "PUBLIC_PKCE": frozenset(
        {
            Path("api_access_requests/common.py"),
            Path("projects/common.py"),
        }
    ),
    "PUBLIC": frozenset({Path("projects/common.py")}),
    "CONFIDENTIAL_CLIENT_CREDENTIALS": frozenset({Path("projects/common.py")}),
    "CONFIDENTIAL": frozenset({Path("projects/common.py")}),
    "CALLBACK": frozenset({Path("projects/common.py")}),
    "LOGOUT": frozenset({Path("projects/common.py")}),
}


@dataclass(frozen=True, order=True)
class ManagedLiteralIssue:
    path: Path
    line: int
    literal: str
    message: str


def python_files(api_root: Path) -> list[Path]:
    return sorted(path for path in api_root.rglob("*.py") if "__pycache__" not in path.parts)


def body_without_docstring(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        yield from body[1:]
        return
    yield from body


class ManagedLiteralVisitor(ast.NodeVisitor):
    def __init__(self, path: Path, api_root: Path) -> None:
        self.path = path
        self.relative_path = path.relative_to(api_root)
        self.issues: list[ManagedLiteralIssue] = []

    def visit_Module(self, node: ast.Module) -> None:
        for statement in body_without_docstring(node.body):
            self.visit(statement)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for statement in body_without_docstring(node.body):
            self.visit(statement)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_body(node.body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_body(node.body)

    def _visit_function_body(self, body: list[ast.stmt]) -> None:
        for statement in body_without_docstring(body):
            self.visit(statement)

    def visit_Constant(self, node: ast.Constant) -> None:
        if not isinstance(node.value, str):
            return
        literal = node.value
        if literal not in MANAGED_LITERALS:
            return
        if self.relative_path in ALLOWED_LITERAL_PATHS.get(literal, frozenset()):
            return
        self.issues.append(
            ManagedLiteralIssue(
                path=self.path,
                line=node.lineno,
                literal=literal,
                message="managed literal must be referenced through a shared constant or enum",
            )
        )


def check_api_managed_literal_file(path: Path, api_root: Path) -> list[ManagedLiteralIssue]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = ManagedLiteralVisitor(path, api_root)
    visitor.visit(tree)
    return visitor.issues


def check_api_managed_literals(api_root: Path) -> list[ManagedLiteralIssue]:
    issues: list[ManagedLiteralIssue] = []
    for path in python_files(api_root):
        issues.extend(check_api_managed_literal_file(path, api_root))
    return sorted(issues)


def check_api_managed_literal_roots(api_roots: Sequence[Path]) -> list[ManagedLiteralIssue]:
    issues: list[ManagedLiteralIssue] = []
    for api_root in api_roots:
        issues.extend(check_api_managed_literals(api_root))
    return sorted(issues)


def render_issues(issues: Sequence[ManagedLiteralIssue]) -> str:
    return "\n".join(
        f"{issue.path}:{issue.line}: {issue.literal}: {issue.message}" for issue in issues
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check API Python code for managed domain literals."
    )
    parser.add_argument(
        "--api-root",
        type=Path,
        action="append",
        dest="api_roots",
        help="API Python root to scan.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    api_roots = args.api_roots or [Path("src/app/apis"), Path("tests/app/apis")]
    issues = check_api_managed_literal_roots(api_roots)
    if issues:
        print(render_issues(issues))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
