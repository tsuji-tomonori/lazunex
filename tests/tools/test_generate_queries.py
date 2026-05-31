from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from sqlglot import exp, parse_one

from tools.generate_db_table_specs import parse_tables
from tools.generate_queries import (
    base_type_from_sql,
    build_arg_parser,
    class_prefix_from_sql_path,
    collect_insert_param_columns,
    collect_update_param_columns,
    function_name_from_sql_path,
    generate_queries,
    infer_row_fields,
    main,
    model_type,
    mutation_target_table,
    operation_from_statements,
    output_field,
    parse_query_spec,
    pascal_case,
    placeholder_names,
    python_identifier,
    render_queries_py,
    render_query_function,
    required_imports,
    returning_output_fields,
    sql_summary,
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
CREATE TABLE metrics (
    metric_id uuid PRIMARY KEY,
    measured_on date NOT NULL,
    amount numeric(10, 2) NOT NULL
);
"""


def test_name_helpers() -> None:
    assert python_identifier("1 Bad-Name") == "field_1_bad_name"
    assert python_identifier("!!!") == "value"
    assert pascal_case("001_select-projects") == "Field001SelectProjects"
    assert class_prefix_from_sql_path(Path("001_select_projects.sql")) == "SelectProjects"
    assert function_name_from_sql_path(Path("001_select_projects.sql")) == "select_projects"


def test_type_helpers() -> None:
    assert base_type_from_sql("uuid") == "UUID"
    assert base_type_from_sql("varchar(100)") == "str"
    assert base_type_from_sql("integer") == "int"
    assert base_type_from_sql("numeric(10, 2)") == "Decimal"
    assert base_type_from_sql("boolean") == "bool"
    assert base_type_from_sql("date") == "date"
    assert base_type_from_sql("timestamptz") == "datetime"
    assert base_type_from_sql("json") == "dict[str, Any]"
    assert base_type_from_sql("custom") == "Any"
    assert model_type("str", True) == "str | None"
    assert model_type("Any", True) == "Any"


def test_placeholder_names_preserves_first_seen_order() -> None:
    assert placeholder_names("@project_id, @name, @project_id") == ["project_id", "name"]


def test_parse_query_spec_infers_select_params_and_rows(tmp_path: Path) -> None:
    sql_path = tmp_path / "001_select_projects.sql"
    sql_path.write_text(
        """
        -- プロジェクトコードの重複確認に使う既存 Project を取得する。
        SELECT project_id, project_code, description
        FROM projects
        WHERE project_code = @project_code;
        """,
        encoding="utf-8",
    )

    spec = parse_query_spec(sql_path, parse_tables(DDL))

    assert spec.class_prefix == "SelectProjects"
    assert spec.function_name == "select_projects"
    assert spec.operation == "select"
    assert spec.sql_filename == "001_select_projects.sql"
    assert spec.summary == "プロジェクトコードの重複確認に使う既存 Project を取得する。"
    assert [(field.name, field.type_hint, field.nullable) for field in spec.params] == [
        ("project_code", "str", False)
    ]
    assert [(field.name, field.type_hint, field.nullable) for field in spec.rows] == [
        ("project_id", "UUID", False),
        ("project_code", "str", False),
        ("description", "str", True),
    ]


def test_parse_query_spec_infers_qualified_alias_and_expression_rows(tmp_path: Path) -> None:
    sql_path = tmp_path / "001_select_projects.sql"
    sql_path.write_text(
        """
        SELECT
            p.name AS project_name,
            COUNT(*) AS total_count,
            p.project_code
        FROM projects AS p
        WHERE p.project_id = @project_id;
        """,
        encoding="utf-8",
    )

    spec = parse_query_spec(sql_path, parse_tables(DDL))

    assert [(field.name, field.type_hint) for field in spec.params] == [("project_id", "UUID")]
    assert [(field.name, field.type_hint) for field in spec.rows] == [
        ("project_name", "str"),
        ("total_count", "Any"),
        ("project_code", "str"),
    ]


def test_operation_from_statements_detects_statement_kind() -> None:
    assert (
        operation_from_statements([parse_one("SELECT project_id FROM projects", read="postgres")])
        == "select"
    )
    assert (
        operation_from_statements(
            [parse_one("INSERT INTO projects (project_id) VALUES (@project_id)", read="postgres")]
        )
        == "insert"
    )
    assert (
        operation_from_statements([parse_one("UPDATE projects SET name = @name", read="postgres")])
        == "update"
    )
    assert (
        operation_from_statements([parse_one("DELETE FROM projects", read="postgres")]) == "delete"
    )
    assert operation_from_statements([]) == "execute"


def test_sql_summary_reads_first_comment_or_falls_back() -> None:
    assert sql_summary("\n-- 利用目的を説明する。\nSELECT 1;") == "利用目的を説明する。"
    assert sql_summary("SELECT 1;") == "SQLで必要なデータを読み書きする。"


def test_parse_query_spec_infers_insert_params_and_returning_rows(tmp_path: Path) -> None:
    sql_path = tmp_path / "002_insert_projects.sql"
    sql_path.write_text(
        """
        INSERT INTO projects (
            project_id,
            project_code,
            name,
            description,
            created_at,
            row_version
        ) VALUES (
            @project_id,
            @project_code,
            @name,
            @description,
            @now,
            1
        )
        RETURNING project_id, row_version;
        """,
        encoding="utf-8",
    )

    spec = parse_query_spec(sql_path, parse_tables(DDL))

    assert [(field.name, field.type_hint) for field in spec.params] == [
        ("project_id", "UUID"),
        ("project_code", "str"),
        ("name", "str"),
        ("description", "str"),
        ("now", "datetime"),
    ]
    assert [(field.name, field.type_hint) for field in spec.rows] == [
        ("project_id", "UUID"),
        ("row_version", "int"),
    ]


def test_parse_query_spec_infers_update_params_and_returning_rows(tmp_path: Path) -> None:
    sql_path = tmp_path / "003_update_projects.sql"
    sql_path.write_text(
        """
        UPDATE projects
        SET name = @name,
            row_version = row_version + 1
        WHERE project_id = @project_id
        RETURNING project_id, row_version;
        """,
        encoding="utf-8",
    )

    spec = parse_query_spec(sql_path, parse_tables(DDL))

    assert [(field.name, field.type_hint) for field in spec.params] == [
        ("name", "str"),
        ("project_id", "UUID"),
    ]
    assert [(field.name, field.type_hint) for field in spec.rows] == [
        ("project_id", "UUID"),
        ("row_version", "int"),
    ]


def test_returning_and_mutation_helpers_handle_missing_returning_or_target() -> None:
    tables = parse_tables(DDL)
    columns = {
        table_name: {column.name: column for column in table.columns}
        for table_name, table in tables.items()
    }
    select = parse_one("SELECT project_id FROM projects", read="postgres")
    assert mutation_target_table(select) is None
    assert returning_output_fields(select, columns) == []


def test_collect_param_columns_handles_non_standard_insert_and_update() -> None:
    tables = parse_tables(DDL)
    columns = {
        table_name: {column.name: column for column in table.columns}
        for table_name, table in tables.items()
    }
    select = parse_one("SELECT project_id FROM projects", read="postgres")
    assert isinstance(select, exp.Select)
    assert collect_insert_param_columns(select, columns) == {}  # type: ignore[arg-type]

    insert_select = parse_one(
        "INSERT INTO projects (project_id) SELECT project_id FROM projects",
        read="postgres",
    )
    assert isinstance(insert_select, exp.Insert)
    assert collect_insert_param_columns(insert_select, columns) == {}

    update = parse_one("UPDATE projects SET row_version = row_version + 1", read="postgres")
    assert isinstance(update, exp.Update)
    assert collect_update_param_columns(update, columns) == {}


def test_render_queries_py_includes_required_imports_and_empty_params(tmp_path: Path) -> None:
    sql_path = tmp_path / "003_insert_project_events.sql"
    sql_path.write_text(
        """
        INSERT INTO project_events (
            event_id,
            aggregate_id,
            event_payload
        ) VALUES (
            @event_id,
            @aggregate_id,
            CAST(@event_payload AS json)
        );
        """,
        encoding="utf-8",
    )
    spec = parse_query_spec(sql_path, parse_tables(DDL))

    rendered = render_queries_py([spec])

    assert "from pathlib import Path" in rendered
    assert "from sqlalchemy.ext.asyncio import AsyncSession" in rendered
    assert "from app.db.query import execute_sql" in rendered
    assert 'SQL_DIR = Path(__file__).with_name("sql")' in rendered
    assert "from typing import Any" in rendered
    assert "from uuid import UUID" in rendered
    assert "class InsertProjectEventsParams(BaseModel):" in rendered
    assert "event_payload: dict[str, Any]" in rendered
    assert "class InsertProjectEventsRow" not in rendered
    assert "async def insert_project_events(" in rendered
    assert '"""SQLで必要なデータを読み書きする。"""' in rendered
    assert "await execute_sql(" in rendered
    assert 'SQL_DIR / "003_insert_project_events.sql"' in rendered


def test_render_queries_py_uses_two_blank_lines_between_top_level_blocks(
    tmp_path: Path,
) -> None:
    sql_path = tmp_path / "001_select_projects.sql"
    sql_path.write_text("SELECT project_id FROM projects;", encoding="utf-8")
    spec = parse_query_spec(sql_path, parse_tables(DDL))

    rendered = render_queries_py([spec])

    assert 'SQL_DIR = Path(__file__).with_name("sql")\n\n\nclass SelectProjectsParams' in rendered
    assert "    pass\n\n\nclass SelectProjectsRow" in rendered
    assert "    project_id: UUID\n\n\nasync def select_projects(" in rendered


def test_render_queries_py_includes_empty_params_and_date_decimal_imports(tmp_path: Path) -> None:
    sql_path = tmp_path / "001_select_metrics.sql"
    sql_path.write_text(
        "SELECT metric_id, measured_on, amount FROM metrics;",
        encoding="utf-8",
    )
    spec = parse_query_spec(sql_path, parse_tables(DDL))

    rendered = render_queries_py([spec])

    assert "from datetime import date" in rendered
    assert "from decimal import Decimal" in rendered
    assert "from app.db.query import fetch_all" in rendered
    assert "class SelectMetricsParams(BaseModel):" in rendered
    assert "    pass" in rendered
    assert "measured_on: date" in rendered
    assert "amount: Decimal" in rendered
    assert "async def select_metrics(" in rendered
    assert "return await fetch_all(" in rendered
    assert 'SQL_DIR / "001_select_metrics.sql"' in rendered


def test_render_query_function_uses_fetch_one_for_mutation_returning(tmp_path: Path) -> None:
    sql_path = tmp_path / "002_insert_projects.sql"
    sql_path.write_text(
        """
        INSERT INTO projects (project_id, project_code, name, created_at, row_version)
        VALUES (@project_id, @project_code, @name, @now, 1)
        RETURNING project_id;
        """,
        encoding="utf-8",
    )
    spec = parse_query_spec(sql_path, parse_tables(DDL))

    rendered = "\n".join(render_query_function(spec))

    assert "async def insert_projects(" in rendered
    assert ") -> InsertProjectsRow | None:" in rendered
    assert "return await fetch_one(" in rendered
    assert 'SQL_DIR / "002_insert_projects.sql"' in rendered


def test_render_queries_py_imports_multiple_query_helpers(tmp_path: Path) -> None:
    select_sql = tmp_path / "001_select_projects.sql"
    select_sql.write_text("SELECT project_id FROM projects;", encoding="utf-8")
    insert_sql = tmp_path / "002_insert_projects.sql"
    insert_sql.write_text(
        "INSERT INTO projects (project_id) VALUES (@project_id) RETURNING project_id;",
        encoding="utf-8",
    )
    execute_sql = tmp_path / "003_insert_project_events.sql"
    execute_sql.write_text(
        "INSERT INTO project_events (event_id, aggregate_id) VALUES (@event_id, @aggregate_id);",
        encoding="utf-8",
    )
    tables = parse_tables(DDL)

    rendered = render_queries_py(
        [
            parse_query_spec(select_sql, tables),
            parse_query_spec(insert_sql, tables),
            parse_query_spec(execute_sql, tables),
        ]
    )

    assert "from app.db.query import execute_sql, fetch_all, fetch_one" in rendered


def test_output_field_falls_back_for_unknown_column_and_plain_expression() -> None:
    tables = parse_tables(DDL)
    columns = {
        table_name: {column.name: column for column in table.columns}
        for table_name, table in tables.items()
    }
    unknown_column = parse_one("SELECT unknown_column FROM projects", read="postgres").expressions[
        0
    ]
    literal_expression = parse_one("SELECT 1", read="postgres").expressions[0]

    assert output_field(unknown_column, {}, columns).type_hint == "Any"
    assert output_field(literal_expression, {}, columns).name == "field_1"


def test_infer_row_fields_returns_empty_when_no_select_or_returning() -> None:
    statement = parse_one("DELETE FROM projects WHERE project_id = @project_id", read="postgres")

    assert infer_row_fields([statement], parse_tables(DDL)) == []


def test_required_imports_handles_minimal_specs() -> None:
    assert required_imports([]) == [
        "from pathlib import Path",
        "",
        "from pydantic import BaseModel, ConfigDict",
        "",
    ]


def test_generate_queries_writes_each_api_queries_file(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    sql_dir = api_root / "projects" / "create_project" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / "001_select_projects.sql").write_text(
        "SELECT project_id FROM projects WHERE project_code = @project_code;",
        encoding="utf-8",
    )
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text(DDL, encoding="utf-8")

    written = generate_queries(api_root, ddl_path)

    assert written == [sql_dir.parent / "queries.py"]
    content = written[0].read_text(encoding="utf-8")
    assert "class SelectProjectsParams(BaseModel):" in content
    assert "project_code: str" in content
    assert "class SelectProjectsRow(BaseModel):" in content
    assert "async def select_projects(" in content


def test_arg_parser_defaults_and_main_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    default_args = build_arg_parser().parse_args([])

    assert default_args.api_root.as_posix() == "src/app/apis"
    assert default_args.ddl.as_posix() == "src/db/ddl.sql"

    api_root = tmp_path / "apis"
    sql_dir = api_root / "projects" / "list_projects" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / "001_select_projects.sql").write_text(
        "SELECT project_id FROM projects;", encoding="utf-8"
    )
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text(DDL, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_queries",
            "--api-root",
            str(api_root),
            "--ddl",
            str(ddl_path),
        ],
    )

    main()

    assert capsys.readouterr().out == "Generated 1 queries.py files.\n"
    assert (sql_dir.parent / "queries.py").exists()


def test_generate_queries_handles_api_without_sql(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    (api_root / "projects" / "empty_api").mkdir(parents=True)
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text(DDL, encoding="utf-8")

    assert generate_queries(api_root, ddl_path) == []


def test_unknown_placeholder_type_falls_back_to_any(tmp_path: Path) -> None:
    sql_path = tmp_path / "001_select_projects.sql"
    sql_path.write_text(
        "SELECT project_id FROM projects WHERE @unknown_value IS NULL;", encoding="utf-8"
    )

    spec = parse_query_spec(sql_path, parse_tables(DDL))

    assert [(field.name, field.type_hint) for field in spec.params] == [("unknown_value", "Any")]


def test_comparison_placeholder_can_be_on_left_side(tmp_path: Path) -> None:
    sql_path = tmp_path / "001_select_projects.sql"
    sql_path.write_text(
        "SELECT project_id FROM projects WHERE @project_code = project_code;", encoding="utf-8"
    )

    spec = parse_query_spec(sql_path, parse_tables(DDL))

    assert [(field.name, field.type_hint) for field in spec.params] == [("project_code", "str")]
