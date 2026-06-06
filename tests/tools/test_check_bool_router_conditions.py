from __future__ import annotations

from pathlib import Path

from tools.check_bool_router_conditions import check_bool_router_conditions


def test_check_bool_router_conditions_reports_bare_await(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "functions.py").write_text(
        """
async def has_permission() -> bool:
    return True

async def get_project() -> object:
    return object()
""",
        encoding="utf-8",
    )
    (api_dir / "router.py").write_text(
        """
from app.apis.projects.create_project import functions as api_functions

async def route() -> object:
    await api_functions.has_permission()
    return await api_functions.get_project()
""",
        encoding="utf-8",
    )

    issues = check_bool_router_conditions(tmp_path / "src" / "app" / "apis")

    assert [(issue.function_name, issue.line) for issue in issues] == [("has_permission", 5)]


def test_check_bool_router_conditions_accepts_if_conditions(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "functions.py").write_text(
        """
async def has_permission() -> bool:
    return True

async def has_duplicate() -> bool:
    return False
""",
        encoding="utf-8",
    )
    (api_dir / "router.py").write_text(
        """
from app.apis.projects.create_project import functions as api_functions

async def route() -> None:
    if not await api_functions.has_permission():
        raise ValueError("forbidden")
    if await api_functions.has_duplicate():
        raise ValueError("conflict")
""",
        encoding="utf-8",
    )

    assert check_bool_router_conditions(tmp_path / "src" / "app" / "apis") == []
