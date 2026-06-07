from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tools.generate_db_crud import CrudMatrix, write_crud_csv

ServiceName = Literal["api_gateway", "cognito", "secrets_manager"]


@dataclass(frozen=True)
class MethodCrud:
    resource: str
    operation: str


@dataclass(frozen=True)
class ServiceCrudConfig:
    output_name: str
    variable_names: frozenset[str]
    methods: dict[str, MethodCrud]

    @property
    def resources(self) -> list[str]:
        return sorted({method.resource for method in self.methods.values()})


SERVICE_CONFIGS: dict[ServiceName, ServiceCrudConfig] = {
    "api_gateway": ServiceCrudConfig(
        output_name="api_gateway_crud.gen.csv",
        variable_names=frozenset({"api_gateway_control"}),
        methods={
            "create_api_key": MethodCrud("api_key", "C"),
            "create_usage_plan": MethodCrud("usage_plan", "C"),
            "create_usage_plan_key": MethodCrud("usage_plan_key", "C"),
            "add_usage_plan_stage": MethodCrud("usage_plan_stage", "C"),
            "get_stage": MethodCrud("stage", "R"),
            "get_resources": MethodCrud("resource", "R"),
            "get_method": MethodCrud("method", "R"),
            "update_method": MethodCrud("method", "U"),
            "create_deployment": MethodCrud("deployment", "C"),
        },
    ),
    "cognito": ServiceCrudConfig(
        output_name="cognito_crud.gen.csv",
        variable_names=frozenset({"identity_admin"}),
        methods={
            "create_public_user_pool_client": MethodCrud("user_pool_client", "C"),
            "create_confidential_user_pool_client": MethodCrud("user_pool_client", "C"),
            "describe_user_pool_client": MethodCrud("user_pool_client", "R"),
            "update_user_pool_client": MethodCrud("user_pool_client", "U"),
            "describe_resource_server": MethodCrud("resource_server", "R"),
            "update_resource_server": MethodCrud("resource_server", "U"),
        },
    ),
    "secrets_manager": ServiceCrudConfig(
        output_name="secrets_manager_crud.gen.csv",
        variable_names=frozenset({"secret_values"}),
        methods={
            "get_hash_pepper": MethodCrud("hash_pepper", "R"),
        },
    ),
}


def api_name_from_functions_path(functions_path: Path, api_root: Path) -> str:
    relative = functions_path.relative_to(api_root)
    if relative.name != "functions.py" or len(relative.parts) < 3:
        raise ValueError(f"functions.py must be under an API directory: {functions_path}")
    return relative.parts[-2]


def called_methods(tree: ast.AST, variable_names: frozenset[str]) -> set[str]:
    methods: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id in variable_names
        ):
            methods.add(function.attr)
    return methods


def file_operations(functions_path: Path, config: ServiceCrudConfig) -> dict[str, set[str]]:
    tree = ast.parse(functions_path.read_text(encoding="utf-8"), filename=functions_path.as_posix())
    operations: dict[str, set[str]] = {}
    for method_name in called_methods(tree, config.variable_names):
        method_crud = config.methods.get(method_name)
        if method_crud is None:
            continue
        operations.setdefault(method_crud.resource, set()).add(method_crud.operation)
    return operations


def collect_service_crud(api_root: Path, config: ServiceCrudConfig) -> CrudMatrix:
    matrix = CrudMatrix(tables=set(config.resources))
    for functions_path in sorted(api_root.rglob("functions.py")):
        api = api_name_from_functions_path(functions_path, api_root)
        operations = file_operations(functions_path, config)
        if not operations:
            continue
        matrix.apis.add(api)
        for resource, resource_operations in operations.items():
            for operation in resource_operations:
                matrix.add(api, resource, operation)
    return matrix


def generate_service(api_root: Path, output_dir: Path, service_name: ServiceName) -> Path:
    config = SERVICE_CONFIGS[service_name]
    matrix = collect_service_crud(api_root, config)
    return write_crud_csv(matrix, config.resources, output_dir / config.output_name)


def generate(api_root: Path, output_dir: Path, service_names: list[ServiceName]) -> list[Path]:
    return [generate_service(api_root, output_dir, service_name) for service_name in service_names]


def service_names_for_arg(value: str) -> list[ServiceName]:
    if value == "all":
        return list(SERVICE_CONFIGS)
    if value not in SERVICE_CONFIGS:
        expected = ", ".join(("all", *SERVICE_CONFIGS))
        raise argparse.ArgumentTypeError(f"service must be one of: {expected}")
    return [value]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate API x external service resource CRUD CSV files."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/spec/30.crud"))
    parser.add_argument(
        "--service",
        type=service_names_for_arg,
        default=service_names_for_arg("all"),
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    output_paths = generate(args.api_root, args.output_dir, args.service)
    for output_path in output_paths:
        print(f"Generated {output_path.as_posix()}.")


if __name__ == "__main__":  # pragma: no cover
    main()
