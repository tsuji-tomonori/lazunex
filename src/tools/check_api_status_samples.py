from __future__ import annotations

import argparse
import ast
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError

from app.apis.base import ApiStatusSample
from app.apis.responses import ErrorResponse
from app.main import create_app


@dataclass(frozen=True, order=True)
class ApiStatusSampleIssue:
    operation_id: str
    status_code: str
    message: str


def _module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").parts[path.parts.index("src") + 1 :])


def _route_operation_id(router_path: Path) -> str | None:
    tree = ast.parse(router_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            for keyword in decorator.keywords:
                if (
                    keyword.arg == "operation_id"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    return keyword.value.value
    return None


def _status_samples_by_operation(api_root: Path) -> dict[str, dict[int, ApiStatusSample]]:
    samples_by_operation: dict[str, dict[int, ApiStatusSample]] = {}
    for samples_path in sorted(api_root.glob("*/*/samples.py")):
        router_path = samples_path.with_name("router.py")
        if not router_path.exists():
            continue
        operation_id = _route_operation_id(router_path)
        if operation_id is None:
            continue
        module = importlib.import_module(_module_name(samples_path))
        status_sample_attrs: list[object] = [
            value
            for name, value in vars(module).items()
            if name.endswith("_STATUS_SAMPLES") and isinstance(value, dict)
        ]
        if len(status_sample_attrs) == 1:
            samples_by_operation[operation_id] = cast(
                dict[int, ApiStatusSample],
                status_sample_attrs[0],
            )
    return samples_by_operation


def _error_resource_models_by_operation(api_root: Path) -> dict[str, type[BaseModel]]:
    models_by_operation: dict[str, type[BaseModel]] = {}
    for router_path in sorted(api_root.glob("*/*/router.py")):
        operation_id = _route_operation_id(router_path)
        if operation_id is None:
            continue
        schemas_path = router_path.with_name("schemas.py")
        if not schemas_path.exists():
            continue
        module = importlib.import_module(_module_name(schemas_path))
        model = getattr(module, "ErrorResource", None)
        if isinstance(model, type) and issubclass(model, BaseModel):
            models_by_operation[operation_id] = model
    return models_by_operation


def _routes_by_operation() -> dict[str, APIRoute]:
    routes: dict[str, APIRoute] = {}
    for route in create_app().routes:
        if isinstance(route, APIRoute) and route.operation_id is not None:
            routes[route.operation_id] = route
    return routes


def _openapi_operations() -> dict[str, dict[str, Any]]:
    schema = create_app().openapi()
    operations: dict[str, dict[str, Any]] = {}
    for path_item in schema["paths"].values():
        for operation in path_item.values():
            operation_id = operation.get("operationId")
            if isinstance(operation_id, str):
                operations[operation_id] = cast(dict[str, Any], operation)
    return operations


def check_api_status_samples(api_root: Path = Path("src/app/apis")) -> list[ApiStatusSampleIssue]:
    issues: list[ApiStatusSampleIssue] = []
    samples_by_operation = _status_samples_by_operation(api_root)
    error_resource_models = _error_resource_models_by_operation(api_root)
    routes_by_operation = _routes_by_operation()
    operations = _openapi_operations()

    for operation_id, operation in sorted(operations.items()):
        if operation_id not in routes_by_operation or operation_id == "health":
            continue
        samples = samples_by_operation.get(operation_id)
        if samples is None:
            issues.append(ApiStatusSampleIssue(operation_id, "*", "status samples are missing"))
            continue

        declared_statuses = set(operation["responses"])
        sample_statuses = {str(status_code) for status_code in samples}
        for status_code in sorted(declared_statuses - sample_statuses):
            issues.append(
                ApiStatusSampleIssue(operation_id, status_code, "status sample is missing")
            )
        for status_code in sorted(sample_statuses - declared_statuses):
            issues.append(
                ApiStatusSampleIssue(operation_id, status_code, "status sample is not declared")
            )

        has_request_body = "requestBody" in operation
        route = routes_by_operation[operation_id]
        success_model = route.response_model
        for status_code, sample in sorted(samples.items()):
            status_name = str(status_code)
            if "request" not in sample:
                issues.append(
                    ApiStatusSampleIssue(operation_id, status_name, "request sample is missing")
                )
            if "response" not in sample:
                issues.append(
                    ApiStatusSampleIssue(operation_id, status_name, "response sample is missing")
                )
                continue
            if has_request_body and "body" not in sample["request"]:
                issues.append(
                    ApiStatusSampleIssue(
                        operation_id,
                        status_name,
                        "request body sample is missing",
                    )
                )
            if not has_request_body and "body" in sample["request"]:
                issues.append(
                    ApiStatusSampleIssue(
                        operation_id,
                        status_name,
                        "unexpected request body sample",
                    )
                )
            _check_request_parameters(
                issues,
                operation_id,
                status_name,
                operation,
                sample["request"],
            )

            _check_response_schema(
                issues,
                operation_id,
                status_name,
                status_code,
                sample["response"],
                success_model,
            )
            _check_error_resource_schema(
                issues,
                operation_id,
                status_name,
                status_code,
                sample["response"],
                error_resource_models.get(operation_id),
            )
            _check_openapi_example(issues, operation_id, status_name, operation, sample["response"])

    return sorted(issues)


def _check_request_parameters(
    issues: list[ApiStatusSampleIssue],
    operation_id: str,
    status_name: str,
    operation: dict[str, Any],
    request_sample: dict[str, Any],
) -> None:
    for location in ("path", "query", "headers"):
        sample_location = request_sample.get(location)
        if sample_location is None:
            sample_keys: set[str] = set()
        elif isinstance(sample_location, dict):
            sample_location_dict = cast(dict[object, object], sample_location)
            sample_keys = {str(key) for key in sample_location_dict}
        else:
            issues.append(
                ApiStatusSampleIssue(
                    operation_id,
                    status_name,
                    f"{location} request sample must be an object",
                )
            )
            continue

        parameter_location = "header" if location == "headers" else location
        parameters = _parameters_by_location(operation, parameter_location)
        parameter_keys = set(parameters)
        for key in sorted(sample_keys - parameter_keys):
            issues.append(
                ApiStatusSampleIssue(
                    operation_id,
                    status_name,
                    f"unknown {location} request sample parameter: {key}",
                )
            )
        for key, required in sorted(parameters.items()):
            if required and key not in sample_keys:
                issues.append(
                    ApiStatusSampleIssue(
                        operation_id,
                        status_name,
                        f"required {location} request sample parameter is missing: {key}",
                    )
                )


def _parameters_by_location(operation: dict[str, Any], location: str) -> dict[str, bool]:
    parameters: dict[str, bool] = {}
    raw_parameters = operation.get("parameters")
    if not isinstance(raw_parameters, list):
        return parameters
    raw_parameter_list = cast(list[object], raw_parameters)
    for raw_parameter in raw_parameter_list:
        if not isinstance(raw_parameter, dict):
            continue
        parameter = cast(dict[str, Any], raw_parameter)
        if parameter.get("in") != location:
            continue
        name = parameter.get("name")
        if isinstance(name, str):
            parameters[name] = bool(parameter.get("required"))
    return parameters


def _check_response_schema(
    issues: list[ApiStatusSampleIssue],
    operation_id: str,
    status_name: str,
    status_code: int,
    response_sample: dict[str, Any],
    success_model: Any,
) -> None:
    model: type[BaseModel] | None
    if status_code < 400:
        model = success_model if isinstance(success_model, type) else None
    else:
        model = ErrorResponse
    if model is None:
        return
    try:
        model.model_validate(response_sample)
    except ValidationError as error:
        issues.append(
            ApiStatusSampleIssue(
                operation_id,
                status_name,
                f"response sample does not match schema: {error.errors()[0]['msg']}",
            )
        )


def _check_error_resource_schema(
    issues: list[ApiStatusSampleIssue],
    operation_id: str,
    status_name: str,
    status_code: int,
    response_sample: dict[str, Any],
    model: type[BaseModel] | None,
) -> None:
    if status_code < 400:
        return
    if model is None:
        issues.append(ApiStatusSampleIssue(operation_id, status_name, "ErrorResource is missing"))
        return

    raw_error_body: object = response_sample.get("error", {})
    if not isinstance(raw_error_body, dict):
        issues.append(ApiStatusSampleIssue(operation_id, status_name, "error body must be object"))
        return
    error_body = cast(dict[str, Any], raw_error_body)
    raw_details: object = error_body.get("details", [])
    if not isinstance(raw_details, list) or not raw_details:
        issues.append(
            ApiStatusSampleIssue(operation_id, status_name, "error details sample is missing")
        )
        return
    details = cast(list[object], raw_details)
    detail = details[0]
    if not isinstance(detail, dict):
        issues.append(
            ApiStatusSampleIssue(operation_id, status_name, "error detail must be object")
        )
        return
    detail_dict = cast(dict[str, Any], detail)
    resource = detail_dict.get("resource")
    if not isinstance(resource, dict) or not resource:
        issues.append(
            ApiStatusSampleIssue(operation_id, status_name, "error resource sample is missing")
        )
        return
    resource_dict = cast(dict[str, Any], resource)

    allowed_keys = set(model.model_json_schema().get("properties", {}))
    extra_keys = set(resource_dict) - allowed_keys
    if extra_keys:
        issues.append(
            ApiStatusSampleIssue(
                operation_id,
                status_name,
                f"error resource has undefined keys: {', '.join(sorted(extra_keys))}",
            )
        )
        return
    try:
        model.model_validate(resource_dict)
    except ValidationError as error:
        issues.append(
            ApiStatusSampleIssue(
                operation_id,
                status_name,
                f"error resource sample does not match schema: {error.errors()[0]['msg']}",
            )
        )


def _check_openapi_example(
    issues: list[ApiStatusSampleIssue],
    operation_id: str,
    status_name: str,
    operation: dict[str, Any],
    response_sample: dict[str, Any],
) -> None:
    responses = cast(dict[str, Any], operation["responses"])
    response = responses.get(status_name)
    if not isinstance(response, dict):
        return
    content = cast(dict[str, Any], response).get("content")
    if not isinstance(content, dict):
        issues.append(ApiStatusSampleIssue(operation_id, status_name, "OpenAPI content is missing"))
        return
    media = cast(dict[str, Any], content).get("application/json")
    if not isinstance(media, dict) or "example" not in media:
        issues.append(ApiStatusSampleIssue(operation_id, status_name, "OpenAPI example is missing"))
        return
    if media["example"] != _drop_none(response_sample):
        issues.append(
            ApiStatusSampleIssue(
                operation_id,
                status_name,
                "OpenAPI example does not match response sample",
            )
        )


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        value_dict = cast(dict[str, Any], value)
        return {key: _drop_none(child) for key, child in value_dict.items() if child is not None}
    if isinstance(value, list):
        value_list = cast(list[object], value)
        return [_drop_none(child) for child in value_list]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    args = parser.parse_args()

    issues = check_api_status_samples(args.api_root)
    for issue in issues:
        print(f"{issue.operation_id} {issue.status_code}: {issue.message}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
