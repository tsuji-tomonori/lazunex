from pathlib import Path

from tools.generate_api_detail_design import (
    api_detail_design_from_dir,
    generate_detail_designs,
    render_detail_design_markdown,
)


def write_api_files(api_dir: Path, api_root: Path) -> None:
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_root / "router_errors.py").write_text(
        "ROUTER_HANDLED_EXCEPTIONS = (ApiFunctionError,)\n",
        encoding="utf-8",
    )
    (api_dir / "router.py").write_text(
        """
from typing import Annotated
from fastapi import APIRouter, Body, Header, Path, status

router = APIRouter()

@router.post(
    "/projects/{projectId}/widgets",
    operation_id="createWidget",
    response_model=CreateWidgetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_widget(
    project_id: Annotated[ResourceId, Path(alias="projectId", description="Project ID")],
    request: Annotated[CreateWidgetRequest, Body()],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
):
    try:
        if not await api_functions.has_permission(project_id):
            return api_error_response(status.HTTP_403_FORBIDDEN, "forbidden")
        widget = await api_functions.save_widget(project_id, request, caller, session)
        external = await api_functions.create_external_widget(request, widget)
        return await api_functions.build_create_widget_response(widget, external)
    except SQLAlchemyError:
        return api_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "database commit failed")
""",
        encoding="utf-8",
    )
    (api_dir / "schemas.py").write_text(
        """
from pydantic import Field
from app.apis.base import ApiBaseModel

class WidgetSettingsRequest(ApiBaseModel):
    enabled: bool = Field(description="Widgetを有効化するかどうかです。")

class CreateWidgetRequest(ApiBaseModel):
    name: str = Field(description="Widget名です。")
    settings: WidgetSettingsRequest = Field(description="Widget設定です。")

class CreateWidgetResponse(ApiBaseModel):
    widget_id: str = Field(description="Widget IDです。")
    name: str = Field(description="Widget名です。")
    external_id: str = Field(description="外部リソースIDです。")
""",
        encoding="utf-8",
    )
    (api_dir / "queries.py").write_text(
        """
from pathlib import Path
from pydantic import BaseModel

SQL_DIR = Path(__file__).with_name("sql")

class InsertWidgetsParams(BaseModel):
    widget_id: str
    project_id: str
    name: str
    aggregate_id: str
    actor_principal_id: str

async def insert_widgets(session, params: InsertWidgetsParams) -> None:
    \"\"\"Widgetを保持するため、Widgetを追加する。\"\"\"
    await execute_sql(session, SQL_DIR / "001_insert_widgets.sql", params)
""",
        encoding="utf-8",
    )
    (api_dir / "sql").mkdir()
    (api_dir / "sql/001_insert_widgets.sql").write_text(
        """
INSERT INTO widgets (
    widget_id,
    project_id,
    name,
    event_seq,
    created_by,
    row_version
) VALUES (
    @widget_id,
    @project_id,
    @name,
    COALESCE((
        SELECT MAX(event_seq) + 1
        FROM widgets
        WHERE aggregate_id = @aggregate_id
    ), 1),
    @actor_principal_id,
    1
);
""",
        encoding="utf-8",
    )
    (api_dir / "functions.py").write_text(
        """
from uuid import uuid4

async def has_permission(project_id):
    \"\"\"呼び出し元がWidgetを作成できるかを判定する。\"\"\"
    return True

async def save_widget(project_id, request, caller, session):
    widget_id = uuid4()
    await queries.insert_widgets(
        session,
        queries.InsertWidgetsParams(
            widget_id=widget_id,
            project_id=project_id,
            name=request.name,
            aggregate_id=project_id,
            actor_principal_id=caller.principal_id,
        ),
    )
    return WidgetRef(widget_id=widget_id, name=request.name)

async def create_external_widget(request, widget):
    return await client.create_widget(
        CreateWidgetInput(name=request.name, widget_id=widget.widget_id)
    )

async def build_create_widget_response(widget, external):
    return CreateWidgetResponse(
        widget_id=widget.widget_id,
        name=widget.name,
        external_id=external.external_id,
    )
""",
        encoding="utf-8",
    )


def test_api_detail_design_extracts_normal_flow_details(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
    api_dir = api_root / "projects/create_widget"
    docs_root = tmp_path / "docs/spec/40.apis"
    ddl_path = tmp_path / "src/db/ddl.sql"
    ddl_path.parent.mkdir(parents=True)
    ddl_path.write_text(
        """
CREATE TABLE widgets (
    widget_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_seq INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    row_version INTEGER NOT NULL
);

-- COMMENT ON COLUMN widgets.widget_id IS 'Widget ID。';
-- COMMENT ON COLUMN widgets.project_id IS 'Project ID。';
-- COMMENT ON COLUMN widgets.name IS 'Widget名。';
-- COMMENT ON COLUMN widgets.event_seq IS 'Widgetごとのイベント連番。';
-- COMMENT ON COLUMN widgets.created_by IS '作成者。';
-- COMMENT ON COLUMN widgets.row_version IS '行バージョン。';
""",
        encoding="utf-8",
    )
    write_api_files(api_dir, api_root)

    doc = api_detail_design_from_dir(api_dir, api_root)
    content = render_detail_design_markdown(doc)
    rendered = generate_detail_designs(api_root, docs_root, ddl_path)
    generated_content = rendered[docs_root / "projects/create_widget/detail-design_gen.md"]

    assert generated_content != content
    assert "| `body` | `request` | `CreateWidgetRequest` | - |" in content
    assert "| `settings.enabled` | `bool` | Widgetを有効化するかどうかです。 |" in content
    assert "条件分岐: 呼び出し元がWidgetを作成できない場合。: 不成立" in content
    assert "### DB `widgets` 作成" in content
    assert "| `name` | Widget名。 | `name` | request.body.name |" in generated_content
    assert (
        "| `created_by` | 作成者。 | `actor_principal_id` | "
        "認証主体: caller.principalId |"
    ) in generated_content
    assert (
        "| `event_seq` | Widgetごとのイベント連番。 | `※1` | "
        "※1 SQL式: 取得元 DB: widgets.aggregate_id |"
    ) in generated_content
    assert "取得元 DB: widgets.event_seq" not in generated_content
    assert "SELECT MAX(event_seq) + 1 FROM widgets WHERE aggregate_id = $aggregate_id" in (
        generated_content
    )
    assert "| `row_version` | 行バージョン。 | `1` | SQL式: 1 |" in generated_content
    assert "### 外部リソース `CreateWidgetInput`" in content
    assert "| `widgetId` | widget.widget_id |" in generated_content
    assert "| `externalId` | 外部リソースIDです。 | external.external_id |" in content
