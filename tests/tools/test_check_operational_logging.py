from __future__ import annotations

from pathlib import Path

from tools.check_operational_logging import main
from tools.generate_api_message_catalog import find_direct_logger_violations


def write_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_find_direct_logger_violations_reports_stdlib_logger_calls(tmp_path: Path) -> None:
    write_file(tmp_path, "src/app/core/logging.py", "")
    write_file(
        tmp_path,
        "src/app/apis/projects/list_projects/router.py",
        """
import logging

logger = logging.getLogger(__name__)


async def route() -> object:
    logger.info("direct call")
    return {}
""",
    )

    violations = find_direct_logger_violations(
        root=tmp_path,
        scan_root=tmp_path / "src/app",
        allowed_files=("src/app/core/logging.py",),
    )

    kinds = [violation.kind for violation in violations]
    assert "forbidden-import" in kinds
    assert "direct-logger-factory" in kinds
    assert "direct-logger-call" in kinds


def test_check_operational_logging_accepts_wrapper_calls(tmp_path: Path) -> None:
    write_file(tmp_path, "src/app/core/logging.py", "")
    write_file(
        tmp_path,
        "src/app/apis/projects/list_projects/router.py",
        """
from fastapi import APIRouter
from app.core.logging import get_operation_logger

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.get("/projects", operation_id="listProjects")
async def route() -> object:
    ops_logger.info("listProjects.request_succeeded")
    return {}
""",
    )
    write_file(
        tmp_path,
        "src/app/apis/projects/list_projects/message_catalog.py",
        """
MESSAGE_CATALOG = [
    {
        "message_id": "listProjects.request_succeeded",
        "level": "INFO",
        "summary": "API処理が正常終了した。",
    }
]
""",
    )

    assert main(["--root", str(tmp_path), "--fail-on-undocumented-emits", "--strict"]) == 0
