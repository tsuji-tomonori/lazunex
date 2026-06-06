from __future__ import annotations

from pathlib import Path

from tools.check_api_router_ignored_returns import check_api_router_ignored_returns


def write_api(tmp_path: Path, *, router: str, functions: str) -> Path:
    api_dir = tmp_path / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "router.py").write_text(router, encoding="utf-8")
    (api_dir / "functions.py").write_text(functions, encoding="utf-8")
    return api_dir


def test_reports_ignored_meaningful_return_and_read_side_effect(tmp_path: Path) -> None:
    api_dir = write_api(
        tmp_path,
        router="""
async def route():
    await api_functions.get_idempotency_record("key")
    await api_functions.append_audit_event()
""",
        functions="""
async def get_idempotency_record() -> IdempotencyRecordRef:
    return IdempotencyRecordRef()

async def append_audit_event() -> EventRef:
    return EventRef()

async def verify_api_gateway_stage_registration() -> bool:
    await api_gateway_control.update_method()
    return True
""",
    )

    issues = check_api_router_ignored_returns(tmp_path)

    assert [(issue.path, issue.function_name, issue.message) for issue in issues] == [
        (
            api_dir / "functions.py",
            "verify_api_gateway_stage_registration",
            "read/check/build function must not perform mutating side effects",
        ),
        (
            api_dir / "router.py",
            "get_idempotency_record",
            "api_functions return value must be used or the function must be side-effect-only",
        ),
    ]


def test_accepts_used_returns_and_named_side_effects(tmp_path: Path) -> None:
    write_api(
        tmp_path,
        router="""
async def route():
    record = await api_functions.get_idempotency_record("key")
    if record.operation_id:
        return None
    await api_functions.append_audit_event()
""",
        functions="""
async def get_idempotency_record() -> IdempotencyRecordRef:
    return IdempotencyRecordRef()

async def append_audit_event() -> EventRef:
    await queries.insert_audit_events()
    return EventRef()

async def update_api_gateway_stage_registration() -> bool:
    await api_gateway_control.update_method()
    return True
""",
    )

    assert check_api_router_ignored_returns(tmp_path) == []
