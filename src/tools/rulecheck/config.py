from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

DEFAULT_CONFIG: dict[str, Any] = {
    "ambiguous_words": [
        "適切",
        "必要に応じて",
        "可能な限り",
        "できるだけ",
        "原則",
        "最小限",
        "など",
        "十分",
        "なるべく",
    ],
    "api_common_files": [
        "__init__.py",
        "base.py",
        "common.py",
        "deps.py",
        "responses.py",
        "router_errors.py",
        "sequence_types.py",
        "types.py",
    ],
    "operation_required_files": [
        "__init__.py",
        "router.py",
        "functions.py",
        "schemas.py",
        "samples.py",
        "queries.py",
        "generated",
        "sql",
    ],
    "tools_required_files": [
        "check_api_function_names.py",
        "generate_api_sequences.py",
        "check_api_mermaid_sequences.py",
        "generate_queries.py",
        "generate_db_crud.py",
        "check_operational_logging.py",
    ],
    "quality_commands": [
        "ruff format",
        "ruff check",
        "pyright",
        "mypy",
        "pytest",
    ],
    "forbidden_provider_imports": [
        "boto3",
        "botocore",
        "httpx",
        "requests",
    ],
    "allowed_provider_import_globs": [
        "src/app/integrations/_aws_boto3.py",
        "src/app/integrations/common_errors.py",
        "src/app/integrations/**/deps.py",
        "src/app/integrations/**/boto3_provider/*.py",
        "tests/**/*.py",
    ],
    "managed_literals": {
        "hub-admin": ["common.py"],
        "PUBLIC_PKCE": ["api_access_requests/common.py", "projects/common.py"],
        "PUBLIC": ["projects/common.py"],
        "CONFIDENTIAL_CLIENT_CREDENTIALS": ["projects/common.py"],
        "CONFIDENTIAL": ["projects/common.py"],
        "CALLBACK": ["projects/common.py"],
        "LOGOUT": ["projects/common.py"],
        "OPENAPI": ["apis/common.py"],
        "published": ["apis/common.py"],
        "openapi": ["apis/common.py"],
    },
    "metrics": {
        "exclude_globs": [
            "src/app/**/generated/*.py",
            "src/app/**/generated/**/*.py",
            "tests/generated/**/*.py",
        ],
        "cyclomatic_complexity": [
            {"glob": "src/app/apis/**/router.py", "max": 10, "function_kind": "endpoint"},
            {"glob": "src/app/**/*.py", "max": 10},
            {"glob": "src/tools/**/*.py", "max": 12},
        ],
        "control_nesting_depth": [
            {"glob": "src/app/apis/**/router.py", "max": 3, "function_kind": "endpoint"},
            {"glob": "src/app/**/*.py", "max": 3},
            {"glob": "src/tools/**/*.py", "max": 4},
        ],
        "function_logical_lines": [
            {"glob": "src/app/apis/**/router.py", "max": 120, "function_kind": "endpoint"},
            {"glob": "src/app/**/*.py", "max": 100},
            {"glob": "src/tools/**/*.py", "max": 120},
        ],
        "file_logical_lines": [
            {"glob": "src/app/apis/**/router.py", "max": 260},
            {"glob": "src/app/**/*.py", "max": 600},
            {"glob": "src/tools/**/*.py", "max": 1000},
        ],
        "function_argument_count": [
            {"glob": "src/app/apis/**/router.py", "max": 8, "function_kind": "endpoint"},
            {"glob": "src/app/**/*.py", "max": 5, "function_kind": "public"},
            {"glob": "src/app/**/*.py", "max": 5, "function_kind": "private"},
            {"glob": "src/tools/**/*.py", "max": 6, "function_kind": "public"},
            {"glob": "src/tools/**/*.py", "max": 6, "function_kind": "private"},
            {"glob": "src/tools/**/*.py", "max": 8, "function_kind": "cli_adapter"},
        ],
        "endpoint_business_argument_count": [
            {"glob": "src/app/apis/**/router.py", "max": 3, "function_kind": "endpoint"},
        ],
        "return_count": [
            {"glob": "src/app/apis/**/router.py", "max": 6, "function_kind": "endpoint"},
            {"glob": "src/app/**/*.py", "max": 6},
            {"glob": "src/tools/**/*.py", "max": 8},
        ],
        "try_body_statement_count": [
            {"glob": "src/app/apis/**/router.py", "max": 5, "function_kind": "endpoint"},
        ],
        "local_variable_count": [
            {"glob": "src/app/**/*.py", "max": 10},
            {"glob": "src/tools/**/*.py", "max": 15},
        ],
        "branch_count": [
            {"glob": "src/app/apis/**/router.py", "max": 4, "function_kind": "endpoint"},
            {"glob": "src/app/**/*.py", "max": 8},
            {"glob": "src/tools/**/*.py", "max": 10},
        ],
        "condition_complexity": {
            "bool_ops_max": 3,
            "comparison_ops_max": 3,
            "ast_depth_max": 7,
            "thresholds": [
                {"glob": "src/app/apis/**/router.py", "bool_ops_max": 1},
                {"glob": "src/app/**/*.py", "bool_ops_max": 3},
                {"glob": "src/tools/**/*.py", "bool_ops_max": 3},
            ],
            "forbid_mixed_and_or": False,
            "forbid_nested_ternary": True,
        },
    },
}


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(cast(dict[str, Any], merged[key]), cast(dict[str, Any], value))
        else:
            merged[key] = value
    return merged


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return deepcopy(DEFAULT_CONFIG)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return _merge(DEFAULT_CONFIG, cast(dict[str, Any], raw))
