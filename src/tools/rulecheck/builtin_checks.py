from __future__ import annotations

import ast
import fnmatch
import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .models import CheckContext, CheckResult, RuleItem
from .rule_parser import iter_normative_lines, normative_lines_without_checker

Checker = Callable[[RuleItem, CheckContext], list[CheckResult]]


def _pass(name: str, item: RuleItem, message: str) -> list[CheckResult]:
    return [CheckResult(name, "PASS", message, rule_id=item.id)]


def _fail(
    name: str, item: RuleItem, message: str, path: Path | None = None, line: int | None = None
) -> CheckResult:
    return CheckResult(name, "FAIL", message, path=path, line=line, rule_id=item.id)


def _skip(name: str, item: RuleItem, message: str) -> list[CheckResult]:
    return [CheckResult(name, "SKIP", message, rule_id=item.id)]


def _repo_path(context: CheckContext, path: str | Path) -> Path:
    return context.repo_root / path


def _rel(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _logical_lines(lines: Iterable[str]) -> int:
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def _python_files(root: Path, pattern: str = "**/*.py") -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.glob(pattern) if "__pycache__" not in path.parts)


def _operation_dirs(context: CheckContext) -> list[Path]:
    root = _repo_path(context, "src/app/apis")
    if not root.exists():
        return []
    dirs: set[Path] = set()
    for marker in (
        "router.py",
        "functions.py",
        "contract.py",
        "queries.py",
        "generated/queries.py",
    ):
        for path in root.glob(f"*/*/{marker}"):
            dirs.add(path.parent.parent if marker.startswith("generated/") else path.parent)
    return sorted(dirs)


def _api_router_files(context: CheckContext) -> list[Path]:
    return sorted(
        path / "router.py" for path in _operation_dirs(context) if (path / "router.py").exists()
    )


def _api_function_files(context: CheckContext) -> list[Path]:
    return sorted(
        path / "functions.py"
        for path in _operation_dirs(context)
        if (path / "functions.py").exists()
    )


def _parse_python(path: Path) -> ast.AST | None:
    try:
        return ast.parse(_read(path), filename=str(path))
    except SyntaxError:
        return None


def _imported_modules(tree: ast.AST) -> list[tuple[str, int]]:
    modules: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append((node.module, node.lineno))
    return modules


def _matches_any(path: Path, patterns: Iterable[str]) -> bool:
    value = path.as_posix()
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _forbidden_import(module: str, context: CheckContext, path: Path) -> str | None:
    rel = _rel(path, context.repo_root)
    allowed = context.config.get("allowed_provider_import_globs", [])
    if _matches_any(rel, allowed):
        return None
    for forbidden in context.config.get("forbidden_provider_imports", []):
        if module == forbidden or module.startswith(f"{forbidden}."):
            return forbidden
    if ".boto3_provider" in module or (module.endswith(".client") and ".provider" in module):
        return module
    return None


# Rule document checks -----------------------------------------------------


def rule_has_checker_tag(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    missing = normative_lines_without_checker(context.rules_dir)
    if not missing:
        return _pass("rule_has_checker_tag", item, "all normative lines have checker tags")
    return [
        _fail(
            "rule_has_checker_tag", item, "normative line has no checker tag", path=path, line=line
        )
        for path, line, _ in missing
    ]


def normative_no_ambiguous_words(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    words = [str(word) for word in context.config.get("ambiguous_words", [])]
    issues: list[CheckResult] = []
    for path, line, text in iter_normative_lines(context.rules_dir):
        for word in words:
            if word and word in text:
                issues.append(
                    _fail(
                        "normative_no_ambiguous_words",
                        item,
                        f"ambiguous word {word!r} found in normative line",
                        path=path,
                        line=line,
                    )
                )
    if issues:
        return issues
    return _pass(
        "normative_no_ambiguous_words", item, "no configured ambiguous words in normative lines"
    )


def required_paths(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    paths = re.findall(r"`([^`]+)`", item.text)
    issues: list[CheckResult] = []
    checked = 0
    for raw in paths:
        if any(token in raw for token in ("{", "}", "*", "[checker:", "source:")):
            continue
        if not raw.startswith(
            ("src/", "docs/", "tests/", "config/", "pyproject.toml", "README.md")
        ):
            continue
        checked += 1
        if not _repo_path(context, raw).exists():
            issues.append(_fail("required_paths", item, f"required path does not exist: {raw}"))
    if issues:
        return issues
    return _pass("required_paths", item, f"checked {checked} concrete paths")


# Repository and entrypoint checks ----------------------------------------


def repo_python_policy(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    path = _repo_path(context, "pyproject.toml")
    if not path.exists():
        return [_fail("repo_python_policy", item, "pyproject.toml is missing", path=path)]
    text = _read(path)
    required = {
        'requires-python = ">=3.14,<3.15"': "Python range must be >=3.14,<3.15",
        'target-version = "py314"': "Ruff target must be py314",
        'pythonVersion = "3.14"': "Pyright pythonVersion must be 3.14",
        'python_version = "3.14"': "mypy python_version must be 3.14",
    }
    issues = [
        _fail("repo_python_policy", item, message, path=path)
        for needle, message in required.items()
        if needle not in text
    ]
    if issues:
        return issues
    return _pass(
        "repo_python_policy",
        item,
        "pyproject Python and typing policy matches current implementation",
    )


def quality_commands_declared(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    combined = ""
    for name in ("README.md", "pyproject.toml"):
        path = _repo_path(context, name)
        if path.exists():
            combined += "\n" + _read(path)
    issues = [
        _fail("quality_commands_declared", item, f"quality command is not documented: {command}")
        for command in context.config.get("quality_commands", [])
        if command not in combined
    ]
    if issues:
        return issues
    return _pass("quality_commands_declared", item, "quality commands are documented")


def entrypoint_fastapi(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    path = _repo_path(context, "src/app/main.py")
    if not path.exists():
        return [_fail("entrypoint_fastapi", item, "src/app/main.py is missing", path=path)]
    text = _read(path)
    issues: list[CheckResult] = []
    for needle in ("FastAPI", "def create_app", "app = create_app()"):
        if needle not in text:
            issues.append(
                _fail("entrypoint_fastapi", item, f"main.py must contain {needle!r}", path=path)
            )
    if issues:
        return issues
    return _pass("entrypoint_fastapi", item, "FastAPI app factory and module app are present")


def health_route(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    path = _repo_path(context, "src/app/main.py")
    if not path.exists():
        return [_fail("health_route", item, "src/app/main.py is missing", path=path)]
    text = _read(path)
    if '"/health"' not in text and "'/health'" not in text:
        return [_fail("health_route", item, "/health route is missing", path=path)]
    return _pass("health_route", item, "/health route is declared")


def main_router_includes(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    main = _repo_path(context, "src/app/main.py")
    if not main.exists():
        return [_fail("main_router_includes", item, "src/app/main.py is missing", path=main)]
    text = _read(main)
    operations = _operation_dirs(context)
    issues: list[CheckResult] = []
    include_count = text.count("include_router(")
    for op_dir in operations:
        rel = _rel(op_dir, context.repo_root)
        parts = rel.parts
        module = f"app.apis.{parts[-2]}.{parts[-1]}.router"
        if module not in text:
            issues.append(
                _fail(
                    "main_router_includes",
                    item,
                    f"router module not imported in main.py: {module}",
                    path=main,
                )
            )
    if include_count < len(operations):
        issues.append(
            _fail(
                "main_router_includes",
                item,
                f"include_router calls {include_count} < operation routers {len(operations)}",
                path=main,
            )
        )
    if issues:
        return issues
    return _pass(
        "main_router_includes", item, f"main.py includes {len(operations)} operation routers"
    )


def entrypoint_no_provider_imports(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in (_repo_path(context, "src/app/main.py"), _repo_path(context, "src/app/local.py")):
        if not path.exists():
            continue
        tree = _parse_python(path)
        if tree is None:
            issues.append(
                _fail("entrypoint_no_provider_imports", item, "cannot parse Python file", path=path)
            )
            continue
        for module, line in _imported_modules(tree):
            forbidden = _forbidden_import(module, context, path)
            if forbidden:
                issues.append(
                    _fail(
                        "entrypoint_no_provider_imports",
                        item,
                        f"forbidden provider import: {module}",
                        path=path,
                        line=line,
                    )
                )
    if issues:
        return issues
    return _pass(
        "entrypoint_no_provider_imports", item, "entrypoints do not import provider clients"
    )


# API layout checks --------------------------------------------------------


def api_common_files(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/app/apis")
    issues = [
        _fail("api_common_files", item, f"common API file is missing: {name}", path=root / name)
        for name in context.config.get("api_common_files", [])
        if not (root / name).exists()
    ]
    if issues:
        return issues
    return _pass("api_common_files", item, "API common files are present")


def api_domain_layout(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/app/apis")
    if not root.exists():
        return [_fail("api_domain_layout", item, "src/app/apis is missing", path=root)]
    operations = _operation_dirs(context)
    if not operations:
        return [
            _fail(
                "api_domain_layout",
                item,
                "no operation directory found under src/app/apis/*/*",
                path=root,
            )
        ]
    issues: list[CheckResult] = []
    for path in operations:
        rel = _rel(path, root)
        if len(rel.parts) != 2:
            issues.append(
                _fail(
                    "api_domain_layout",
                    item,
                    f"operation directory must be two levels under api root: {rel}",
                    path=path,
                )
            )
    if issues:
        return issues
    return _pass(
        "api_domain_layout", item, f"found {len(operations)} two-level operation directories"
    )


def api_operation_required_files(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    operations = _operation_dirs(context)
    issues: list[CheckResult] = []
    for op_dir in operations:
        for name in context.config.get("operation_required_files", []):
            if not (op_dir / name).exists():
                issues.append(
                    _fail(
                        "api_operation_required_files",
                        item,
                        f"operation required path is missing: {name}",
                        path=op_dir / name,
                    )
                )
    if issues:
        return issues
    return _pass(
        "api_operation_required_files", item, f"checked {len(operations)} operation directories"
    )


def forbid_generated_subdir_queries(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/app/apis")
    matches = sorted(root.glob("*/*/generated/queries.py")) if root.exists() else []
    if matches:
        return [
            _fail(
                "forbid_generated_subdir_queries",
                item,
                "queries.py must not be under generated/",
                path=path,
            )
            for path in matches
        ]
    return _pass(
        "forbid_generated_subdir_queries", item, "no operation generated/queries.py files found"
    )


def generated_queries_layout(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for op_dir in _operation_dirs(context):
        if not (op_dir / "sql").exists():
            continue
        for path in (
            op_dir / "generated" / "__init__.py",
            op_dir / "generated" / "queries.py",
            op_dir / "queries.py",
        ):
            if not path.exists():
                issues.append(
                    _fail(
                        "generated_queries_layout",
                        item,
                        "operation generated query wrapper path is missing",
                        path=path,
                    )
                )
    if issues:
        return issues
    return _pass("generated_queries_layout", item, "operation generated query wrappers exist")


def operation_sql_dir_files(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    operations = _operation_dirs(context)
    issues: list[CheckResult] = []
    for op_dir in operations:
        sql_dir = op_dir / "sql"
        sql_files = sorted(sql_dir.glob("*.sql")) if sql_dir.exists() else []
        if not sql_files:
            issues.append(
                _fail(
                    "operation_sql_dir_files",
                    item,
                    "operation sql directory has no .sql files",
                    path=sql_dir,
                )
            )
            continue
        for sql_path in sql_files:
            if not re.match(r"^\d{3}_[a-z0-9_]+\.sql$", sql_path.name):
                issues.append(
                    _fail(
                        "operation_sql_dir_files",
                        item,
                        "SQL filename must match 000_name.sql",
                        path=sql_path,
                    )
                )
    if issues:
        return issues
    return _pass(
        "operation_sql_dir_files", item, f"checked SQL files for {len(operations)} operations"
    )


def queries_generated_marker(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for op_dir in _operation_dirs(context):
        path = op_dir / "generated" / "queries.py"
        if not path.exists():
            continue
        text = _read(path)
        for needle in (
            "This file is generated from SQL files in the sibling sql directory.",
            "Do not edit generated models by hand.",
            'SQL_DIR = Path(__file__).parents[1] / "sql"',
        ):
            if needle not in text:
                issues.append(
                    _fail(
                        "queries_generated_marker",
                        item,
                        f"queries.py missing marker: {needle}",
                        path=path,
                    )
                )
        shim_path = op_dir / "queries.py"
        if shim_path.exists() and "from .generated.queries import *" not in _read(shim_path):
            issues.append(
                _fail(
                    "queries_generated_marker",
                    item,
                    "queries.py compatibility shim must re-export generated queries",
                    path=shim_path,
                )
            )
    if issues:
        return issues
    return _pass(
        "queries_generated_marker", item, "operation generated queries contain generated markers"
    )


# Router checks ------------------------------------------------------------


def router_import_api_functions_alias(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in _api_router_files(context):
        rel = _rel(path.parent, context.repo_root)
        parts = rel.parts
        expected = f"from app.apis.{parts[-2]}.{parts[-1]} import functions as api_functions"
        if expected not in _read(path):
            issues.append(
                _fail(
                    "router_import_api_functions_alias",
                    item,
                    f"router must import same-operation functions as api_functions: {expected}",
                    path=path,
                )
            )
    if issues:
        return issues
    return _pass(
        "router_import_api_functions_alias",
        item,
        "routers import operation functions as api_functions",
    )


def router_no_direct_resource_calls(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    forbidden_calls = {"fetch_all", "fetch_one", "execute_sql", "create_boto3_client"}
    allowed_session_calls = {"commit", "rollback"}
    for path in _api_router_files(context):
        tree = _parse_python(path)
        if tree is None:
            issues.append(
                _fail("router_no_direct_resource_calls", item, "cannot parse router.py", path=path)
            )
            continue
        for module, line in _imported_modules(tree):
            if module.endswith(".queries") or module == "app.db.query":
                issues.append(
                    _fail(
                        "router_no_direct_resource_calls",
                        item,
                        f"router imports query module: {module}",
                        path=path,
                        line=line,
                    )
                )
            forbidden = _forbidden_import(module, context, path)
            if forbidden:
                issues.append(
                    _fail(
                        "router_no_direct_resource_calls",
                        item,
                        f"router imports provider module: {module}",
                        path=path,
                        line=line,
                    )
                )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name in forbidden_calls:
                issues.append(
                    _fail(
                        "router_no_direct_resource_calls",
                        item,
                        f"router calls direct resource helper: {name}",
                        path=path,
                        line=node.lineno,
                    )
                )
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "session" and node.func.attr in allowed_session_calls:
                    continue
                if node.func.value.id in {"session", "queries"}:
                    issues.append(
                        _fail(
                            "router_no_direct_resource_calls",
                            item,
                            f"router calls direct resource object: {node.func.value.id}.{node.func.attr}",
                            path=path,
                            line=node.lineno,
                        )
                    )
    if issues:
        return issues
    return _pass(
        "router_no_direct_resource_calls",
        item,
        "routers do not call SQL/query/provider clients directly",
    )


def router_logging_wrapper(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    log_methods = {"debug", "info", "warning", "warn", "error", "exception", "critical"}
    for path in _api_router_files(context):
        tree = _parse_python(path)
        if tree is None:
            continue
        text = _read(path)
        for module, line in _imported_modules(tree):
            if module == "logging" or module.startswith("logging."):
                issues.append(
                    _fail(
                        "router_logging_wrapper",
                        item,
                        "router imports stdlib logging",
                        path=path,
                        line=line,
                    )
                )
        has_log_call = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in log_methods
            for node in ast.walk(tree)
        )
        if has_log_call and "get_operation_logger" not in text:
            issues.append(
                _fail(
                    "router_logging_wrapper",
                    item,
                    "router log calls must use get_operation_logger wrapper",
                    path=path,
                )
            )
    if issues:
        return issues
    return _pass("router_logging_wrapper", item, "router logging uses operational wrapper")


def router_error_handling(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    allowed = {
        "ROUTER_HANDLED_EXCEPTIONS",
        "NonBlockingOperationalError",
        "IntegrityError",
        "SQLAlchemyError",
    }
    for path in _api_router_files(context):
        tree = _parse_python(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            exc_name = _exception_name(node.type)
            if exc_name in {"Exception", "BaseException"}:
                issues.append(
                    _fail(
                        "router_error_handling",
                        item,
                        f"router catches generic exception: {exc_name}",
                        path=path,
                        line=node.lineno,
                    )
                )
            if exc_name not in allowed:
                issues.append(
                    _fail(
                        "router_error_handling",
                        item,
                        f"router catches undeclared exception group: {exc_name}",
                        path=path,
                        line=node.lineno,
                    )
                )
            if not any(isinstance(child, ast.Return) for child in ast.walk(node)):
                issues.append(
                    _fail(
                        "router_error_handling",
                        item,
                        "router except handler must return a response",
                        path=path,
                        line=node.lineno,
                    )
                )
    if issues:
        return issues
    return _pass(
        "router_error_handling", item, "router exception handlers use declared exception groups"
    )


def router_bool_conditions(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for functions_path in _api_function_files(context):
        router_path = functions_path.with_name("router.py")
        if not router_path.exists():
            continue
        bool_names = _bool_function_names(functions_path)
        if not bool_names:
            continue
        tree = _parse_python(router_path)
        if tree is None:
            issues.append(
                _fail("router_bool_conditions", item, "cannot parse router.py", path=router_path)
            )
            continue
        parents = _parent_map(tree)
        reported: set[tuple[int, str]] = set()
        for node in ast.walk(tree):
            function_name = _called_api_function(node)
            if function_name not in bool_names:
                continue
            if _is_inside_if_test(node, parents):
                continue
            if _is_assigned_for_later_condition(node, parents):
                continue
            key = (getattr(node, "lineno", 0), function_name)
            if key in reported:
                continue
            reported.add(key)
            issues.append(
                _fail(
                    "router_bool_conditions",
                    item,
                    "bool-returning api_functions call must be used in if condition",
                    path=router_path,
                    line=getattr(node, "lineno", None),
                )
            )
    if issues:
        return issues
    return _pass(
        "router_bool_conditions",
        item,
        "bool-returning function calls in routers are used in if tests",
    )


def router_no_inline_business_comparison(
    item: RuleItem, context: CheckContext
) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in _api_router_files(context):
        tree = _parse_python(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if any(isinstance(child, ast.Compare) for child in ast.walk(node.test)):
                    issues.append(
                        _fail(
                            "router_no_inline_business_comparison",
                            item,
                            "router if test must not contain inline comparison",
                            path=path,
                            line=node.lineno,
                        )
                    )
    if issues:
        return issues
    return _pass(
        "router_no_inline_business_comparison",
        item,
        "router if tests do not contain inline comparisons",
    )


# Function checks ----------------------------------------------------------


def functions_public_contract(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in _api_function_files(context):
        tree = _parse_python(path)
        if tree is None:
            issues.append(
                _fail("functions_public_contract", item, "cannot parse functions.py", path=path)
            )
            continue
        for fn in _public_functions(tree):
            if ast.get_docstring(fn) is None:
                issues.append(
                    _fail(
                        "functions_public_contract",
                        item,
                        "public function requires docstring",
                        path=path,
                        line=fn.lineno,
                    )
                )
            if fn.returns is None:
                issues.append(
                    _fail(
                        "functions_public_contract",
                        item,
                        "public function requires return annotation",
                        path=path,
                        line=fn.lineno,
                    )
                )
            args = [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]
            for arg in args:
                if arg.annotation is None and arg.arg not in {"self", "cls"}:
                    issues.append(
                        _fail(
                            "functions_public_contract",
                            item,
                            f"argument requires annotation: {arg.arg}",
                            path=path,
                            line=fn.lineno,
                        )
                    )
            if "_" not in fn.name:
                issues.append(
                    _fail(
                        "functions_public_contract",
                        item,
                        "public function name must contain an action/predicate prefix and target",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass(
        "functions_public_contract", item, "public functions have docstrings and type annotations"
    )


def functions_vocab_names(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    rule_dir = _repo_path(context, "docs/rule/docs")
    filenames = {
        "actions": "sequence_function_actions.json",
        "targets": "sequence_function_targets.json",
        "predicates": "sequence_function_predicates.json",
        "conditions": "sequence_function_conditions.json",
    }
    if not rule_dir.exists() or not all((rule_dir / name).exists() for name in filenames.values()):
        return _skip("functions_vocab_names", item, "sequence vocabulary JSON files are absent")
    try:
        rules = {key: _load_rule_names(rule_dir / filename) for key, filename in filenames.items()}
    except ValueError as error:
        return [_fail("functions_vocab_names", item, str(error), path=rule_dir)]
    issues: list[CheckResult] = []
    for path in _api_function_files(context):
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _public_functions(tree):
            head, sep, tail = fn.name.partition("_")
            if not sep:
                issues.append(
                    _fail(
                        "functions_vocab_names",
                        item,
                        "function name must contain _",
                        path=path,
                        line=fn.lineno,
                    )
                )
            elif head in rules["predicates"]:
                if tail not in rules["conditions"]:
                    issues.append(
                        _fail(
                            "functions_vocab_names",
                            item,
                            f"condition is not in vocabulary: {tail}",
                            path=path,
                            line=fn.lineno,
                        )
                    )
            elif head in rules["actions"]:
                if tail not in rules["targets"] and not (
                    head == "build" and tail.endswith("_response")
                ):
                    issues.append(
                        _fail(
                            "functions_vocab_names",
                            item,
                            f"target is not in vocabulary: {tail}",
                            path=path,
                            line=fn.lineno,
                        )
                    )
            else:
                issues.append(
                    _fail(
                        "functions_vocab_names",
                        item,
                        f"action or predicate is not in vocabulary: {head}",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass(
        "functions_vocab_names", item, "public function names match sequence vocabulary JSON"
    )


def functions_resource_usage(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    marker = "@resource-free"
    exact_free = {"get_caller_identity"}
    free_prefixes = ("is_", "has_", "validate_", "build_", "merge_", "apply_")
    issues: list[CheckResult] = []
    for path in _api_function_files(context):
        text = _read(path)
        lines = text.splitlines()
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _public_functions(tree):
            if fn.name in exact_free or fn.name.startswith(free_prefixes):
                continue
            start = max(fn.lineno - 3, 0)
            end = min(fn.lineno + 1, len(lines))
            has_marker = marker in (ast.get_docstring(fn) or "") or any(
                marker in line for line in lines[start:end]
            )
            if has_marker:
                continue
            if _function_uses_queries_or_resource(fn):
                continue
            issues.append(
                _fail(
                    "functions_resource_usage",
                    item,
                    f"non-validation function must use queries/integration or declare {marker}",
                    path=path,
                    line=fn.lineno,
                )
            )
    if issues:
        return issues
    return _pass(
        "functions_resource_usage",
        item,
        "non-validation functions use resources or declare resource-free marker",
    )


def functions_exception_policy(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    runtime_names = {"session", "api_gateway_control", "identity_admin", "secret_values"}
    suffixes = ("_client", "_control", "_admin", "_values")
    issues: list[CheckResult] = []
    targets = [*_api_function_files(context)]
    common = _repo_path(context, "src/app/apis/projects/common.py")
    if common.exists():
        targets.append(common)
    for path in targets:
        tree = _parse_python(path)
        if tree is None:
            continue
        parents = _parent_map(tree)
        for fn in [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]:
            optional = _optional_runtime_dependencies(fn, runtime_names, suffixes)
            missing_calls = [
                node
                for node in ast.walk(fn)
                if isinstance(node, ast.Call)
                and _call_name(node) == "raise_missing_runtime_dependency"
            ]
            if _uses_runtime_dependency(fn, optional) and not missing_calls:
                issues.append(
                    _fail(
                        "functions_exception_policy",
                        item,
                        "runtime dependency function must call raise_missing_runtime_dependency",
                        path=path,
                        line=fn.lineno,
                    )
                )
            for call in missing_calls:
                if not isinstance(parents.get(call), ast.Return):
                    issues.append(
                        _fail(
                            "functions_exception_policy",
                            item,
                            "raise_missing_runtime_dependency must be returned directly",
                            path=path,
                            line=call.lineno,
                        )
                    )
                arg = (
                    call.args[0].value
                    if call.args and isinstance(call.args[0], ast.Constant)
                    else None
                )
                if arg != fn.name:
                    issues.append(
                        _fail(
                            "functions_exception_policy",
                            item,
                            "raise_missing_runtime_dependency argument must match function name",
                            path=path,
                            line=call.lineno,
                        )
                    )
            for raise_node in (node for node in ast.walk(fn) if isinstance(node, ast.Raise)):
                raised = raise_node.exc
                if isinstance(raised, ast.Call) and _call_name(raised) == "HTTPException":
                    issues.append(
                        _fail(
                            "functions_exception_policy",
                            item,
                            "functions.py must not raise HTTPException directly",
                            path=path,
                            line=raise_node.lineno,
                        )
                    )
    if issues:
        return issues
    return _pass("functions_exception_policy", item, "API function exception policy is satisfied")


def managed_literals(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/app/apis")
    if not root.exists():
        return _skip("managed_literals", item, "src/app/apis is absent")
    managed: dict[str, list[str]] = context.config.get("managed_literals", {})
    issues: list[CheckResult] = []
    for path in _python_files(root):
        rel = _rel(path, root).as_posix()
        tree = _parse_python(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            literal = node.value
            if literal not in managed:
                continue
            if rel in managed[literal] or path.name in managed[literal]:
                continue
            issues.append(
                _fail(
                    "managed_literals",
                    item,
                    f"managed literal must be referenced from shared constant or enum: {literal}",
                    path=path,
                    line=node.lineno,
                )
            )
    if issues:
        return issues
    return _pass("managed_literals", item, "managed literals are centralized")


def functions_no_provider_imports(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in _api_function_files(context):
        tree = _parse_python(path)
        if tree is None:
            continue
        for module, line in _imported_modules(tree):
            forbidden = _forbidden_import(module, context, path)
            if forbidden:
                issues.append(
                    _fail(
                        "functions_no_provider_imports",
                        item,
                        f"functions.py imports provider module: {module}",
                        path=path,
                        line=line,
                    )
                )
    if issues:
        return issues
    return _pass(
        "functions_no_provider_imports", item, "functions.py files do not import provider clients"
    )


# SQL and query checks -----------------------------------------------------


def _sql_files(context: CheckContext) -> list[Path]:
    root = _repo_path(context, "src/app/apis")
    if not root.exists():
        return []
    return sorted(root.glob("*/*/sql/*.sql"))


def sql_no_select_star(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in _sql_files(context):
        if re.search(r"\bSELECT\s+\*", _read(path), re.IGNORECASE):
            issues.append(_fail("sql_no_select_star", item, "SELECT * is forbidden", path=path))
    if issues:
        return issues
    return _pass("sql_no_select_star", item, "SQL files do not use SELECT *")


def sql_first_comment_summary(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    for path in _sql_files(context):
        first = next((line.strip() for line in _read(path).splitlines() if line.strip()), "")
        if not first.startswith("-- ") or len(first.removeprefix("-- ").strip()) < 6:
            issues.append(
                _fail(
                    "sql_first_comment_summary",
                    item,
                    "first non-empty SQL line must be a summary comment",
                    path=path,
                    line=1,
                )
            )
    if issues:
        return issues
    return _pass("sql_first_comment_summary", item, "SQL files start with summary comments")


def sql_placeholders_at_names(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    colon_bind = re.compile(r"(?<!:):(?!:)[A-Za-z_][A-Za-z0-9_]*")
    at_bind = re.compile(r"(?<![\w@])@[A-Za-z_][A-Za-z0-9_]*")
    for path in _sql_files(context):
        text = _read(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if colon_bind.search(line):
                issues.append(
                    _fail(
                        "sql_placeholders_at_names",
                        item,
                        "SQL bind placeholder must use @name, not :name",
                        path=path,
                        line=line_no,
                    )
                )
        if "@" in text and not at_bind.search(text):
            issues.append(
                _fail(
                    "sql_placeholders_at_names", item, "@ placeholder syntax is invalid", path=path
                )
            )
    if issues:
        return issues
    return _pass("sql_placeholders_at_names", item, "SQL placeholders use @name syntax")


# Integration / DB / tools -------------------------------------------------


def integration_port_provider_layout(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/app/integrations")
    if not root.exists():
        return [
            _fail(
                "integration_port_provider_layout",
                item,
                "src/app/integrations is missing",
                path=root,
            )
        ]
    resources = [path for path in root.iterdir() if path.is_dir() and not path.name.startswith("_")]
    issues: list[CheckResult] = []
    port_resources = 0
    for resource in resources:
        if not (resource / "port.py").exists():
            continue
        port_resources += 1
        for required in ("schemas.py", "deps.py"):
            if not (resource / required).exists():
                issues.append(
                    _fail(
                        "integration_port_provider_layout",
                        item,
                        f"integration resource missing {required}",
                        path=resource / required,
                    )
                )
        if (resource / "client.py").exists():
            continue
        provider_dirs = [
            child
            for child in resource.iterdir()
            if child.is_dir()
            and (child.name.endswith("_provider") or (child / "client.py").exists())
        ]
        if not provider_dirs:
            issues.append(
                _fail(
                    "integration_port_provider_layout",
                    item,
                    "integration resource has no provider client directory",
                    path=resource,
                )
            )
        for provider in provider_dirs:
            if not (provider / "client.py").exists():
                issues.append(
                    _fail(
                        "integration_port_provider_layout",
                        item,
                        "provider directory must contain client.py",
                        path=provider,
                    )
                )
    if issues:
        return issues
    if port_resources == 0:
        return [
            _fail(
                "integration_port_provider_layout",
                item,
                "no integration resource with port.py found",
                path=root,
            )
        ]
    return _pass(
        "integration_port_provider_layout",
        item,
        f"checked {port_resources} integration port resources",
    )


def integration_provider_boundary(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/app")
    issues: list[CheckResult] = []
    for path in _python_files(root):
        tree = _parse_python(path)
        if tree is None:
            continue
        for module, line in _imported_modules(tree):
            forbidden = _forbidden_import(module, context, path)
            if forbidden:
                issues.append(
                    _fail(
                        "integration_provider_boundary",
                        item,
                        f"provider import outside allowed provider boundary: {module}",
                        path=path,
                        line=line,
                    )
                )
    if issues:
        return issues
    return _pass(
        "integration_provider_boundary", item, "provider imports are confined to provider boundary"
    )


def db_query_contract(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    path = _repo_path(context, "src/app/db/query.py")
    if not path.exists():
        return [_fail("db_query_contract", item, "src/app/db/query.py is missing", path=path)]
    text = _read(path)
    required = [
        "MYSQL_VARIABLE_RE",
        "load_sql",
        "fetch_all",
        "fetch_one",
        "execute_sql",
        "model_parameters",
    ]
    issues = [
        _fail("db_query_contract", item, f"db query helper missing symbol: {name}", path=path)
        for name in required
        if name not in text
    ]
    if issues:
        return issues
    return _pass(
        "db_query_contract", item, "DB query helper exposes current SQL execution contract"
    )


def ddl_exists(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    path = _repo_path(context, "src/db/ddl.sql")
    if not path.exists():
        return [_fail("ddl_exists", item, "src/db/ddl.sql is missing", path=path)]
    if not _read(path).strip():
        return [_fail("ddl_exists", item, "src/db/ddl.sql is empty", path=path)]
    return _pass("ddl_exists", item, "DDL file exists and is non-empty")


def tools_existing_checks(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    root = _repo_path(context, "src/tools")
    issues = [
        _fail(
            "tools_existing_checks",
            item,
            f"required current tool is missing: {name}",
            path=root / name,
        )
        for name in context.config.get("tools_required_files", [])
        if not (root / name).exists()
    ]
    if issues:
        return issues
    return _pass("tools_existing_checks", item, "current generator/checker scripts are present")


# Quantitative metric checks ----------------------------------------------


@dataclass(frozen=True)
class Threshold:
    pattern: str
    max_value: int


def _thresholds(context: CheckContext, key: str) -> list[Threshold]:
    entries = context.config.get("metrics", {}).get(key, [])
    return [Threshold(str(entry["glob"]), int(entry["max"])) for entry in entries]


def _effective_threshold(rel: Path, thresholds: list[Threshold]) -> int | None:
    value = rel.as_posix()
    matches = [threshold for threshold in thresholds if fnmatch.fnmatch(value, threshold.pattern)]
    if not matches:
        return None
    return min(threshold.max_value for threshold in matches)


def _metric_python_files(context: CheckContext, key: str) -> list[tuple[Path, int]]:
    thresholds = _thresholds(context, key)
    paths: dict[Path, int] = {}
    for threshold in thresholds:
        for path in context.repo_root.glob(threshold.pattern):
            if path.is_file() and "__pycache__" not in path.parts:
                rel = _rel(path, context.repo_root)
                effective = _effective_threshold(rel, thresholds)
                if effective is not None:
                    paths[path] = effective
    return sorted(paths.items())


def python_complexity(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    checked = 0
    for path, max_value in _metric_python_files(context, "cyclomatic_complexity"):
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _all_functions(tree):
            checked += 1
            value = _cyclomatic_complexity(fn)
            if value > max_value:
                issues.append(
                    _fail(
                        "python_complexity",
                        item,
                        f"cyclomatic complexity {value} > {max_value}",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass("python_complexity", item, f"checked {checked} functions")


def control_nesting_depth(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    checked = 0
    for path, max_value in _metric_python_files(context, "control_nesting_depth"):
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _all_functions(tree):
            checked += 1
            value = _max_control_depth(fn)
            if value > max_value:
                issues.append(
                    _fail(
                        "control_nesting_depth",
                        item,
                        f"control nesting depth {value} > {max_value}",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass("control_nesting_depth", item, f"checked {checked} functions")


def function_logical_lines(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    checked = 0
    for path, max_value in _metric_python_files(context, "function_logical_lines"):
        lines = _read(path).splitlines()
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _all_functions(tree):
            checked += 1
            end = getattr(fn, "end_lineno", fn.lineno)
            value = _logical_lines(lines[fn.lineno - 1 : end])
            if value > max_value:
                issues.append(
                    _fail(
                        "function_logical_lines",
                        item,
                        f"function logical lines {value} > {max_value}",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass("function_logical_lines", item, f"checked {checked} functions")


def file_logical_lines(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    checked = 0
    for path, max_value in _metric_python_files(context, "file_logical_lines"):
        checked += 1
        value = _logical_lines(_read(path).splitlines())
        if value > max_value:
            issues.append(
                _fail(
                    "file_logical_lines",
                    item,
                    f"file logical lines {value} > {max_value}",
                    path=path,
                )
            )
    if issues:
        return issues
    return _pass("file_logical_lines", item, f"checked {checked} files")


def function_argument_count(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    checked = 0
    for path, max_value in _metric_python_files(context, "function_argument_count"):
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _all_functions(tree):
            checked += 1
            args = [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]
            count = len([arg for arg in args if arg.arg not in {"self", "cls"}])
            if count > max_value:
                issues.append(
                    _fail(
                        "function_argument_count",
                        item,
                        f"function arguments {count} > {max_value}",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass("function_argument_count", item, f"checked {checked} functions")


def return_count(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    issues: list[CheckResult] = []
    checked = 0
    for path, max_value in _metric_python_files(context, "return_count"):
        tree = _parse_python(path)
        if tree is None:
            continue
        for fn in _all_functions(tree):
            checked += 1
            count = sum(1 for node in ast.walk(fn) if isinstance(node, ast.Return))
            if count > max_value:
                issues.append(
                    _fail(
                        "return_count",
                        item,
                        f"return statements {count} > {max_value}",
                        path=path,
                        line=fn.lineno,
                    )
                )
    if issues:
        return issues
    return _pass("return_count", item, f"checked {checked} functions")


def condition_complexity(item: RuleItem, context: CheckContext) -> list[CheckResult]:
    settings = context.config.get("metrics", {}).get("condition_complexity", {})
    bool_max = int(settings.get("bool_ops_max", 2))
    compare_max = int(settings.get("comparison_ops_max", 2))
    depth_max = int(settings.get("ast_depth_max", 5))
    forbid_mixed = bool(settings.get("forbid_mixed_and_or", True))
    forbid_nested_ternary = bool(settings.get("forbid_nested_ternary", True))
    issues: list[CheckResult] = []
    checked = 0
    for path, _ in _metric_python_files(context, "cyclomatic_complexity"):
        tree = _parse_python(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            tests: list[ast.AST] = []
            if isinstance(node, (ast.If, ast.While, ast.Assert)):
                tests.append(node.test)
            if isinstance(node, ast.IfExp):
                tests.append(node.test)
            for test in tests:
                checked += 1
                bool_ops = _bool_operator_count(test)
                comparisons = sum(
                    len(compare.ops)
                    for compare in ast.walk(test)
                    if isinstance(compare, ast.Compare)
                )
                depth = _ast_depth(test)
                if bool_ops > bool_max:
                    issues.append(
                        _fail(
                            "condition_complexity",
                            item,
                            f"condition bool operators {bool_ops} > {bool_max}",
                            path=path,
                            line=getattr(node, "lineno", None),
                        )
                    )
                if comparisons > compare_max:
                    issues.append(
                        _fail(
                            "condition_complexity",
                            item,
                            f"condition comparison operators {comparisons} > {compare_max}",
                            path=path,
                            line=getattr(node, "lineno", None),
                        )
                    )
                if depth > depth_max:
                    issues.append(
                        _fail(
                            "condition_complexity",
                            item,
                            f"condition AST depth {depth} > {depth_max}",
                            path=path,
                            line=getattr(node, "lineno", None),
                        )
                    )
                if forbid_mixed and _has_mixed_and_or(test):
                    issues.append(
                        _fail(
                            "condition_complexity",
                            item,
                            "condition mixes and/or",
                            path=path,
                            line=getattr(node, "lineno", None),
                        )
                    )
            if forbid_nested_ternary and isinstance(node, ast.IfExp):
                if (
                    any(isinstance(child, ast.IfExp) for child in ast.walk(node.test))
                    or isinstance(node.body, ast.IfExp)
                    or isinstance(node.orelse, ast.IfExp)
                ):
                    issues.append(
                        _fail(
                            "condition_complexity",
                            item,
                            "nested ternary expression is forbidden",
                            path=path,
                            line=node.lineno,
                        )
                    )
    if issues:
        return issues
    return _pass("condition_complexity", item, f"checked {checked} conditions")


# Helpers ------------------------------------------------------------------


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _exception_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Tuple):
        names = [_exception_name(elt) for elt in node.elts]
        return ",".join(name for name in names if name)
    return ast.unparse(node) if hasattr(ast, "unparse") else type(node).__name__


def _public_functions(tree: ast.AST) -> Iterable[ast.AsyncFunctionDef | ast.FunctionDef]:
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
            "_"
        ):
            yield node


def _all_functions(tree: ast.AST) -> Iterable[ast.AsyncFunctionDef | ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _annotation_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _annotation_name(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _annotation_name(node.left) or _annotation_name(node.right)
    return None


def _function_uses_queries_or_resource(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    resource_names: set[str] = set()
    for arg in fn.args.args:
        annotation = _annotation_name(arg.annotation)
        if arg.arg in {
            "api_gateway",
            "api_gateway_control",
            "identity_admin",
            "secret_values",
            "secrets_manager",
        }:
            resource_names.add(arg.arg)
        if annotation and annotation.endswith(("Port", "Client")):
            resource_names.add(arg.arg)
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        base = _base_name(node.func.value)
        if base == "queries" or base in resource_names:
            return True
    return False


def _base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _base_name(node.value)
    return None


def _optional_runtime_dependencies(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
    names: set[str],
    suffixes: tuple[str, ...],
) -> set[str]:
    parameters = [*fn.args.posonlyargs, *fn.args.args]
    defaults = list(fn.args.defaults)
    offset = len(parameters) - len(defaults)
    result: set[str] = set()
    for index, param in enumerate(parameters):
        if index < offset:
            continue
        default = defaults[index - offset]
        if not isinstance(default, ast.Constant) or default.value is not None:
            continue
        annotation = (
            ast.unparse(param.annotation)
            if param.annotation is not None and hasattr(ast, "unparse")
            else ""
        )
        if (
            param.arg in names
            or param.arg.endswith(suffixes)
            or any(token in annotation for token in ("AsyncSession", "Port", "Client", "Admin"))
        ):
            result.add(param.arg)
    return result


def _uses_runtime_dependency(
    fn: ast.FunctionDef | ast.AsyncFunctionDef, optional: set[str]
) -> bool:
    if not optional:
        return False
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "queries":
                return True
            if isinstance(node.value, ast.Name) and node.value.id in optional:
                return True
    return False


def _load_rule_names(path: Path) -> set[str]:
    raw = json.loads(_read(path))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain entries list")
    raw_dict = cast(dict[str, Any], raw)
    entries_raw = raw_dict.get("entries")
    if not isinstance(entries_raw, list):
        raise ValueError(f"{path} must contain entries list")
    entries = cast(list[Any], entries_raw)
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"{path} contains invalid entry")
        entry_dict = cast(dict[str, Any], entry)
        name = entry_dict.get("name")
        if not isinstance(name, str):
            raise ValueError(f"{path} contains invalid entry")
        names.add(name)
    return names


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _bool_function_names(functions_path: Path) -> set[str]:
    tree = _parse_python(functions_path)
    if tree is None:
        return set()
    names: set[str] = set()
    for fn in _public_functions(tree):
        annotation = fn.returns
        if (isinstance(annotation, ast.Name) and annotation.id == "bool") or (
            isinstance(annotation, ast.Constant) and annotation.value == "bool"
        ):
            names.add(fn.name)
    return names


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


def _contains(root: ast.AST, target: ast.AST) -> bool:
    return any(node is target for node in ast.walk(root))


def _is_inside_if_test(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    child = node
    while child in parents:
        parent = parents[child]
        if isinstance(parent, ast.If):
            return parent.test is child or _contains(parent.test, child)
        child = parent
    return False


def _is_assigned_for_later_condition(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, ast.Assign):
            return any(isinstance(target, ast.Name) for target in parent.targets)
        if isinstance(parent, ast.AnnAssign):
            return isinstance(parent.target, ast.Name)
        if not isinstance(parent, ast.Await):
            return False
        current = parent
    return False


def _cyclomatic_complexity(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    complexity = 1
    for node in ast.walk(fn):
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.IfExp,
                ast.Assert,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
            ),
        ):
            complexity += 1
        elif isinstance(node, ast.Try):
            complexity += max(1, len(node.handlers))
        elif isinstance(node, ast.BoolOp):
            complexity += max(1, len(node.values) - 1)
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(node.generators)
    return complexity


def _max_control_depth(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    control = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.AsyncWith,
        ast.ExceptHandler,
        ast.Match,
    )

    def walk(node: ast.AST, depth: int) -> int:
        is_control = isinstance(node, control)
        next_depth = depth + 1 if is_control else depth
        max_depth = next_depth
        for child in ast.iter_child_nodes(node):
            max_depth = max(max_depth, walk(child, next_depth))
        return max_depth

    return max(0, walk(fn, -1))


def _bool_operator_count(node: ast.AST) -> int:
    count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.BoolOp):
            count += max(1, len(child.values) - 1)
    return count


def _ast_depth(node: ast.AST) -> int:
    children = list(ast.iter_child_nodes(node))
    if not children:
        return 1
    return 1 + max(_ast_depth(child) for child in children)


def _has_mixed_and_or(node: ast.AST) -> bool:
    ops = {type(child.op) for child in ast.walk(node) if isinstance(child, ast.BoolOp)}
    return ast.And in ops and ast.Or in ops


REGISTRY: dict[str, Checker] = {
    "rule_has_checker_tag": rule_has_checker_tag,
    "normative_no_ambiguous_words": normative_no_ambiguous_words,
    "required_paths": required_paths,
    "repo_python_policy": repo_python_policy,
    "quality_commands_declared": quality_commands_declared,
    "entrypoint_fastapi": entrypoint_fastapi,
    "health_route": health_route,
    "main_router_includes": main_router_includes,
    "entrypoint_no_provider_imports": entrypoint_no_provider_imports,
    "api_common_files": api_common_files,
    "api_domain_layout": api_domain_layout,
    "api_operation_required_files": api_operation_required_files,
    "forbid_generated_subdir_queries": forbid_generated_subdir_queries,
    "generated_queries_layout": generated_queries_layout,
    "operation_sql_dir_files": operation_sql_dir_files,
    "queries_generated_marker": queries_generated_marker,
    "router_import_api_functions_alias": router_import_api_functions_alias,
    "router_no_direct_resource_calls": router_no_direct_resource_calls,
    "router_logging_wrapper": router_logging_wrapper,
    "router_error_handling": router_error_handling,
    "router_bool_conditions": router_bool_conditions,
    "router_no_inline_business_comparison": router_no_inline_business_comparison,
    "functions_public_contract": functions_public_contract,
    "functions_vocab_names": functions_vocab_names,
    "functions_resource_usage": functions_resource_usage,
    "functions_exception_policy": functions_exception_policy,
    "managed_literals": managed_literals,
    "functions_no_provider_imports": functions_no_provider_imports,
    "sql_no_select_star": sql_no_select_star,
    "sql_first_comment_summary": sql_first_comment_summary,
    "sql_placeholders_at_names": sql_placeholders_at_names,
    "integration_port_provider_layout": integration_port_provider_layout,
    "integration_provider_boundary": integration_provider_boundary,
    "db_query_contract": db_query_contract,
    "ddl_exists": ddl_exists,
    "tools_existing_checks": tools_existing_checks,
    "python_complexity": python_complexity,
    "control_nesting_depth": control_nesting_depth,
    "function_logical_lines": function_logical_lines,
    "file_logical_lines": file_logical_lines,
    "function_argument_count": function_argument_count,
    "return_count": return_count,
    "condition_complexity": condition_complexity,
}
