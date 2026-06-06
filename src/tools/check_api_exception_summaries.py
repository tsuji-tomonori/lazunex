from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class ApiExceptionSummaryIssue:
    path: Path
    line: int
    message: str


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _keyword_value(call: ast.Call, name: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _is_api_function_error(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == "ApiFunctionError"


def _check_raise(path: Path, node: ast.Raise) -> list[ApiExceptionSummaryIssue]:
    issues: list[ApiExceptionSummaryIssue] = []
    raised = node.exc
    if isinstance(raised, ast.Call) and _is_api_function_error(raised):
        if len(raised.args) < 2:
            issues.append(
                ApiExceptionSummaryIssue(
                    path,
                    node.lineno,
                    "ApiFunctionError must receive status_code and detail arguments",
                )
            )
        summary = _literal_string(_keyword_value(raised, "summary"))
        if summary is None or not summary.strip():
            issues.append(
                ApiExceptionSummaryIssue(
                    path,
                    node.lineno,
                    "ApiFunctionError must receive a non-empty literal summary keyword",
                )
            )
        return issues

    if isinstance(raised, ast.Call):
        name = raised.func.id if isinstance(raised.func, ast.Name) else None
        attr = raised.func.attr if isinstance(raised.func, ast.Attribute) else None
        if name in {"ValueError", "RuntimeError"} or attr == "HTTPException":
            issues.append(
                ApiExceptionSummaryIssue(
                    path,
                    node.lineno,
                    "API functions must raise ApiFunctionError with summary",
                )
            )
    return issues


def _check_external_error_summaries(path: Path, tree: ast.AST) -> list[ApiExceptionSummaryIssue]:
    issues: list[ApiExceptionSummaryIssue] = []
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name == "ExternalApiError":
            continue
        if not node.name.endswith("Error"):
            continue
        inherits_external = any(
            isinstance(base, ast.Name)
            and base.id in {"ExternalApiError", "ExternalApiUnavailableError"}
            for base in node.bases
        )
        if not inherits_external:
            continue
        summary = None
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            if any(
                isinstance(target, ast.Name) and target.id == "summary"
                for target in statement.targets
            ):
                summary = _literal_string(statement.value)
        if summary is None or not summary.strip():
            issues.append(
                ApiExceptionSummaryIssue(
                    path,
                    node.lineno,
                    f"{node.name} must define a non-empty summary class attribute",
                )
            )
    return issues


def check_api_exception_summaries(
    api_root: Path = Path("src/app/apis"),
    integrations_root: Path = Path("src/app/integrations"),
) -> list[ApiExceptionSummaryIssue]:
    issues: list[ApiExceptionSummaryIssue] = []
    for path in sorted([*api_root.glob("*/*/functions.py"), *api_root.glob("projects/common.py")]):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                issues.extend(_check_raise(path, node))

    common_errors = integrations_root / "common_errors.py"
    if common_errors.exists():
        tree = ast.parse(common_errors.read_text(encoding="utf-8"), filename=str(common_errors))
        issues.extend(_check_external_error_summaries(common_errors, tree))
    return sorted(issues)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check API function and external errors provide natural-language summaries."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--integrations-root", type=Path, default=Path("src/app/integrations"))
    args = parser.parse_args()

    issues = check_api_exception_summaries(args.api_root, args.integrations_root)
    if not issues:
        print("All API exceptions provide summaries.")
        return 0

    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
