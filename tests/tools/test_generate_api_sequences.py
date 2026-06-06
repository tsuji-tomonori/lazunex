from __future__ import annotations

import ast
from pathlib import Path

from _pytest.capture import CaptureFixture

from tools.generate_api_sequences import (
    ApiSequence,
    ErrorReturnStep,
    FunctionErrorMetadata,
    FunctionMetadata,
    SequenceStep,
    SqlStep,
    SuccessReturnStep,
    api_dirs,
    api_sequence_from_dir,
    awaited_api_function_name,
    build_arg_parser,
    changed_outputs,
    endpoint_error_returns,
    endpoint_exception_error_returns,
    endpoint_function,
    endpoint_operation_id,
    endpoint_route_method,
    endpoint_route_path,
    endpoint_sequence_items,
    endpoint_status_codes,
    function_metadata,
    function_target,
    generate_sequences,
    http_status_code_label,
    imported_integration_ports,
    integration_resource_for_target,
    integration_resources,
    is_predicate_function,
    is_router_decorator,
    literal_string,
    main,
    query_sql_filenames,
    query_sql_filenames_for_step,
    query_sql_summaries,
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
    if not await api_functions.has_project_owner_permission(project, caller=None):
        return api_error_response(status.HTTP_403_FORBIDDEN, 'caller cannot view project')
    return await api_functions.build_project_detail_response(project)
""",
    )
    write_file(
        api_root,
        "projects/get_project/functions.py",
        """
from app.apis.types import ResourceId
from app.apis.projects.get_project import queries

async def get_project(project_id: ResourceId) -> ProjectRef:
    \"\"\"プロジェクト情報を取得する。\"\"\"
    return await queries.select_projects(session, params)

async def has_project_view_permission(project: ProjectRef, caller=None) -> bool:
    \"\"\"プロジェクトを参照できるかを判定する。\"\"\"

async def has_project_owner_permission(project: ProjectRef, caller=None) -> bool:
    \"\"\"呼び出し元が Project owner であるかを判定する。\"\"\"

async def build_project_detail_response(project: ProjectRef) -> GetProjectResponse:
    \"\"\"プロジェクト詳細レスポンスを組み立てる。\"\"\"
""",
    )
    write_file(
        api_root,
        "projects/get_project/sql/001_select_projects.sql",
        "-- Project 詳細表示に必要な Project レコードを取得する。\n"
        "SELECT projects.project_id FROM projects;",
    )
    write_file(
        api_root,
        "projects/get_project/queries.py",
        """
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

SQL_DIR = Path(__file__).with_name("sql")

async def select_projects(session: AsyncSession, params):
    \"\"\"Project 詳細表示に必要な Project レコードを取得する。\"\"\"
    return await fetch_all(session, SQL_DIR / "001_select_projects.sql", params, Row)
""",
    )

    sequence = api_sequence_from_dir(api_dir, api_root, integrations_root)

    assert sequence.domain == "projects"
    assert sequence.api == "get_project"
    assert sequence.operation_id == "getProject"
    assert sequence.method == "GET"
    assert sequence.path == "/projects/{projectId}"
    assert sequence.status_codes == (200,)
    assert sequence.steps == [
        SequenceStep(
            "get_project",
            "project",
            "プロジェクト情報を取得する。",
            ("project_id ResourceId",),
            "ProjectRef",
            (),
            ("select_projects",),
        ),
        SequenceStep(
            "has_project_view_permission",
            "project_view_permission",
            "プロジェクトを参照できるかを判定する。",
            ("project ProjectRef", "caller"),
            "bool",
        ),
        SequenceStep(
            "has_project_owner_permission",
            "project_owner_permission",
            "呼び出し元が Project owner であるかを判定する。",
            ("project ProjectRef", "caller"),
            "bool",
            condition_label="呼び出し元が Project owner である場合。",
        ),
        SequenceStep(
            "build_project_detail_response",
            "project_detail_response",
            "プロジェクト詳細レスポンスを組み立てる。",
            ("project ProjectRef",),
            "GetProjectResponse",
        ),
    ]
    assert sequence.error_returns == [
        ErrorReturnStep(
            403,
            "呼び出し元が Project owner でない場合。",
            "caller cannot view project",
        )
    ]
    assert [success.status_code for success in sequence.success_returns] == [200]
    assert sequence.sql_steps == [
        SqlStep(
            "001_select_projects.sql",
            "参照",
            ("projects",),
            "Project 詳細表示に必要な Project レコードを取得する。",
        ),
    ]
    assert sequence.integration_resources == frozenset({"api_gateway"})


def test_function_metadata_reads_called_integration_resources(tmp_path: Path) -> None:
    functions_path = write_file(
        tmp_path,
        "functions.py",
        """
from app.integrations.identity.port import IdentityAdminPort

async def update_cognito_app_client(identity_admin: IdentityAdminPort) -> ClientRef:
    \"\"\"Cognito App Client を更新する。\"\"\"
    return await identity_admin.update_user_pool_client(request)
""",
    )
    tree = ast.parse(functions_path.read_text(encoding="utf-8"))

    assert imported_integration_ports(tree) == {"IdentityAdminPort": "identity"}
    assert function_metadata(functions_path)["update_cognito_app_client"].integration_resources == (
        "identity",
    )


def test_query_sql_filenames_maps_called_query_to_sql(tmp_path: Path) -> None:
    queries_path = write_file(
        tmp_path,
        "queries.py",
        """
from pathlib import Path

SQL_DIR = Path(__file__).with_name("sql")

async def select_projects(session, params):
    return await fetch_all(session, SQL_DIR / "001_select_projects.sql", params, Row)
""",
    )

    assert query_sql_filenames(queries_path) == {"select_projects": "001_select_projects.sql"}


def test_endpoint_route_metadata_reads_path_method_and_responses() -> None:
    tree = ast.parse(
        """
@router.post(
    '/apis',
    operation_id='publishApi',
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {},
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    },
)
async def publish_api():
    return {}
"""
    )
    function = endpoint_function(tree)

    assert endpoint_route_method(function) == "POST"
    assert endpoint_route_path(function) == "/apis"
    assert endpoint_status_codes(function) == (201, 401, 422, 429, 500, 400, 409, 503)
    assert http_status_code_label(400) == "HTTP 400 Bad Request"


def test_endpoint_error_returns_reads_router_error_schema_returns() -> None:
    tree = ast.parse(
        """
async def get_project():
    if not await api_functions.has_project_view_permission(project, caller):
        return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot view project")
    if await api_functions.has_project_conflict(project):
        return api_error_response(status.HTTP_409_CONFLICT, "project is already updated")
    if not await api_functions.verify_project_registration(project):
        return api_error_response(status.HTTP_502_BAD_GATEWAY, "project registration is not valid")
"""
    )
    metadata = {
        "has_project_view_permission": FunctionMetadata(
            "呼び出し元が Project 詳細を参照できるかを判定する。",
            (),
            "bool",
        ),
        "has_project_conflict": FunctionMetadata(
            "Project の更新競合が存在するかを判定する。",
            (),
            "bool",
        ),
        "verify_project_registration": FunctionMetadata(
            "Project の登録情報を検証する。",
            (),
            "bool",
        ),
    }
    function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef))

    assert endpoint_error_returns(function, metadata) == [
        ErrorReturnStep(
            403,
            "呼び出し元が Project 詳細を参照できない場合。",
            "caller cannot view project",
        ),
        ErrorReturnStep(
            409,
            "Project の更新競合が存在する場合。",
            "project is already updated",
        ),
        ErrorReturnStep(
            502,
            "Project の登録情報を検証できない場合。",
            "project registration is not valid",
        ),
    ]


def test_endpoint_exception_error_returns_reads_api_function_error_summaries() -> None:
    steps = [
        SequenceStep(
            "validate_request",
            "request",
            "リクエストを検証する。",
        )
    ]
    metadata = {
        "validate_request": FunctionMetadata(
            "リクエストを検証する。",
            (),
            "Request",
            errors=(
                FunctionErrorMetadata(
                    400,
                    "requested_reason must not be blank",
                    "requestedReason が空白である場合。",
                ),
            ),
        )
    }

    assert endpoint_exception_error_returns(steps, metadata) == [
        ErrorReturnStep(
            400,
            "requestedReason が空白である場合。",
            "requested_reason must not be blank",
        )
    ]


def test_endpoint_sequence_items_reads_router_error_handler_as_500() -> None:
    tree = ast.parse(
        """
async def create_project():
    try:
        project = await api_functions.create_project()
        return await api_functions.build_project_response(project)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return error_response_for_router_error(error)
"""
    )
    function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef))
    metadata = {
        "create_project": FunctionMetadata(
            "Project を作成する。",
            (),
            "ProjectRef",
        ),
        "build_project_response": FunctionMetadata(
            "Project 作成レスポンスを組み立てる。",
            (),
            "CreateProjectResponse",
        ),
    }

    assert endpoint_sequence_items(function, metadata, 201) == [
        SequenceStep("create_project", "project", "Project を作成する。", (), "ProjectRef"),
        SequenceStep(
            "build_project_response",
            "project_response",
            "Project 作成レスポンスを組み立てる。",
            (),
            "CreateProjectResponse",
        ),
        SuccessReturnStep(201),
        ErrorReturnStep(
            500,
            "Router で捕捉した例外を error response に変換する場合。",
            "internal server error",
        ),
    ]


def test_endpoint_route_metadata_handles_defaults_keyword_path_and_unknown_status() -> None:
    tree = ast.parse(
        """
@tracer.wrap()
@router.get(
    path='/health',
    status_code=202,
    responses={
        418: {},
        status.HTTP_OK: {},
        **responses.error_responses(status.HTTP_404_NOT_FOUND),
    },
)
async def health():
    return {}
"""
    )
    function = endpoint_function(tree)

    assert endpoint_operation_id(function) == "health"
    assert endpoint_route_method(function) == "GET"
    assert endpoint_route_path(function) == "/health"
    assert endpoint_status_codes(function) == (202, 418, 401, 422, 429, 500, 404)
    assert http_status_code_label(418) == "HTTP 418"

    fallback_tree = ast.parse(
        """
@router.get()
async def fallback():
    return {}
"""
    )
    fallback_function = endpoint_function(fallback_tree)

    assert endpoint_route_path(fallback_function) == "/"
    assert endpoint_status_codes(fallback_function) == (200,)


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
                    ("project_id ResourceId",),
                    "ProjectRef",
                    query_functions=("select_projects",),
                ),
                SequenceStep(
                    "create_api_gateway_api_key",
                    "api_gateway_api_key",
                    "API keyを作成する。",
                    ("project ProjectRef",),
                    "ApiGatewayApiKeyRef",
                    ("api_gateway_control",),
                ),
                SequenceStep(
                    "has_project_view_permission",
                    "project_view_permission",
                    "プロジェクトを参照できるかを判定する。",
                    ("project ProjectRef", "caller CallerIdentity"),
                    "bool",
                    query_functions=("select_projects",),
                ),
                SequenceStep(
                    "append_project_created_event",
                    "project_created_event",
                    "Project 作成イベントを追記する。",
                    ("project ProjectRef",),
                    "EventRef",
                    query_functions=("insert_project_events",),
                ),
                SequenceStep(
                    "build_project_detail_response",
                    "project_detail_response",
                    "プロジェクト詳細レスポンスを組み立てる。",
                    ("project ProjectRef",),
                    "GetProjectResponse",
                ),
            ],
            error_returns=[
                ErrorReturnStep(
                    403,
                    "呼び出し元が Project 詳細を参照できない場合。",
                    "caller cannot view project",
                )
            ],
            sql_steps=[
                SqlStep(
                    "001_select_projects.sql",
                    "参照",
                    ("projects", "project_members"),
                    "Project 詳細表示に必要な Project と member を取得する。",
                ),
                SqlStep(
                    "003_insert_project_events.sql",
                    "追加",
                    ("project_events",),
                    "Project 作成の処理結果として、Project eventを追加する。",
                ),
            ],
            integration_resources=frozenset({"api_gateway", "api_gateway_control"}),
            method="GET",
            path="/projects/{projectId}",
            status_codes=(200, 404),
        )
    )

    assert "participant API as API" in markdown
    assert "participant User as User" in markdown
    assert "User->>API: GET /projects/{projectId}" in markdown
    assert "participant R_project as Resource: project" not in markdown
    assert "participant R_api_gateway as Resource: api gateway" not in markdown
    assert "participant R_api_gateway_control as Resource: api gateway control" in markdown
    assert "participant R_project_view_permission" not in markdown
    assert "participant DB as DB" in markdown
    assert "participant T_projects" not in markdown
    assert "  autonumber" in markdown
    assert "API->>API: プロジェクト情報を取得する。" not in markdown
    assert (
        "API->>DB: プロジェクト情報を取得する。"
        "<br/>SQL 001_select_projects.sql<br/>テーブル projects, project_members" in markdown
    )
    assert "API->>R_api_gateway_control: API keyを作成する。" in markdown
    assert "alt プロジェクトを参照できる場合。" in markdown
    assert "API->>API: プロジェクトを参照できるかを判定する。" not in markdown
    assert "    API->>API: プロジェクト詳細レスポンスを組み立てる。" in markdown
    assert (
        "API->>API: Project 作成イベントを追記する。" not in markdown
    )
    assert (
        "API->>DB: Project 作成イベントを追記する。"
        "<br/>SQL 003_insert_project_events.sql<br/>テーブル project_events" in markdown
    )
    assert markdown.index("API->>DB: Project 作成イベントを追記する。") < markdown.index(
        "SQL 003_insert_project_events.sql"
    )
    assert "API-->>User: HTTP 200 OK" not in markdown
    assert "alt 呼び出し元が Project 詳細を参照できない場合。" in markdown
    assert "API-->>User: HTTP 403 Forbidden<br/>caller cannot view project" in markdown
    assert "API-->>User: HTTP 404 Not Found" not in markdown
    assert markdown.rstrip().endswith("  end\n```")


def test_query_sql_filenames_for_step_matches_query_function_suffix() -> None:
    step = SequenceStep(
        "append_project_created_event",
        "project_created_event",
        "Project 作成イベントを追記する。",
        query_functions=("insert_project_events",),
    )

    assert query_sql_filenames_for_step(
        step,
        [
            SqlStep("001_select_projects.sql", "参照", ("projects",), "Projectを取得する。"),
            SqlStep(
                "003_insert_project_events.sql",
                "追加",
                ("project_events",),
                "Project eventを追加する。",
            ),
        ],
    ) == ["003_insert_project_events.sql"]


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
        SqlStep("001_insert_audit_events.sql", "追加", ("audit_events",), "レコードを追加する")
    ]
    assert build_arg_parser().parse_args([]).docs_root == Path("docs/spec/40.apis")


def test_query_sql_summaries_reads_docstrings_by_sql_filename(tmp_path: Path) -> None:
    queries_path = write_file(
        tmp_path,
        "queries.py",
        """
from pathlib import Path
SQL_DIR = Path(__file__).with_name("sql")

async def select_projects(session, params):
    \"\"\"Project 一覧表示に必要な Project を取得する。\"\"\"
    return await fetch_all(session, SQL_DIR / "001_select_projects.sql", params, Row)

async def helper():
    \"\"\"SQL参照がない関数です。\"\"\"
    return None
""",
    )

    assert query_sql_summaries(queries_path) == {
        "001_select_projects.sql": "Project 一覧表示に必要な Project を取得する。"
    }


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
        "project_id ResourceId",
        "caller CallerIdentity",
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
    expressions = [node.value for node in ast.walk(tree) if isinstance(node, ast.Expr)]

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
