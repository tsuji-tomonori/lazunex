from __future__ import annotations

import argparse
import ast
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

CASE_ID_PATTERN = re.compile(r"^### (?P<case_id>TC[0-9]+)$")
HTTP_EXPECTATION_PATTERN = re.compile(
    r"HTTP (?P<status>[0-9]{3}) error response: (?P<detail>[^|;<]+)"
)
SUCCESS_EXPECTATION_PATTERN = re.compile(r"HTTP (?P<status>[0-9]{3}) success response")
LOG_EXPECTATION_PATTERN = re.compile(
    r"log message_id: (?P<message_id>[^|;<]+)(?:; |<br>)log summary: (?P<summary>[^|]+)"
)


@dataclass(frozen=True, order=True)
class UnitTestCaseExpectation:
    case_id: str
    expected_status: int | None
    expected_detail: str | None
    expected_log_message_id: str | None = None
    expected_log_summary: str | None = None
    router_error: bool = False
    expected_exception_type: str | None = None
    expected_outcome: str | None = None


@dataclass(frozen=True, order=True)
class RouterUnitTestFactorIssue:
    api: str
    test_path: Path
    spec_path: Path
    message: str


def api_name_from_spec_path(spec_path: Path, spec_root: Path) -> str:
    relative = spec_path.relative_to(spec_root)
    if len(relative.parts) < 3 or relative.name != "unit-test_gen.md":
        raise ValueError(
            f"unit-test spec must be under docs/spec/40.apis/{{domain}}/{{api}}: {spec_path}"
        )
    return relative.parts[-2]


def parse_unit_test_cases(
    spec_path: Path, success_status: int | None = None
) -> list[UnitTestCaseExpectation]:
    cases: list[UnitTestCaseExpectation] = []
    current_case_id: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_case_id, current_lines
        if current_case_id is None:
            return
        text = "\n".join(current_lines)
        expected_exception_type = router_error_exception_type(text)
        log_match = LOG_EXPECTATION_PATTERN.search(text)
        expected_log_message_id = (
            log_match.group("message_id").strip().strip("`") if log_match is not None else None
        )
        expected_log_summary = log_match.group("summary").strip() if log_match is not None else None
        http_match = HTTP_EXPECTATION_PATTERN.search(text)
        if http_match is not None:
            cases.append(
                UnitTestCaseExpectation(
                    case_id=current_case_id,
                    expected_status=int(http_match.group("status")),
                    expected_detail=http_match.group("detail").strip(),
                    expected_log_message_id=expected_log_message_id,
                    expected_log_summary=expected_log_summary,
                    router_error=expected_exception_type is not None,
                    expected_exception_type=expected_exception_type,
                )
            )
        elif "router error response" in text:
            expected_status, expected_detail = router_error_expected_response(
                expected_exception_type
            )
            cases.append(
                UnitTestCaseExpectation(
                    case_id=current_case_id,
                    expected_status=expected_status,
                    expected_detail=expected_detail,
                    expected_log_message_id=expected_log_message_id,
                    expected_log_summary=expected_log_summary,
                    router_error=True,
                    expected_exception_type=expected_exception_type,
                )
            )
        else:
            success_match = SUCCESS_EXPECTATION_PATTERN.search(text)
            parsed_success_status = (
                int(success_match.group("status")) if success_match is not None else success_status
            )
            cases.append(
                UnitTestCaseExpectation(
                    case_id=current_case_id,
                    expected_status=parsed_success_status,
                    expected_detail=None,
                    expected_outcome="success",
                )
            )
        current_case_id = None
        current_lines = []

    for line in spec_path.read_text(encoding="utf-8").splitlines():
        match = CASE_ID_PATTERN.match(line)
        if match is not None:
            flush()
            current_case_id = match.group("case_id")
            continue
        if current_case_id is not None:
            current_lines.append(line)
    flush()
    return cases


def router_error_exception_type(text: str) -> str | None:
    for exception_type in ("ApiFunctionError", "ExternalApiError", "HTTPException"):
        if f"| {exception_type} |" in text:
            return exception_type
    return None


def router_error_expected_response(exception_type: str | None) -> tuple[int, str]:
    if exception_type == "ExternalApiError":
        return 502, "external service request failed"
    if exception_type == "HTTPException":
        return 400, "forced http exception"
    return 500, "forced router error"


def expected_test_path(spec_path: Path, spec_root: Path, test_root: Path) -> Path:
    relative_parent = spec_path.relative_to(spec_root).parent
    return test_root / relative_parent / "test_router.py"


def expected_function_name(api: str, case_id: str) -> str:
    return f"test_{case_id.lower()}_{api}_router_matches_unit_test_gen"


def function_defs(tree: ast.Module) -> dict[str, ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_tc")
    }


def function_literals(node: ast.AST) -> set[object]:
    values: set[object] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant):
            values.add(child.value)
    return values


def calls_direct_client_method(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Await) or not isinstance(child.value, ast.Call):
            continue
        func = child.value.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr not in {"get", "post", "put", "patch", "delete", "request"}:
            continue
        if _is_router_db_harness_client(func.value):
            return True
    return False


def _is_router_db_harness_client(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "client"
        and isinstance(node.value, ast.Name)
        and node.value.id == "router_db_harness"
    )


def assert_expected_status(node: ast.AST, expected_status: int | None) -> bool:
    if expected_status is None:
        return False
    for assertion in _assert_nodes(node):
        if not isinstance(assertion.test, ast.Compare):
            continue
        if _contains_status_code(assertion.test.left) and _compare_has_literal(
            assertion.test.comparators, expected_status
        ):
            return True
    return False


def assert_expected_detail(node: ast.AST, expected_detail: str) -> bool:
    for assertion in _assert_nodes(node):
        if not isinstance(assertion.test, ast.Compare):
            continue
        if _compare_has_literal(assertion.test.comparators, expected_detail):
            return True
    return False


def finds_log_event_from_literal(node: ast.AST, expected: str) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if not isinstance(child.func, ast.Name) or child.func.id != "find_log_event":
            continue
        if len(child.args) != 1:
            continue
        arg = child.args[0]
        if isinstance(arg, ast.Constant) and arg.value == expected:
            return True
    return False


def assert_log_event_field_literal(node: ast.AST, field: str, expected: str) -> bool:
    for assertion in _assert_nodes(node):
        if not isinstance(assertion.test, ast.Compare):
            continue
        if not _is_actual_log_event_field(assertion.test.left, field):
            continue
        for comparator in assertion.test.comparators:
            if isinstance(comparator, ast.Constant) and comparator.value == expected:
                return True
    return False


def has_forbidden_expected_log_variable(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in {
            "expected_log_message_id",
            "expected_log_summary",
        }:
            return True
    return False


def references_name(node: ast.AST, expected: str) -> bool:
    return any(isinstance(child, ast.Name) and child.id == expected for child in ast.walk(node))


def _is_actual_log_event_field(node: ast.AST, field: str) -> bool:
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "actual_log_event"
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == field
    )


def _assert_nodes(node: ast.AST) -> Iterable[ast.Assert]:
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            yield child


def _contains_status_code(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and child.attr == "status_code":
            return True
    return False


def _compare_has_literal(comparators: list[ast.expr], expected: object) -> bool:
    return any(
        isinstance(comparator, ast.Constant) and comparator.value == expected
        for comparator in comparators
    )


def validate_case_function(
    api: str,
    expected: UnitTestCaseExpectation,
    node: ast.AsyncFunctionDef,
) -> list[str]:
    messages: list[str] = []
    literals = function_literals(node)
    if not calls_direct_client_method(node):
        messages.append(f"{expected.case_id} must call router_db_harness.client API directly")
    if not assert_expected_status(node, expected.expected_status):
        messages.append(f"{expected.case_id} must assert status_code == {expected.expected_status}")
    if expected.expected_detail is not None:
        if expected.expected_detail not in literals:
            messages.append(
                f"{expected.case_id} must include expected detail {expected.expected_detail!r}"
            )
        if not assert_expected_detail(node, expected.expected_detail):
            messages.append(
                f"{expected.case_id} must assert expected detail {expected.expected_detail!r}"
            )
    if (
        expected.router_error
        and expected.expected_exception_type is not None
        and not references_name(node, expected.expected_exception_type)
    ):
        messages.append(f"{expected.case_id} must raise {expected.expected_exception_type}")
    if expected.expected_log_message_id is not None:
        if has_forbidden_expected_log_variable(node):
            messages.append(f"{expected.case_id} must compare log expectations directly")
        if expected.expected_log_message_id not in literals:
            messages.append(
                f"{expected.case_id} must include expected log message_id "
                f"{expected.expected_log_message_id!r}"
            )
        if not finds_log_event_from_literal(node, expected.expected_log_message_id):
            messages.append(f"{expected.case_id} must read actual log event from stdout")
        if not assert_log_event_field_literal(node, "messageId", expected.expected_log_message_id):
            messages.append(
                f"{expected.case_id} must assert actual log message_id "
                f"{expected.expected_log_message_id!r}"
            )
    if expected.expected_log_summary is not None:
        if expected.expected_log_summary not in literals:
            messages.append(
                f"{expected.case_id} must include expected log summary "
                f"{expected.expected_log_summary!r}"
            )
        if not assert_log_event_field_literal(node, "summary", expected.expected_log_summary):
            messages.append(
                f"{expected.case_id} must assert actual log summary "
                f"{expected.expected_log_summary!r}"
            )
    if expected.expected_outcome == "success" and expected.expected_status is None:
        messages.append(f"{expected.case_id} success status cannot be inferred")
    if node.name != expected_function_name(api, expected.case_id):
        messages.append(
            f"{expected.case_id} function name must be "
            f"{expected_function_name(api, expected.case_id)!r}"
        )
    return messages


def infer_success_status(functions: dict[str, ast.AsyncFunctionDef]) -> int | None:
    statuses: set[int] = set()
    for node in functions.values():
        for assertion in _assert_nodes(node):
            if not isinstance(assertion.test, ast.Compare):
                continue
            if not _contains_status_code(assertion.test.left):
                continue
            for comparator in assertion.test.comparators:
                if (
                    isinstance(comparator, ast.Constant)
                    and isinstance(comparator.value, int)
                    and 200 <= comparator.value < 300
                ):
                    statuses.add(comparator.value)
    if len(statuses) == 1:
        return next(iter(statuses))
    if 201 in statuses:
        return 201
    if 200 in statuses:
        return 200
    return None


def check_api_router_unit_test_factors(
    spec_root: Path,
    test_root: Path,
) -> list[RouterUnitTestFactorIssue]:
    issues: list[RouterUnitTestFactorIssue] = []
    for spec_path in sorted(spec_root.glob("*/*/unit-test_gen.md")):
        api = api_name_from_spec_path(spec_path, spec_root)
        test_path = expected_test_path(spec_path, spec_root, test_root)
        if not test_path.exists():
            issues.append(
                RouterUnitTestFactorIssue(api, test_path, spec_path, "router test file is missing")
            )
            continue
        tree = ast.parse(test_path.read_text(encoding="utf-8"), filename=test_path.as_posix())
        functions = function_defs(tree)
        expected_cases = parse_unit_test_cases(
            spec_path,
            success_status=infer_success_status(functions),
        )
        for expected in expected_cases:
            function_name = expected_function_name(api, expected.case_id)
            node = functions.get(function_name)
            if node is None:
                issues.append(
                    RouterUnitTestFactorIssue(
                        api,
                        test_path,
                        spec_path,
                        f"{expected.case_id} function {function_name!r} is missing",
                    )
                )
                continue
            for message in validate_case_function(api, expected, node):
                issues.append(RouterUnitTestFactorIssue(api, test_path, spec_path, message))
    return sorted(issues)


def render_issues(issues: Sequence[RouterUnitTestFactorIssue]) -> str:
    return "\n".join(
        f"{issue.test_path}: {issue.api}: {issue.message} (spec: {issue.spec_path})"
        for issue in issues
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check router tests execute unit-test_gen.md cases with direct API calls."
    )
    parser.add_argument("--spec-root", type=Path, default=Path("docs/spec/40.apis"))
    parser.add_argument("--test-root", type=Path, default=Path("tests/app/apis"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    issues = check_api_router_unit_test_factors(args.spec_root, args.test_root)
    if issues:
        print(render_issues(issues))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
