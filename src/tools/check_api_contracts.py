from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from tools.generate_api_sequences import endpoint_function, endpoint_operation_id

DEFAULT_API_ROOT = Path("src/app/apis")


@dataclass(frozen=True)
class ContractMetadata:
    operation_id: str
    markdown_slug: str
    auth_mode: str
    business_summary: str
    permissions: tuple[str, ...]


@dataclass(frozen=True)
class ContractIssue:
    path: Path
    message: str


def literal_string_tuple(node: ast.AST | None) -> tuple[str, ...] | None:
    if node is None:
        return ()
    if isinstance(node, ast.Tuple):
        values: list[str] = []
        for item in node.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                return None
            values.append(item.value)
        return tuple(values)
    return None


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def contract_call(tree: ast.Module) -> ast.Call | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "CONTRACT" for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Call):
            return node.value
    return None


def contract_metadata(path: Path) -> ContractMetadata | ContractIssue:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return ContractIssue(path, f"cannot parse contract.py: {exc}")
    call = contract_call(tree)
    if call is None:
        return ContractIssue(path, "CONTRACT assignment is missing")
    values = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg is not None}
    operation_id = literal_string(values.get("operation_id"))
    markdown_slug = literal_string(values.get("markdown_slug"))
    auth_mode = literal_string(values.get("auth_mode"))
    business_summary = literal_string(values.get("business_summary"))
    permissions = literal_string_tuple(values.get("permissions"))
    fields = (
        ("operation_id", operation_id),
        ("markdown_slug", markdown_slug),
        ("auth_mode", auth_mode),
        ("business_summary", business_summary),
        ("permissions", permissions),
    )
    missing = [name for name, value in fields if value is None]
    if missing:
        return ContractIssue(
            path, "CONTRACT literal field is missing or invalid: " + ", ".join(missing)
        )
    if (
        operation_id is None
        or markdown_slug is None
        or auth_mode is None
        or business_summary is None
        or permissions is None
    ):
        raise AssertionError("unreachable: missing fields were checked")
    if business_summary == "":
        return ContractIssue(path, "CONTRACT business_summary must not be empty")
    return ContractMetadata(
        operation_id=operation_id,
        markdown_slug=markdown_slug,
        auth_mode=auth_mode,
        business_summary=business_summary,
        permissions=permissions,
    )


def router_operation_id(path: Path) -> str | ContractIssue:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return ContractIssue(path, f"cannot parse router.py: {exc}")
    try:
        return endpoint_operation_id(endpoint_function(tree))
    except ValueError as exc:
        return ContractIssue(path, str(exc))


def operation_dirs(api_root: Path) -> tuple[Path, ...]:
    if not api_root.exists():
        return ()
    return tuple(
        sorted(path.parent for path in api_root.glob("*/*/router.py") if path.parent.is_dir())
    )


def issues_for_operation(api_dir: Path, api_root: Path) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    contract_path = api_dir / "contract.py"
    router_path = api_dir / "router.py"
    if not contract_path.exists():
        return [ContractIssue(contract_path, "contract.py is missing")]
    contract = contract_metadata(contract_path)
    if isinstance(contract, ContractIssue):
        return [contract]
    operation_id = router_operation_id(router_path)
    if isinstance(operation_id, ContractIssue):
        return [operation_id]
    if contract.operation_id != operation_id:
        issues.append(
            ContractIssue(
                contract_path,
                f"operation_id {contract.operation_id!r} does not match router {operation_id!r}",
            )
        )
    expected_slug = api_dir.relative_to(api_root).as_posix()
    if contract.markdown_slug != expected_slug:
        issues.append(
            ContractIssue(
                contract_path,
                f"markdown_slug {contract.markdown_slug!r} does not match {expected_slug!r}",
            )
        )
    if contract.auth_mode not in {"management-bearer", "public", "none"}:
        issues.append(
            ContractIssue(
                contract_path,
                f"auth_mode {contract.auth_mode!r} is not supported",
            )
        )
    return issues


def check_contracts(api_root: Path = DEFAULT_API_ROOT) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    for api_dir in operation_dirs(api_root):
        issues.extend(issues_for_operation(api_dir, api_root))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-root", type=Path, default=DEFAULT_API_ROOT)
    args = parser.parse_args()
    issues = check_contracts(args.api_root)
    for issue in issues:
        print(f"{issue.path}: {issue.message}")
    if issues:
        return 1
    print("All API contracts match routers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
