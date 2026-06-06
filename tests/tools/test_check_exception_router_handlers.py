from __future__ import annotations

from pathlib import Path

from tools.check_exception_router_handlers import check_exception_router_handlers


def test_check_exception_router_handlers_reports_unhandled_calls(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "functions.py").write_text(
        """
async def validate_request() -> object:
    raise ValueError("invalid")

async def create_project() -> object:
    return await validate_request()
""",
        encoding="utf-8",
    )
    (api_dir / "router.py").write_text(
        """
from app.apis.projects.create_project import functions as api_functions

async def route() -> object:
    await api_functions.validate_request()
    return await api_functions.create_project()
""",
        encoding="utf-8",
    )

    issues = check_exception_router_handlers(tmp_path / "src" / "app" / "apis")

    assert [(issue.function_name, issue.line) for issue in issues] == [
        ("validate_request", 5),
        ("create_project", 6),
    ]


def test_check_exception_router_handlers_accepts_try_blocks(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "functions.py").write_text(
        """
async def validate_request() -> object:
    raise ValueError("invalid")
""",
        encoding="utf-8",
    )
    (api_dir / "router.py").write_text(
        """
from app.apis.projects.create_project import functions as api_functions

async def route() -> object:
    try:
        return await api_functions.validate_request()
    except ValueError:
        raise
""",
        encoding="utf-8",
    )

    assert check_exception_router_handlers(tmp_path / "src" / "app" / "apis") == []
