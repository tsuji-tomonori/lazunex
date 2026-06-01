from __future__ import annotations

from pathlib import Path

from tools.generate_query_specs import (
    GENERATED_COMMENT,
    build_arg_parser,
    generate_query_specs,
    main,
    parse_statements,
    render_query_markdown,
    sql_conditions,
    sql_tables,
)

DDL = """
CREATE TABLE projects (
    project_id uuid PRIMARY KEY,
    project_code varchar(100) NOT NULL,
    name varchar(200) NOT NULL,
    description text,
    created_at timestamptz NOT NULL,
    row_version int NOT NULL
);
CREATE TABLE project_events (
    event_id uuid PRIMARY KEY,
    aggregate_id uuid NOT NULL,
    event_payload json
);
-- COMMENT ON COLUMN projects.project_id IS 'Project ID。';
-- COMMENT ON COLUMN projects.project_code IS '人が読めるProjectコード。';
-- COMMENT ON COLUMN projects.description IS 'プロジェクトの説明。';
-- COMMENT ON COLUMN project_events.event_id IS 'ProjectイベントID。';
"""


def write_api_sql(tmp_path: Path, sql: str, filename: str = "001_select_projects.sql") -> Path:
    api_root = tmp_path / "apis"
    sql_dir = api_root / "projects" / "list_projects" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / filename).write_text(sql, encoding="utf-8")
    return api_root


def write_ddl(tmp_path: Path) -> Path:
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text(DDL, encoding="utf-8")
    return ddl_path


def test_sql_tables_and_conditions_preserve_sql_order() -> None:
    statements = parse_statements(
        """
        SELECT p.project_id, e.event_id
        FROM projects AS p
        JOIN project_events AS e ON e.aggregate_id = p.project_id
        WHERE p.project_code = @project_code
        HAVING COUNT(*) > 0;
        """
    )

    assert sql_tables(statements) == ("projects", "project_events")
    assert sql_conditions(statements) == (
        "JOIN ON project_events.aggregate_id = projects.project_id",
        "WHERE projects.project_code = @project_code",
        "HAVING COUNT(*) > 0",
    )


def test_generate_query_specs_renders_sql_chapters(tmp_path: Path) -> None:
    api_root = write_api_sql(
        tmp_path,
        """
        -- Project 一覧を取得する。
        SELECT project_id, project_code, description
        FROM projects
        WHERE project_code = @project_code;
        """,
    )
    docs_root = tmp_path / "docs"

    rendered = generate_query_specs(api_root, docs_root, write_ddl(tmp_path))
    output_path = docs_root / "projects" / "list_projects" / "query_gen.md"
    content = rendered[output_path]

    assert content.startswith(GENERATED_COMMENT)
    assert "# list_projects query" in content
    assert "## 001_select_projects.sql" in content
    assert "### SQL種別\n\n`SELECT`" in content
    assert "### SQLの概要" in content
    assert "Project 一覧を取得する。" in content
    assert "### 利用するテーブル\n\n- `projects`" in content
    assert (
        "| <code>projects.project_code</code> | <code>project_code</code> | "
        "人が読めるProjectコード。 | <code>VARCHAR(100)</code> | no |"
    ) in content
    assert (
        "| <code>projects.description</code> | <code>description</code> | "
        "プロジェクトの説明。 | <code>TEXT</code> | yes |"
    ) in content
    assert "### 条件\n\n- `WHERE project_code = @project_code`" in content


def test_generate_query_specs_renders_source_tables_and_expanded_aliases(
    tmp_path: Path,
) -> None:
    api_root = write_api_sql(
        tmp_path,
        """
        SELECT
            p.project_id,
            COUNT(e.event_id) AS event_count
        FROM projects AS p
        LEFT JOIN project_events AS e
            ON e.aggregate_id = p.project_id
        WHERE p.project_code = @project_code;
        """,
    )

    content = next(
        iter(generate_query_specs(api_root, tmp_path / "docs", write_ddl(tmp_path)).values())
    )

    assert (
        "| <code>projects.project_code</code> | <code>project_code</code> | "
        "人が読めるProjectコード。 | <code>VARCHAR(100)</code> | no |"
    ) in content
    assert (
        "| <code>projects.project_id</code> | <code>project_id</code> | "
        "Project ID。 | <code>UUID</code> | no |"
    ) in content
    assert (
        "| <code>-</code> | <code>event_count</code> | - | <code>Any</code> | no |"
    ) in content
    assert (
        "- `JOIN ON project_events.aggregate_id = projects.project_id`"
        in content
    )
    assert "- `WHERE projects.project_code = @project_code`" in content


def test_render_query_markdown_marks_empty_sections(tmp_path: Path) -> None:
    api_root = write_api_sql(
        tmp_path,
        "INSERT INTO project_events (event_id, aggregate_id) VALUES (@event_id, @aggregate_id);",
        filename="002_insert_project_events.sql",
    )
    rendered = generate_query_specs(api_root, tmp_path / "docs", write_ddl(tmp_path))
    content = next(iter(rendered.values()))

    assert "## 002_insert_project_events.sql" in content
    assert "### 戻り値\n\n_なし_" in content
    assert "### 条件\n\n_なし_" in content


def test_main_writes_outputs_and_check_reports_changed(
    tmp_path: Path,
) -> None:
    api_root = write_api_sql(tmp_path, "SELECT project_id FROM projects;")
    docs_root = tmp_path / "docs"
    ddl_path = write_ddl(tmp_path)

    assert main(
        [
            "--api-root",
            str(api_root),
            "--docs-root",
            str(docs_root),
            "--ddl",
            str(ddl_path),
        ]
    ) == 0
    assert (docs_root / "projects" / "list_projects" / "query_gen.md").exists()
    assert main(
        [
            "--api-root",
            str(api_root),
            "--docs-root",
            str(docs_root),
            "--ddl",
            str(ddl_path),
            "--check",
        ]
    ) == 0

    (docs_root / "projects" / "list_projects" / "query_gen.md").write_text(
        "stale",
        encoding="utf-8",
    )

    assert main(
        [
            "--api-root",
            str(api_root),
            "--docs-root",
            str(docs_root),
            "--ddl",
            str(ddl_path),
            "--check",
        ]
    ) == 1


def test_arg_parser_defaults() -> None:
    args = build_arg_parser().parse_args([])

    assert args.api_root.as_posix() == "src/app/apis"
    assert args.docs_root.as_posix() == "docs/spec/40.apis"
    assert args.ddl.as_posix() == "src/db/ddl.sql"


def test_render_query_markdown_handles_no_sql_specs() -> None:
    from tools.generate_query_specs import ApiQueryDoc

    assert render_query_markdown(ApiQueryDoc("projects", "empty", [])) == (
        f"{GENERATED_COMMENT}\n\n# empty query\n"
    )
