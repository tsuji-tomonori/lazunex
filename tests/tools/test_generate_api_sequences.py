from __future__ import annotations

import ast
from pathlib import Path

from _pytest.capture import CaptureFixture

from tools.generate_api_sequences import (
    ApiSequence,
    SequenceStep,
    SqlStep,
    api_dirs,
    api_sequence_from_dir,
    awaited_api_function_name,
    build_arg_parser,
    changed_outputs,
    endpoint_function,
    endpoint_operation_id,
    function_metadata,
    function_target,
    generate_sequences,
    integration_resource_for_target,
    integration_resources,
    is_predicate_function,
    is_router_decorator,
    literal_string,
    main,
    render_sequence_markdown,
    sql_sequence_steps,
    sql_tables,
)


def write_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_sql_tables_extracts_ordered_unique_table_names() -> None:
    source = """
SELECT projects.project_id
FROM projects
JOIN project_members ON project_members.project_id = projects.project_id;
INSERT INTO audit_events (audit_event_id) VALUES (:audit_event_id);
"""

    assert sql_tables(source) == ["projects", "project_members", "audit_events"]


def test_function_target_accepts_action_and_predicate_names() -> None:
    assert function_target("get_project") == "project"
    assert function_target("has_project_owner_permission") == "project_owner_permission"
    assert function_target("is_pending_access_request") == "pending_access_request"
    assert not is_predicate_function("get_project")
    assert is_predicate_function("has_project_owner_permission")


def test_api_sequence_from_dir_reads_router_calls_and_sql(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
    integrations_root = tmp_path / "src/app/integrations"
    api_dir = api_root / "projects/get_project"
    write_file(integrations_root, "api_gateway/port.py", "class ApiGatewayPort: ...")
    write_file(
        api_root,
        "projects/get_project/router.py",
        """
from fastapi import APIRouter
from app.apis.projects.get_project import functions as api_functions
router = APIRouter()

@router.get('/projects/{projectId}', operation_id='getProject')
async def get_project(project_id):
    project = await api_functions.get_project(project_id)
    await api_functions.has_project_view_permission(project, caller=None)
    return await api_functions.build_project_detail_response(project)
""",
    )
    write_file(
        api_root,
        "projects/get_project/functions.py",
        """
from app.apis.types import ResourceId

async def get_project(project_id: ResourceId) -> ProjectRef:
    \"\"\"プロジェクト情報を取得する。\"\"\"

async def has_project_view_permission(project: ProjectRef, caller=None) -> bool:
    \"\"\"プロジェクトを参照できるかを判定する。\"\"\"

async def build_project_detail_response(project: ProjectRef) -> GetProjectResponse:
    \"\"\"プロジェクト詳細レスポンスを組み立てる。\"\"\"
""",
    )
    write_file(
        api_root,
        "projects/get_project/sql/001_select_projects.sql",
        "SELECT projects.project_id FROM projects;",
    )

    sequence = api_sequence_from_dir(api_dir, api_root, integrations_root)

    assert sequence.domain == "projects"
    assert sequence.api == "get_project"
    assert sequence.operation_id == "getProject"
    assert sequence.steps == [
        SequenceStep(
            "get_project",
            "project",
            "プロジェクト情報を取得する。",
            ("project_id: ResourceId",),
            "ProjectRef",
        ),
        SequenceStep(
            "has_project_view_permission",
            "project_view_permission",
            "プロジェクトを参照できるかを判定する。",
            ("project: ProjectRef", "caller"),
            "bool",
        ),
        SequenceStep(
            "build_project_detail_response",
            "project_detail_response",
            "プロジェクト詳細レスポンスを組み立てる。",
            ("project: ProjectRef",),
            "GetProjectResponse",
        ),
    ]
    assert sequence.sql_steps == [
        SqlStep("001_select_projects.sql", "参照", ("projects",)),
    ]
    assert sequence.integration_resources == frozenset({"api_gateway"})


def test_render_sequence_markdown_limits_resources_and_groups_tables() -> None:
    markdown = render_sequence_markdown(
        ApiSequence(
            domain="projects",
            api="get_project",
            endpoint_name="get_project",
            operation_id="getProject",
            steps=[
                SequenceStep(
                    "get_project",
                    "project",
                    "プロジェクト情報を取得する。",
                    ("project_id: ResourceId",),
                    "ProjectRef",
                ),
                SequenceStep(
                    "create_api_gateway_api_key",
                    "api_gateway_api_key",
                    "API keyを作成する。",
                    ("project: ProjectRef",),
                    "ApiGatewayApiKeyRef",
                ),
                SequenceStep(
                    "has_project_view_permission",
                    "project_view_permission",
                    "プロジェクトを参照できるかを判定する。",
                    ("project: ProjectRef", "caller: CallerIdentity"),
                    "bool",
                ),
                SequenceStep(
                    "build_project_detail_response",
                    "project_detail_response",
                    "プロジェクト詳細レスポンスを組み立てる。",
                    ("project: ProjectRef",),
                    "GetProjectResponse",
                ),
            ],
            sql_steps=[
                SqlStep("001_select_projects.sql", "参照", ("projects", "project_members")),
                SqlStep("002_select_projects.sql", "参照", ("projects",)),
            ],
            integration_resources=frozenset({"api_gateway"}),
        )
    )

    assert "participant API as API: getProject" in markdown
    assert "participant R_project as Resource: project" not in markdown
    assert markdown.count("participant R_api_gateway as Resource: api gateway") == 1
    assert "participant R_project_view_permission" not in markdown
    assert "participant DB as DB" in markdown
    assert "participant T_projects" not in markdown
    assert "  autonumber" in markdown
    assert "API->>API: プロジェクト情報を取得する。" in markdown
    assert "引数: project_id: ResourceId" in markdown
    assert "戻り値: ProjectRef" in markdown
    assert "API->>R_api_gateway: API keyを作成する。" in markdown
    assert "alt プロジェクトを参照できるかを判定する。" in markdown
    assert (
        "API->>DB: DBを参照する"
        "(SQL: 001_select_projects.sql; テーブル: projects, project_members)"
        in markdown
    )


def test_generate_sequences_and_check_mode(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    api_root = tmp_path / "apis"
    docs_root = tmp_path / "docs/spec/40.apis"
    integrations_root = tmp_path / "integrations"
    write_file(integrations_root, "cognito/port.py", "class CognitoPort: ...")
    write_file(
        api_root,
        "apis/list_apis/router.py",
        """
from fastapi import APIRouter
from app.apis.apis.list_apis import functions as api_functions
router = APIRouter()

@router.get('/apis', operation_id='listApis')
async def list_apis(query):
    page = await api_functions.get_viewable_apis(query, caller=None)
    return await api_functions.build_api_list_response(page)
""",
    )
    write_file(
        api_root,
        "apis/list_apis/functions.py",
        """
async def get_viewable_apis(query, caller=None) -> ApiListPage:
    \"\"\"参照可能なAPI一覧を取得する。\"\"\"

async def build_api_list_response(page: ApiListPage) -> ListApisResponse:
    \"\"\"API一覧レスポンスを組み立てる。\"\"\"
""",
    )

    rendered = generate_sequences(api_root, docs_root, integrations_root)
    assert list(rendered) == [docs_root / "apis/list_apis/sequence_gen.md"]
    assert changed_outputs(rendered) == [docs_root / "apis/list_apis/sequence_gen.md"]

    assert (
        main(
            [
                "--api-root",
                str(api_root),
                "--docs-root",
                str(docs_root),
                "--integrations-root",
                str(integrations_root),
                "--check",
            ]
        )
        == 1
    )
    assert "sequence_gen.md" in capsys.readouterr().out

    assert (
        main(
            [
                "--api-root",
                str(api_root),
                "--docs-root",
                str(docs_root),
                "--integrations-root",
                str(integrations_root),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "--api-root",
                str(api_root),
                "--docs-root",
                str(docs_root),
                "--integrations-root",
                str(integrations_root),
                "--check",
            ]
        )
        == 0
    )


def test_helpers_cover_api_dirs_sql_steps_and_arg_parser(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_file(
        api_root,
        "apis/list_apis/router.py",
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/apis')
async def list_apis():
    return await api_functions.build_api_list_response(page)
""",
    )
    write_file(
        api_root,
        "apis/list_apis/sql/001_insert_audit_events.sql",
        "INSERT INTO audit_events (audit_event_id) VALUES (:audit_event_id);",
    )

    assert api_dirs(api_root) == [api_root / "apis/list_apis"]
    assert sql_sequence_steps(api_root / "apis/list_apis/sql") == [
        SqlStep("001_insert_audit_events.sql", "追加", ("audit_events",))
    ]
    assert build_arg_parser().parse_args([]).docs_root == Path("docs/spec/40.apis")


def test_function_metadata_reads_docstrings_arguments_and_return_types(
    tmp_path: Path,
) -> None:
    functions_path = write_file(
        tmp_path,
        "functions.py",
        """
async def get_project(project_id: ResourceId, *, caller: CallerIdentity) -> ProjectRef:
    \"\"\"プロジェクト情報を取得する。\"\"\"

def helper() -> None:
    \"\"\"privateではない同期helperも読み取る。\"\"\"

async def _internal_helper(value: str) -> str:
    return value
""",
    )

    metadata = function_metadata(functions_path)

    assert metadata["get_project"].description == "プロジェクト情報を取得する。"
    assert metadata["get_project"].arguments == (
        "project_id: ResourceId",
        "caller: CallerIdentity",
    )
    assert metadata["get_project"].return_type == "ProjectRef"
    assert "_internal_helper" not in metadata


def test_function_metadata_requires_docstrings(tmp_path: Path) -> None:
    functions_path = write_file(
        tmp_path,
        "functions.py",
        """
async def get_project() -> ProjectRef:
    return project
""",
    )

    try:
        function_metadata(functions_path)
    except ValueError as error:
        assert str(error) == "get_project docstring is not found"
    else:
        raise AssertionError("function_metadata should reject functions without docstrings")


def test_integration_resources_are_loaded_from_port_directories(tmp_path: Path) -> None:
    integrations_root = tmp_path / "integrations"
    write_file(integrations_root, "api_gateway/port.py", "class ApiGatewayPort: ...")
    write_file(integrations_root, "cognito/schemas.py", "class CognitoSchema: ...")
    write_file(integrations_root, "secrets_manager/port.py", "class SecretsManagerPort: ...")

    resources = integration_resources(integrations_root)

    assert resources == frozenset({"api_gateway", "secrets_manager"})
    assert integration_resource_for_target("api_gateway_api_key", resources) == "api_gateway"
    assert integration_resource_for_target("secrets_manager_secret", resources) == "secrets_manager"
    assert integration_resource_for_target("project", resources) is None


def test_ast_helpers_handle_non_matches_and_fallbacks() -> None:
    assert literal_string(ast.parse("value", mode="eval").body) is None
    assert not is_router_decorator(ast.parse("router.get", mode="eval").body)
    assert not is_router_decorator(ast.parse("other.get('/apis')", mode="eval").body)

    tree = ast.parse(
        """
def helper():
    return None
"""
    )
    try:
        endpoint_function(tree)
    except ValueError as error:
        assert str(error) == "router endpoint function is not found"
    else:
        raise AssertionError("endpoint_function should reject modules without router endpoints")

    router_tree = ast.parse(
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/apis')
async def list_apis():
    return []
"""
    )
    assert endpoint_operation_id(endpoint_function(router_tree)) == "list_apis"


def test_awaited_api_function_name_rejects_unrelated_awaits() -> None:
    tree = ast.parse(
        """
async def endpoint():
    value
    await value
    await other_functions.get_project()
    await api_functions()
    await api_functions.get_project()
"""
    )
    expressions = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
    ]

    assert [awaited_api_function_name(expression) for expression in expressions] == [
        None,
        None,
        None,
        None,
        "get_project",
    ]


def test_sql_sequence_steps_ignores_missing_or_unparseable_sql(tmp_path: Path) -> None:
    assert sql_sequence_steps(tmp_path / "missing") == []

    sql_dir = tmp_path / "sql"
    write_file(sql_dir, "001_select_literal.sql", "SELECT 1;")

    assert sql_sequence_steps(sql_dir) == []
