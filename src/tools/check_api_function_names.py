from __future__ import annotations

import argparse
import ast
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

RULE_FILENAMES = {
    "actions": "sequence_function_actions.json",
    "targets": "sequence_function_targets.json",
    "predicates": "sequence_function_predicates.json",
    "conditions": "sequence_function_conditions.json",
}


@dataclass(frozen=True, order=True)
class FunctionNameIssue:
    path: Path
    line: int
    target: str
    message: str


def load_rule_names(path: Path) -> set[str]:
    raw_object: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_object, dict):
        raise ValueError(f"{path} must contain a JSON object")
    raw = cast("dict[str, object]", raw_object)
    entries_object = raw.get("entries")
    if not isinstance(entries_object, list):
        raise ValueError(f"{path} must contain entries list")
    entries = cast("list[object]", entries_object)

    names: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: entries[{index}] must be an object")
        entry_dict = cast("dict[str, object]", entry)
        name = entry_dict.get("name")
        description = entry_dict.get("description")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{path}: entries[{index}].name must be a non-empty string")
        if not isinstance(description, str) or not description:
            raise ValueError(f"{path}: entries[{index}].description must be a non-empty string")
        if name in names:
            raise ValueError(f"{path}: duplicated name {name!r}")
        names.add(name)
    return names


def load_rules(rule_dir: Path) -> dict[str, set[str]]:
    return {key: load_rule_names(rule_dir / filename) for key, filename in RULE_FILENAMES.items()}


def api_function_files(api_root: Path) -> list[Path]:
    return sorted(api_root.glob("*/*/functions.py"))


def public_functions(tree: ast.AST) -> Iterable[ast.AsyncFunctionDef | ast.FunctionDef]:
    for statement in getattr(tree, "body", []):
        if not isinstance(statement, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if statement.name.startswith("_"):
            continue
        yield statement


def check_function_name(
    path: Path,
    function: ast.AsyncFunctionDef | ast.FunctionDef,
    rules: dict[str, set[str]],
) -> list[FunctionNameIssue]:
    issues: list[FunctionNameIssue] = []
    name = function.name
    head, separator, tail = name.partition("_")
    if not separator or not tail:
        issues.append(
            FunctionNameIssue(
                path=path,
                line=function.lineno,
                target=name,
                message="function name must be {action}_{target} or {is|has}_{condition}",
            )
        )
        return issues

    if head in rules["predicates"]:
        if tail not in rules["conditions"]:
            issues.append(
                FunctionNameIssue(
                    path=path,
                    line=function.lineno,
                    target=name,
                    message=(
                        f"condition {tail!r} is not defined in sequence_function_conditions.json"
                    ),
                )
            )
    elif head in rules["actions"]:
        if tail not in rules["targets"]:
            issues.append(
                FunctionNameIssue(
                    path=path,
                    line=function.lineno,
                    target=name,
                    message=f"target {tail!r} is not defined in sequence_function_targets.json",
                )
            )
    else:
        issues.append(
            FunctionNameIssue(
                path=path,
                line=function.lineno,
                target=name,
                message=f"action or predicate {head!r} is not defined",
            )
        )

    if ast.get_docstring(function) is None:
        issues.append(
            FunctionNameIssue(
                path=path,
                line=function.lineno,
                target=name,
                message="public sequence function requires a docstring",
            )
        )
    return issues


def check_api_function_file(path: Path, rules: dict[str, set[str]]) -> list[FunctionNameIssue]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    issues: list[FunctionNameIssue] = []
    for function in public_functions(tree):
        issues.extend(check_function_name(path, function, rules))
    return issues


def check_api_function_names(api_root: Path, rule_dir: Path) -> list[FunctionNameIssue]:
    rules = load_rules(rule_dir)
    issues: list[FunctionNameIssue] = []
    for path in api_function_files(api_root):
        issues.extend(check_api_function_file(path, rules))
    return sorted(issues)


def render_issues(issues: Sequence[FunctionNameIssue]) -> str:
    return "\n".join(
        f"{issue.path}:{issue.line}: {issue.target}: {issue.message}" for issue in issues
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check API functions.py names against sequence function vocabularies."
    )
    parser.add_argument(
        "--api-root",
        type=Path,
        default=Path("src/app/apis"),
        help="API root containing {domain}/{api}/functions.py files.",
    )
    parser.add_argument(
        "--rule-dir",
        type=Path,
        default=Path("docs/rule/docs"),
        help="Directory containing sequence function vocabulary JSON files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    issues = check_api_function_names(args.api_root, args.rule_dir)
    if issues:
        print(render_issues(issues))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
