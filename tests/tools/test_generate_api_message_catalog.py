from __future__ import annotations

from pathlib import Path

from tools.generate_api_message_catalog import (
    build_api_catalogs,
    main,
    render_catalog,
    validate_catalogs,
)


def write_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_build_api_catalogs_reads_catalog_and_wrapper_calls(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
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
    ops_logger.info(
        "listProjects.request_succeeded",
        context={"api": {"method": "GET", "route": "/projects", "statusCode": 200}},
    )
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
        "when": "2xx responseを返す直前。",
    }
]
""",
    )

    catalogs = build_api_catalogs(root=tmp_path, api_root=api_root, include_http_defaults=False)

    assert len(catalogs) == 1
    catalog = catalogs[0]
    assert catalog.meta.operation_id == "listProjects"
    assert catalog.wrapper_calls[0].message_id == "listProjects.request_succeeded"
    assert catalog.wrapper_calls[0].level_hint == "INFO"
    assert validate_catalogs(
        catalogs,
        strict=True,
        fail_on_undocumented_emits=True,
        fail_on_missing_message_id=True,
        fail_on_level_mismatch=True,
        require_api_wrapper_calls=True,
    ) == []
    assert "`listProjects.request_succeeded`" in render_catalog(catalog, tmp_path)


def test_generate_api_message_catalog_main_writes_and_checks_docs(tmp_path: Path) -> None:
    write_file(
        tmp_path,
        "src/app/apis/projects/list_projects/router.py",
        """
from fastapi import APIRouter

router = APIRouter()


@router.get("/projects", operation_id="listProjects")
async def route() -> object:
    return {}
""",
    )

    args = ["--root", str(tmp_path), "--docs-root", "docs/spec/40.apis"]

    assert main(args) == 0
    assert (tmp_path / "docs/spec/40.apis/projects/list_projects/messages_gen.md").exists()
    assert (tmp_path / "docs/spec/40.apis/messages_index_gen.md").exists()
    assert main([*args, "--check"]) == 0
