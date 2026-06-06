from __future__ import annotations

from pathlib import Path

from tools.generate_api_message_catalog import (
    build_api_catalogs,
    main,
    render_catalog,
    render_index,
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
        catalog_id="M001",
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
        "id": "M001",
        "message_id": "listProjects.request_succeeded",
        "level": "INFO",
        "summary": "API処理が正常終了した。",
        "when": "2xx responseを返す直前。",
        "context_model": "traceId, api.statusCode, error.code",
    }
]
""",
    )

    catalogs = build_api_catalogs(root=tmp_path, api_root=api_root, include_http_defaults=False)

    assert len(catalogs) == 1
    catalog = catalogs[0]
    assert catalog.meta.operation_id == "listProjects"
    assert catalog.messages[0].catalog_id == "M001"
    assert catalog.wrapper_calls[0].message_id == "listProjects.request_succeeded"
    assert catalog.wrapper_calls[0].level_hint == "INFO"
    assert validate_catalogs(
        catalogs,
        strict=True,
        fail_on_undocumented_emits=True,
        fail_on_missing_message_id=True,
        fail_on_missing_catalog_id=True,
        fail_on_level_mismatch=True,
        require_api_wrapper_calls=True,
    ) == []
    rendered = render_catalog(catalog, tmp_path)
    header = "| id | message_id | ログ概要 |"
    assert header in rendered
    assert (
        "`M001` | `listProjects.request_succeeded` | API処理が正常終了した。"
        in rendered
    )
    assert "## ログ詳細" in rendered
    assert "### `M001` `listProjects.request_succeeded`" in rendered
    assert "| level | `INFO` |" in rendered
    assert "| wrapper calls | 1 |" in rendered
    assert "| 出力項目 |" not in rendered.split("#### 出力項目", maxsplit=1)[0]
    assert "#### 出力項目" in rendered
    assert "| `api.statusCode` | API responseとして返したHTTP status codeです。 |" in rendered
    assert "| `error.code` | エラー分類を表す機械処理向けコードです。 |" in rendered


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


def test_build_api_catalogs_reads_warning_messages_from_router_logger_call(
    tmp_path: Path,
) -> None:
    api_root = tmp_path / "src/app/apis"
    write_file(
        tmp_path,
        "src/app/apis/projects/list_projects/router.py",
        """
from fastapi import APIRouter, status
from app.core.logging import get_operation_logger

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.get("/projects", operation_id="listProjects")
async def route() -> object:
    if not await api_functions.has_project_list_permission(caller):
        ops_logger.warning(
            "listProjects.caller_cannot_list_projects",
            catalog_id="M001",
            summary="呼び出し元がProject一覧を参照できないため、リクエストを拒否した。",
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot list projects",
            when="呼び出し元が Project 一覧を参照できない場合。",
            why_production="Project一覧の認可拒否を運用で追跡するため。",
            context_model="traceId, actorPrincipalId, api.statusCode, error.code, error.message",
            operator_action="actorPrincipalIdと認可条件を確認する。",
            runbook="RUNBOOK-authorization-forbidden",
            context={"api": {"statusCode": status.HTTP_403_FORBIDDEN}},
        )
        return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot list projects")
    return {}
""",
    )
    write_file(
        tmp_path,
        "src/app/apis/projects/list_projects/functions.py",
        """
async def has_project_list_permission(caller) -> bool:
    \"\"\"呼び出し元が Project 一覧を参照できるかを判定する。\"\"\"
""",
    )

    catalogs = build_api_catalogs(root=tmp_path, api_root=api_root, include_http_defaults=True)

    message_refs = [
        (message.catalog_id, message.message_id, message.level)
        for message in catalogs[0].messages
    ]
    assert message_refs == [
        ("M001", "listProjects.caller_cannot_list_projects", "WARNING")
    ]
    assert validate_catalogs(
        catalogs,
        strict=True,
        fail_on_undocumented_emits=True,
        fail_on_missing_message_id=True,
        fail_on_missing_catalog_id=True,
        fail_on_level_mismatch=True,
        require_api_wrapper_calls=True,
    ) == []
    rendered = render_catalog(catalogs[0], tmp_path)
    assert "呼び出し元が Project 一覧を参照できない場合。" in rendered
    assert "RUNBOOK-authorization-forbidden" in rendered

    index = render_index(catalogs, tmp_path / "docs/spec/40.apis", "messages_gen.md", tmp_path)
    assert "`M001` | `listProjects.caller_cannot_list_projects` | `WARNING` | 403" in index
