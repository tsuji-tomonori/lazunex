from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path

from tools.generate_api_sequences import (
    endpoint_exception_error_returns,
    endpoint_function,
    endpoint_sequence_steps,
    function_metadata,
)

HTTP_STATUS_CODE_PATTERN = re.compile(r"HTTP_(?P<code>[0-9]{3})_(?P<reason>[A-Z0-9_]+)")
HTTP_STATUS_NAMES = {
    400: "HTTP_400_BAD_REQUEST",
    401: "HTTP_401_UNAUTHORIZED",
    403: "HTTP_403_FORBIDDEN",
    404: "HTTP_404_NOT_FOUND",
    409: "HTTP_409_CONFLICT",
    422: "HTTP_422_UNPROCESSABLE_CONTENT",
    429: "HTTP_429_TOO_MANY_REQUESTS",
    500: "HTTP_500_INTERNAL_SERVER_ERROR",
    502: "HTTP_502_BAD_GATEWAY",
    503: "HTTP_503_SERVICE_UNAVAILABLE",
}
EXTERNAL_API_ERROR_STATUSES = {
    502,
    503,
}
ROUTER_ERROR_HANDLER_STATUSES = {
    500,
}


@dataclass(frozen=True, order=True)
class RouterErrorResponseReturnIssue:
    path: Path
    line: int
    status_name: str
    message: str


def _status_attr_code(node: ast.AST) -> tuple[int, str] | None:
    if not isinstance(node, ast.Attribute):
        return None
    if not isinstance(node.value, ast.Name):
        return None
    if node.value.id != "status":
        return None
    match = HTTP_STATUS_CODE_PATTERN.fullmatch(node.attr)
    if match is None:
        return None
    return int(match.group("code")), node.attr


def _declared_error_response_statuses(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
) -> dict[int, str]:
    statuses: dict[int, str] = {}
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        responses_keyword = next(
            (keyword for keyword in decorator.keywords if keyword.arg == "responses"),
            None,
        )
        if responses_keyword is None:
            continue
        for node in ast.walk(responses_keyword.value):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "error_responses":
                continue
            statuses[500] = HTTP_STATUS_NAMES[500]
            for arg in node.args:
                status = _status_attr_code(arg)
                if status is not None:
                    statuses[status[0]] = status[1]
    return statuses


def _returned_error_response_statuses(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
) -> list[tuple[int, int, str]]:
    statuses: list[tuple[int, int, str]] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "api_error_response":
            continue
        if not node.args:
            continue
        status = _status_attr_code(node.args[0])
        if status is not None:
            statuses.append((node.lineno, status[0], status[1]))
    return statuses


def _returns_error_response_for_router_error(node: ast.stmt) -> bool:
    if not isinstance(node, ast.Return):
        return False
    call = node.value
    if not isinstance(call, ast.Call):
        return False
    return isinstance(call.func, ast.Name) and call.func.id == "error_response_for_router_error"


def _excepts_router_handled_exceptions(node: ast.ExceptHandler) -> bool:
    exception_type = node.type
    if isinstance(exception_type, ast.Name):
        return exception_type.id == "ROUTER_HANDLED_EXCEPTIONS"
    if isinstance(exception_type, ast.Tuple):
        return any(
            isinstance(element, ast.Name) and element.id == "ROUTER_HANDLED_EXCEPTIONS"
            for element in exception_type.elts
        )
    return False


def _returned_router_error_handler_statuses(
    function: ast.AsyncFunctionDef | ast.FunctionDef,
) -> list[tuple[int, int, str]]:
    statuses: list[tuple[int, int, str]] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _excepts_router_handled_exceptions(node):
            continue
        if not any(_returns_error_response_for_router_error(statement) for statement in node.body):
            continue
        statuses.extend(
            (node.lineno, status_code, HTTP_STATUS_NAMES[status_code])
            for status_code in sorted(ROUTER_ERROR_HANDLER_STATUSES)
        )
    return statuses


def _returned_exception_statuses(
    path: Path, router_function: ast.AsyncFunctionDef | ast.FunctionDef
) -> list[tuple[int, int, str]]:
    functions_path = path.with_name("functions.py")
    if not functions_path.exists():
        return []
    metadata = function_metadata(functions_path)
    steps = endpoint_sequence_steps(router_function, metadata)
    return [
        (
            router_function.lineno,
            error.status_code,
            HTTP_STATUS_NAMES.get(error.status_code, f"HTTP_{error.status_code}"),
        )
        for error in endpoint_exception_error_returns(steps, metadata)
    ]


def _returned_external_error_statuses(
    path: Path, router_function: ast.AsyncFunctionDef | ast.FunctionDef
) -> list[tuple[int, int, str]]:
    functions_path = path.with_name("functions.py")
    if not functions_path.exists():
        return []
    metadata = function_metadata(functions_path)
    steps = endpoint_sequence_steps(router_function, metadata)
    if not any(step.integration_resources for step in steps):
        return []
    return [
        (
            router_function.lineno,
            status_code,
            HTTP_STATUS_NAMES.get(status_code, f"HTTP_{status_code}"),
        )
        for status_code in sorted(EXTERNAL_API_ERROR_STATUSES)
    ]


def check_router_error_response_returns(
    api_root: Path = Path("src/app/apis"),
) -> list[RouterErrorResponseReturnIssue]:
    issues: list[RouterErrorResponseReturnIssue] = []
    for path in sorted(api_root.glob("*/*/router.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        try:
            route_functions = [endpoint_function(tree)]
        except ValueError:
            route_functions = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
            ]
        for node in route_functions:
            declared = _declared_error_response_statuses(node)
            if not declared:
                continue
            returned_statuses = [
                *_returned_error_response_statuses(node),
                *_returned_router_error_handler_statuses(node),
                *_returned_exception_statuses(path, node),
                *_returned_external_error_statuses(path, node),
            ]
            returned_status_codes = {status_code for _line, status_code, _name in returned_statuses}
            for line, returned_status, returned_name in returned_statuses:
                if returned_status in declared:
                    continue
                issues.append(
                    RouterErrorResponseReturnIssue(
                        path=path,
                        line=line,
                        status_name=returned_name,
                        message="error response status is not declared in error_responses",
                    )
                )
            for declared_status, declared_name in declared.items():
                if declared_status in returned_status_codes:
                    continue
                issues.append(
                    RouterErrorResponseReturnIssue(
                        path=path,
                        line=node.lineno,
                        status_name=declared_name,
                        message=(
                            "error_responses declares a status not returned by "
                            "router implementation"
                        ),
                    )
                )
    return sorted(issues)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check router error response returns exactly match declared error_responses."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    args = parser.parse_args()

    issues = check_router_error_response_returns(args.api_root)
    if not issues:
        print("All router error response returns exactly match declared error_responses.")
        return 0

    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.status_name}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
