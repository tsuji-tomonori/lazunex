from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture

from tools.generate_api_sequences import (
    ApiSequence,
    SequenceStep,
    SqlStep,
    api_dirs,
    api_sequence_from_dir,
    build_arg_parser,
    changed_outputs,
    function_target,
    generate_sequences,
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


def test_api_sequence_from_dir_reads_router_calls_and_sql(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
    api_dir = api_root / "projects/get_project"
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
        "projects/get_project/sql/001_select_projects.sql",
        "SELECT projects.project_id FROM projects;",
    )

    sequence = api_sequence_from_dir(api_dir, api_root)

    assert sequence.domain == "projects"
    assert sequence.api == "get_project"
    assert sequence.operation_id == "getProject"
    assert sequence.steps == [
        SequenceStep("get_project", "project"),
        SequenceStep("has_project_view_permission", "project_view_permission"),
        SequenceStep("build_project_detail_response", "project_detail_response"),
    ]
    assert sequence.sql_steps == [
        SqlStep("001_select_projects.sql", "参照", "projects"),
    ]


def test_render_sequence_markdown_contains_api_resource_and_table_participants() -> None:
    markdown = render_sequence_markdown(
        ApiSequence(
            domain="projects",
            api="get_project",
            endpoint_name="get_project",
            operation_id="getProject",
            steps=[
                SequenceStep("get_project", "project"),
                SequenceStep("build_project_detail_response", "project_detail_response"),
            ],
            sql_steps=[SqlStep("001_select_projects.sql", "参照", "projects")],
        )
    )

    assert "participant API as API: getProject" in markdown
    assert "participant R_project as Resource: project" in markdown
    assert "participant T_projects as Table: projects" in markdown
    assert "API->>R_project: get_project" in markdown
    assert "API->>T_projects: 参照 001_select_projects.sql" in markdown


def test_generate_sequences_and_check_mode(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    api_root = tmp_path / "apis"
    docs_root = tmp_path / "docs/spec/40.apis"
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

    rendered = generate_sequences(api_root, docs_root)
    assert list(rendered) == [docs_root / "apis/list_apis/sequence_gen.md"]
    assert changed_outputs(rendered) == [docs_root / "apis/list_apis/sequence_gen.md"]

    assert main(["--api-root", str(api_root), "--docs-root", str(docs_root), "--check"]) == 1
    assert "sequence_gen.md" in capsys.readouterr().out

    assert main(["--api-root", str(api_root), "--docs-root", str(docs_root)]) == 0
    assert main(["--api-root", str(api_root), "--docs-root", str(docs_root), "--check"]) == 0


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
        SqlStep("001_insert_audit_events.sql", "追加", "audit_events")
    ]
    assert build_arg_parser().parse_args([]).docs_root == Path("docs/spec/40.apis")
