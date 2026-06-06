from __future__ import annotations

from pathlib import Path

from tools.check_router_error_response_returns import check_router_error_response_returns


def test_check_router_error_response_returns_reports_undeclared_status(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "router.py").write_text(
        """
from fastapi import APIRouter, status
from app.apis.responses import error_responses
from app.apis.router_errors import api_error_response

router = APIRouter()

@router.post("/projects", responses={**error_responses(status.HTTP_400_BAD_REQUEST)})
async def route() -> object:
    return api_error_response(status.HTTP_409_CONFLICT, "conflict")
""",
        encoding="utf-8",
    )

    issues = check_router_error_response_returns(tmp_path / "src" / "app" / "apis")

    assert [(issue.status_name, issue.line) for issue in issues] == [
        ("HTTP_409_CONFLICT", 10),
    ]


def test_check_router_error_response_returns_accepts_declared_status(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "router.py").write_text(
        """
from fastapi import APIRouter, status
from app.apis.responses import error_responses
from app.apis.router_errors import api_error_response

router = APIRouter()

@router.post("/projects", responses={**error_responses(status.HTTP_409_CONFLICT)})
async def route() -> object:
    return api_error_response(status.HTTP_409_CONFLICT, "conflict")
""",
        encoding="utf-8",
    )

    assert check_router_error_response_returns(tmp_path / "src" / "app" / "apis") == []


def test_check_router_error_response_returns_reports_exception_status(tmp_path: Path) -> None:
    api_dir = tmp_path / "src" / "app" / "apis" / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "router.py").write_text(
        """
from fastapi import APIRouter, status
from app.apis.responses import error_responses

router = APIRouter()

@router.post("/projects", responses={**error_responses(status.HTTP_400_BAD_REQUEST)})
async def route() -> object:
    try:
        return await api_functions.create_project()
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return error_response_for_router_error(error)
""",
        encoding="utf-8",
    )
    (api_dir / "functions.py").write_text(
        """
async def create_project():
    \"\"\"Project を作成する。\"\"\"
    raise ApiFunctionError(
        status.HTTP_409_CONFLICT,
        "project code is already registered",
        summary="登録対象 Project code が既に登録済みである場合。",
    )
""",
        encoding="utf-8",
    )

    issues = check_router_error_response_returns(tmp_path / "src" / "app" / "apis")

    assert [(issue.status_name, issue.line) for issue in issues] == [
        ("HTTP_409_CONFLICT", 8),
    ]
