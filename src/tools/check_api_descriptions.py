from __future__ import annotations

import argparse
import ast
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
PLACEHOLDER_TEXT = re.compile(
    r"(OpenAPIスキーマを説明します|[A-Za-z_][A-Za-z0-9_]*\s+の値を指定します。)"
)
ROUTER_METHODS = {"delete", "get", "patch", "post", "put"}


@dataclass(frozen=True, order=True)
class DescriptionIssue:
    path: Path
    line: int
    target: str
    message: str


def has_japanese_text(value: str | None) -> bool:
    return bool(value and JAPANESE_TEXT.search(value))


def is_placeholder_description(value: str | None) -> bool:
    return bool(value and PLACEHOLDER_TEXT.search(value))


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def keyword_value(call: ast.Call, name: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def is_field_call(node: ast.AST | None) -> TypeGuard[ast.Call]:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == "Field"
    return isinstance(node.func, ast.Attribute) and node.func.attr == "Field"


def field_name(node: ast.AnnAssign) -> str | None:
    if isinstance(node.target, ast.Name):
        return node.target.id
    return None


def is_str_enum_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "StrEnum":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "StrEnum":
            return True
    return False


def enum_members(node: ast.ClassDef) -> dict[str, str]:
    members: dict[str, str] = {}
    for statement in node.body:
        if not isinstance(statement, ast.Assign):
            continue
        value = literal_string(statement.value)
        if value is None:
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                members[target.id] = value
    return members


def enum_member_line_numbers(node: ast.ClassDef) -> dict[str, int]:
    lines: dict[str, int] = {}
    for statement in node.body:
        if not isinstance(statement, ast.Assign):
            continue
        if literal_string(statement.value) is None:
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                lines[target.id] = statement.lineno
    return lines


def enum_member_comment(source_lines: Sequence[str], line_number: int) -> str | None:
    if line_number <= 0 or line_number > len(source_lines):
        return None
    line = source_lines[line_number - 1]
    if "#" in line:
        return line.split("#", maxsplit=1)[1].strip()
    previous_index = line_number - 2
    if previous_index < 0:
        return None
    previous_line = source_lines[previous_index].strip()
    if previous_line.startswith("#"):
        return previous_line.removeprefix("#").strip()
    return None


def is_router_decorator(node: ast.AST) -> TypeGuard[ast.Call]:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in ROUTER_METHODS:
        return False
    return isinstance(node.func.value, ast.Name) and node.func.value.id == "router"


def router_decorators(
    tree: ast.AST,
) -> Iterable[tuple[ast.AsyncFunctionDef | ast.FunctionDef, ast.Call]]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if is_router_decorator(decorator):
                yield node, decorator


def check_router_file(path: Path) -> list[DescriptionIssue]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    issues: list[DescriptionIssue] = []

    for function, decorator in router_decorators(tree):
        for key in ("summary", "description"):
            value = literal_string(keyword_value(decorator, key))
            if value is None:
                issues.append(
                    DescriptionIssue(
                        path=path,
                        line=decorator.lineno,
                        target=f"{function.name}.{key}",
                        message=f"router decorator requires Japanese {key}",
                    )
                )
            elif not has_japanese_text(value):
                issues.append(
                    DescriptionIssue(
                        path=path,
                        line=decorator.lineno,
                        target=f"{function.name}.{key}",
                        message=f"router decorator {key} must contain Japanese text",
                    )
                )
    return issues


def check_schema_file(path: Path) -> list[DescriptionIssue]:
    source = path.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    tree = ast.parse(source, filename=str(path))
    issues: list[DescriptionIssue] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        docstring = ast.get_docstring(node)
        if docstring is None:
            issues.append(
                DescriptionIssue(
                    path=path,
                    line=node.lineno,
                    target=node.name,
                    message="schema model requires a Japanese docstring",
                )
            )
        elif not has_japanese_text(docstring):
            issues.append(
                DescriptionIssue(
                    path=path,
                    line=node.lineno,
                    target=node.name,
                    message="schema model docstring must contain Japanese text",
                )
            )
        elif is_placeholder_description(docstring):
            issues.append(
                DescriptionIssue(
                    path=path,
                    line=node.lineno,
                    target=node.name,
                    message="schema model docstring must describe the model purpose concretely",
                )
            )
        for statement in node.body:
            if not isinstance(statement, ast.AnnAssign):
                continue
            name = field_name(statement)
            if name is None:
                continue
            if not is_field_call(statement.value):
                issues.append(
                    DescriptionIssue(
                        path=path,
                        line=statement.lineno,
                        target=f"{node.name}.{name}",
                        message="schema field requires Field(description=...)",
                    )
                )
                continue

            description = literal_string(keyword_value(statement.value, "description"))
            if description is None:
                issues.append(
                    DescriptionIssue(
                        path=path,
                        line=statement.lineno,
                        target=f"{node.name}.{name}",
                        message="schema field requires a Japanese Field description",
                    )
                )
            elif not has_japanese_text(description):
                issues.append(
                    DescriptionIssue(
                        path=path,
                        line=statement.lineno,
                        target=f"{node.name}.{name}",
                        message="schema field description must contain Japanese text",
                    )
                )
            elif is_placeholder_description(description):
                issues.append(
                    DescriptionIssue(
                        path=path,
                        line=statement.lineno,
                        target=f"{node.name}.{name}",
                        message=(
                            "schema field description must describe the field purpose concretely"
                        ),
                    )
                )
        if is_str_enum_class(node):
            members = enum_members(node)
            member_lines = enum_member_line_numbers(node)
            for member_name in members:
                line = member_lines[member_name]
                description = enum_member_comment(source_lines, line)
                if description is None:
                    issues.append(
                        DescriptionIssue(
                            path=path,
                            line=line,
                            target=f"{node.name}.{member_name}",
                            message="enum value requires a Japanese comment",
                        )
                    )
                elif not has_japanese_text(description):
                    issues.append(
                        DescriptionIssue(
                            path=path,
                            line=line,
                            target=f"{node.name}.{member_name}",
                            message="enum value comment must contain Japanese text",
                        )
                    )
                elif is_placeholder_description(description):
                    issues.append(
                        DescriptionIssue(
                            path=path,
                            line=line,
                            target=f"{node.name}.{member_name}",
                            message="enum value comment must describe the value meaning concretely",
                        )
                    )
    return issues


def api_description_files(api_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in api_dir.rglob("*.py")
        if path.name in {"common.py", "router.py", "schemas.py"} and "__pycache__" not in path.parts
    )


def check_api_descriptions(api_dir: Path) -> list[DescriptionIssue]:
    issues: list[DescriptionIssue] = []
    for path in api_description_files(api_dir):
        if path.name == "router.py":
            issues.extend(check_router_file(path))
        elif path.name in {"common.py", "schemas.py"}:
            issues.extend(check_schema_file(path))
    return sorted(issues)


def render_issues(issues: Sequence[DescriptionIssue]) -> str:
    if not issues:
        return "# API description check\n\nAll router and schema descriptions are present."

    lines = ["# API description check", "", "Description issues found:"]
    for issue in issues:
        lines.append(f"- {issue.path}:{issue.line} `{issue.target}`: {issue.message}")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Japanese descriptions on API routers/schemas."
    )
    parser.add_argument("--api-dir", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--no-fail-on-issue", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    issues = check_api_descriptions(args.api_dir)
    print(render_issues(issues))
    if issues and not args.no_fail_on_issue:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
