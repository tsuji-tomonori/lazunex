from __future__ import annotations

from pathlib import Path

from tools.generate_db_table_specs import Table, parse_tables
from tools.generate_queries import FieldSpec, QuerySpec
from tools.generate_query_specs import (
    GENERATED_COMMENT,
    ApiQueryDoc,
    ColumnRef,
    ConditionSpec,
    DocFieldSpec,
    SqlDocSpec,
    build_arg_parser,
    changed_outputs,
    code_cell,
    display_nullable,
    display_type,
    expression_sql,
    field_rows,
    field_type,
    generate_query_specs,
    joined_ref_values,
    main,
    param_column_refs,
    parenthesized_condition_items,
    parse_statements,
    render_changed,
    render_code_lines,
    render_conditions,
    render_field_table,
    render_list,
    render_query_markdown,
    render_sql_spec,
    row_column_refs,
    source_column_ref,
    sql_conditions,
    sql_tables,
    text_cell,
)

DDL = """
CREATE TABLE projects (
    project_id CHAR(36) PRIMARY KEY,
    project_code varchar(100) NOT NULL,
    name varchar(200) NOT NULL,
    description text,
    created_at DATETIME(6) NOT NULL,
    row_version int NOT NULL
);
CREATE TABLE project_events (
    event_id CHAR(36) PRIMARY KEY,
    aggregate_id CHAR(36) NOT NULL,
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


def ddl_tables(tmp_path: Path) -> dict[str, Table]:
    return parse_tables(write_ddl(tmp_path).read_text(encoding="utf-8"))


def first_column_ref(tmp_path: Path, table: str, column: str) -> ColumnRef:
    tables = ddl_tables(tmp_path)
    ref = source_column_ref(
        table,
        column,
        {name: {item.name: item for item in spec.columns} for name, spec in tables.items()},
    )
    assert ref is not None
    return ref


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
        ConditionSpec(
            "JOIN ON",
            ("project_events.aggregate_id = projects.project_id",),
        ),
        ConditionSpec("WHERE", ("projects.project_code = @project_code",)),
        ConditionSpec("HAVING", ("COUNT(*) > 0",)),
    )


def test_sql_tables_deduplicates_repeated_tables() -> None:
    statements = parse_statements(
        """
        SELECT p.project_id
        FROM projects AS p
        JOIN projects AS parent ON parent.project_id = p.project_id;
        """
    )

    assert sql_tables(statements) == ("projects",)


def test_column_ref_resolution_handles_aliases_and_ambiguity(tmp_path: Path) -> None:
    tables = ddl_tables(tmp_path)

    select_refs = row_column_refs(
        parse_statements(
            """
            SELECT
                project_code,
                missing_column,
                e.event_id,
                COUNT(*) AS event_count
            FROM projects AS p
            JOIN project_events AS e ON e.aggregate_id = p.project_id;
            """
        ),
        tables,
    )
    single_table_refs = row_column_refs(
        parse_statements("SELECT project_code FROM projects AS p;"),
        tables,
    )

    assert [(ref.table_name, ref.column.name) for ref in select_refs[0]] == [
        ("projects", "project_code")
    ]
    assert select_refs[1] == ()
    assert [(ref.table_name, ref.column.name) for ref in select_refs[2]] == [
        ("project_events", "event_id")
    ]
    assert select_refs[3] == ()
    assert [(ref.table_name, ref.column.name) for ref in single_table_refs[0]] == [
        ("projects", "project_code")
    ]


def test_row_column_refs_handles_returning_and_empty_cases(tmp_path: Path) -> None:
    tables = ddl_tables(tmp_path)

    update_refs = row_column_refs(
        parse_statements(
            """
            UPDATE projects
            SET name = @name
            WHERE project_id = @project_id
            RETURNING project_id, unknown_column;
            """
        ),
        tables,
    )
    insert_without_returning = row_column_refs(
        parse_statements("INSERT INTO projects (project_id) VALUES (@project_id);"),
        tables,
    )
    delete_without_returning = row_column_refs(
        parse_statements("DELETE FROM projects WHERE project_id = @project_id;"),
        tables,
    )

    assert [(ref.table_name, ref.column.name) for ref in update_refs[0]] == [
        ("projects", "project_id")
    ]
    assert update_refs[1] == ()
    assert insert_without_returning == []
    assert delete_without_returning == []


def test_param_column_refs_cover_insert_update_and_comparison_paths(tmp_path: Path) -> None:
    tables = ddl_tables(tmp_path)
    sql = """
    INSERT INTO projects (project_id, project_code, missing_column)
    VALUES (@project_id, @project_code, @missing_value);
    UPDATE projects AS p
    SET description = @description, unknown_column = @unknown_update
    WHERE @name = p.name
      AND p.row_version >= @row_version
      AND p.project_code = 'literal';
    SELECT project_id
    FROM projects AS p
    WHERE @created_at < p.created_at
      AND p.description = @description_filter
      AND p.project_id = @project_id;
    """

    refs = param_column_refs(sql, parse_statements(sql), tables)
    pairs = [
        tuple((ref.table_name, ref.column.name) for ref in refs_for_param)
        for refs_for_param in refs
    ]

    assert pairs == [
        (("projects", "project_id"),),
        (("projects", "project_code"),),
        (),
        (("projects", "description"),),
        (),
        (("projects", "name"),),
        (("projects", "row_version"),),
        (("projects", "created_at"),),
        (("projects", "description"),),
    ]


def test_param_column_refs_falls_back_to_unique_ddl_column(tmp_path: Path) -> None:
    tables = ddl_tables(tmp_path)
    sql = "SELECT @event_payload;"

    refs = param_column_refs(sql, parse_statements(sql), tables)

    assert [[(ref.table_name, ref.column.name) for ref in item] for item in refs] == [
        [("project_events", "event_payload")]
    ]


def test_parenthesized_condition_items_handles_empty_and_single() -> None:
    expressions = parse_statements("SELECT 1 WHERE project_code = @project_code;")
    condition = expressions[0].args["where"].this

    assert parenthesized_condition_items(condition, {}) == ("(project_code = @project_code)",)


def test_expression_and_conditions_handle_unaliased_and_empty_paths() -> None:
    statements = parse_statements(
        """
        SELECT project_id
        FROM projects AS p
        JOIN project_events AS e
        WHERE p.project_code = @project_code;
        """
    )

    assert expression_sql(statements[0].expressions[0]) == "project_id"
    assert sql_conditions(statements) == (
        ConditionSpec("WHERE", ("projects.project_code = @project_code",)),
    )
    assert sql_conditions(parse_statements("SELECT 1;")) == ()


def test_display_and_render_helpers_cover_empty_and_fallback_paths(tmp_path: Path) -> None:
    ref = first_column_ref(tmp_path, "projects", "project_code")
    nullable_field = FieldSpec("optional_name", "str", True)
    any_field = FieldSpec("metadata", "Any", True)
    required_field = FieldSpec("project_code", "str", False)

    assert field_type(nullable_field) == "str | None"
    assert field_type(any_field) == "Any"
    assert display_type(required_field, (ref,)) == "VARCHAR(100)"
    assert display_type(nullable_field, ()) == "str | None"
    assert display_nullable(required_field, (ref,)) == "no"
    assert display_nullable(nullable_field, ()) == "yes"
    assert joined_ref_values((ref,), "table") == "projects"
    assert joined_ref_values((ref,), "comment") == "人が読めるProjectコード。"
    assert joined_ref_values((ref,), "unknown") == "-"
    assert code_cell("a|b") == "<code>a&#124;b</code>"
    assert text_cell("a|b\nc") == "a&#124;b c"
    assert render_code_lines("a<br>b|c") == "<code>a</code><br><code>b&#124;c</code>"
    assert field_rows(nullable_field, ()) == [
        (
            "<code>-</code>",
            "<code>optional_name</code>",
            "<code>optional_name</code>",
            "-",
            "<code>str &#124; None</code>",
            "yes",
        )
    ]
    assert render_field_table([], "_empty_") == ["_empty_"]
    assert render_list((), "_empty_") == ["_empty_"]
    assert render_conditions(()) == ["_なし_"]


def test_render_sql_spec_handles_operation_fallback_and_empty_sections() -> None:
    spec = SqlDocSpec(
        query=QuerySpec(
            sql_filename="999_custom.sql",
            summary="Custom query.",
            class_prefix="Custom",
            function_name="custom_query",
            operation="merge",
            params=[],
            rows=[FieldSpec("result", "Any", False)],
        ),
        tables=(),
        params=[],
        rows=[DocFieldSpec(FieldSpec("result", "Any", False))],
        conditions=(),
    )

    rendered = "\n".join(render_sql_spec(spec))

    assert "`MERGE`" in rendered
    assert "### 利用するテーブル\n\n_なし_" in rendered
    assert "| <code>-</code> | <code>result</code> | <code>result</code> | -" in rendered


def test_render_query_markdown_inserts_blank_line_between_multiple_specs() -> None:
    query = QuerySpec(
        sql_filename="001_select.sql",
        summary="Select.",
        class_prefix="Select",
        function_name="select_rows",
        operation="select",
        params=[],
        rows=[],
    )
    spec = SqlDocSpec(query=query, tables=(), params=[], rows=[], conditions=())

    rendered = render_query_markdown(ApiQueryDoc("projects", "multi", [spec, spec]))

    assert rendered.count("## 001_select.sql") == 2
    assert "\n\n## 001_select.sql" in rendered


def test_changed_outputs_and_render_changed_cover_missing_and_stale_files(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    stale = tmp_path / "stale.md"
    fresh = tmp_path / "fresh.md"
    stale.write_text("old", encoding="utf-8")
    fresh.write_text("new", encoding="utf-8")

    changed = changed_outputs({missing: "new", stale: "new", fresh: "new"})

    assert changed == [missing, stale]
    assert render_changed(changed) == f"{missing}\n{stale}"


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
        "| <code>projects</code> | <code>project_code</code> | <code>project_code</code> | "
        "人が読めるProjectコード。 | <code>VARCHAR(100)</code> | no |"
    ) in content
    assert (
        "| <code>projects</code> | <code>description</code> | <code>description</code> | "
        "プロジェクトの説明。 | <code>TEXT</code> | yes |"
    ) in content
    assert "### 条件\n\n- `WHERE`\n  - `project_code = @project_code`" in content


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
        "| <code>projects</code> | <code>project_code</code> | <code>project_code</code> | "
        "人が読めるProjectコード。 | <code>VARCHAR(100)</code> | no |"
    ) in content
    assert (
        "| <code>projects</code> | <code>project_id</code> | <code>project_id</code> | "
        "Project ID。 | <code>CHAR(36)</code> | no |"
    ) in content
    assert (
        "| <code>-</code> | <code>event_count</code> | <code>event_count</code> | "
        "- | <code>Any</code> | no |"
    ) in content
    assert "- `JOIN ON`\n  - `project_events.aggregate_id = projects.project_id`" in content
    assert "- `WHERE`\n  - `projects.project_code = @project_code`" in content


def test_generate_query_specs_splits_and_or_conditions(tmp_path: Path) -> None:
    api_root = write_api_sql(
        tmp_path,
        """
        SELECT project_id
        FROM projects AS p
        JOIN project_events AS e
            ON e.aggregate_id = p.project_id
           AND e.event_id = @event_id
        WHERE (p.project_code = @project_code
            OR p.description = @description)
          AND p.project_id = @project_id;
        """,
    )

    content = next(
        iter(generate_query_specs(api_root, tmp_path / "docs", write_ddl(tmp_path)).values())
    )

    assert (
        "- `JOIN ON`\n"
        "  - `project_events.aggregate_id = projects.project_id`\n"
        "  - `AND project_events.event_id = @event_id`"
    ) in content
    assert (
        "- `WHERE`\n"
        "  - `(projects.project_code = @project_code`\n"
        "  - `OR projects.description = @description)`\n"
        "  - `AND projects.project_id = @project_id`"
    ) in content


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

    assert (
        main(
            [
                "--api-root",
                str(api_root),
                "--docs-root",
                str(docs_root),
                "--ddl",
                str(ddl_path),
            ]
        )
        == 0
    )
    assert (docs_root / "projects" / "list_projects" / "query_gen.md").exists()
    assert (
        main(
            [
                "--api-root",
                str(api_root),
                "--docs-root",
                str(docs_root),
                "--ddl",
                str(ddl_path),
                "--check",
            ]
        )
        == 0
    )

    (docs_root / "projects" / "list_projects" / "query_gen.md").write_text(
        "stale",
        encoding="utf-8",
    )

    assert (
        main(
            [
                "--api-root",
                str(api_root),
                "--docs-root",
                str(docs_root),
                "--ddl",
                str(ddl_path),
                "--check",
            ]
        )
        == 1
    )


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
