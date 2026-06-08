from __future__ import annotations

import csv
from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from sqlglot import parse_one

from tools.generate_db_crud import (
    CrudMatrix,
    api_name_from_sql_path,
    build_arg_parser,
    collect_crud,
    csv_escape,
    expression_tables,
    generate,
    main,
    mutation_target,
    operation_label,
    render_csv,
    sql_operations,
)


def test_operation_label_orders_crud_letters() -> None:
    assert operation_label({"U", "R"}) == "RU"
    assert operation_label({"D", "C", "R", "U"}) == "CRUD"
    assert operation_label(set()) == ""


def test_api_name_from_sql_path_uses_api_folder_name() -> None:
    root = Path("src/app/apis")
    path = root / "projects" / "create_project" / "sql" / "001_insert_projects.sql"

    assert api_name_from_sql_path(path, root) == "create_project"


def test_api_name_from_sql_path_rejects_non_api_sql_path() -> None:
    with pytest.raises(ValueError, match="API sql directory"):
        api_name_from_sql_path(
            Path("src/app/apis/projects/create_project/query.sql"), Path("src/app/apis")
        )


def test_sql_operations_extracts_crud_from_sqlglot_ast() -> None:
    operations = sql_operations(
        """
        INSERT INTO projects (project_id, project_code)
        VALUES (
            :project_id,
            (SELECT project_code FROM projects WHERE project_code = :project_code)
        );

        SELECT p.project_id, pm.project_member_id
        FROM projects AS p
        JOIN project_members AS pm ON pm.project_id = p.project_id;

        UPDATE project_members
        SET member_role = :member_role
        WHERE project_member_id = :project_member_id;

        DELETE FROM project_member_events
        WHERE project_member_event_id = :project_member_event_id;
        """
    )

    assert operations == {
        "projects": {"C", "R"},
        "project_members": {"R", "U"},
        "project_member_events": {"D"},
    }


def test_sql_operations_reads_delete_using_tables() -> None:
    operations = sql_operations(
        """
        DELETE FROM project_members
        USING projects
        WHERE projects.project_id = project_members.project_id;
        """
    )

    assert operations == {
        "project_members": {"D"},
        "projects": {"R"},
    }


def test_mutation_target_returns_none_without_target() -> None:
    class StatementWithoutTarget:
        this = None

    assert mutation_target(StatementWithoutTarget()) is None


def test_expression_tables_returns_empty_for_non_expression() -> None:
    assert expression_tables(False) == set()
    assert expression_tables([False]) == set()
    assert expression_tables(parse_one("SELECT project_id FROM projects", read="mysql")) == {
        "projects"
    }


def test_sql_operations_ignores_empty_parsed_statement(monkeypatch: MonkeyPatch) -> None:
    def parse_empty(_sql: str, read: str) -> list[None]:
        return [None]

    monkeypatch.setattr("tools.generate_db_crud.sqlglot.parse", parse_empty)

    assert sql_operations("") == {}


def test_collect_crud_ignores_tables_not_defined_in_ddl(tmp_path: Path) -> None:
    api_sql_dir = tmp_path / "apis"
    sql_dir = api_sql_dir / "projects" / "create_project" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / "001_select_projects.sql").write_text(
        """
        SELECT p.project_id, u.unknown_id
        FROM projects AS p
        JOIN unknown_table AS u ON u.project_id = p.project_id;
        """,
        encoding="utf-8",
    )

    matrix = collect_crud(api_sql_dir, ["projects"])

    assert matrix.apis == {"create_project"}
    assert matrix.cells["create_project"]["projects"] == {"R"}
    assert "unknown_table" not in matrix.cells["create_project"]


def test_render_csv_outputs_api_rows_and_table_columns() -> None:
    matrix = CrudMatrix(tables={"projects", "project_members"})
    matrix.add("create_project", "projects", "C")
    matrix.add("create_project", "projects", "R")
    matrix.add("update_project", "project_members", "U")

    rendered = render_csv(matrix, ["project_members", "projects"])

    assert list(csv.reader(rendered.splitlines())) == [
        ["api", "project_members", "projects"],
        ["create_project", "", "CR"],
        ["update_project", "U", ""],
    ]


def test_csv_escape_quotes_special_values() -> None:
    assert csv_escape("plain") == "plain"
    assert csv_escape('a,b"c') == '"a,b""c"'


def test_generate_writes_db_crud_csv(tmp_path: Path) -> None:
    api_sql_dir = tmp_path / "apis"
    sql_dir = api_sql_dir / "projects" / "create_project" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / "001_insert_projects.sql").write_text(
        "INSERT INTO projects (project_id) VALUES (:project_id);",
        encoding="utf-8",
    )
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text(
        """
        CREATE TABLE project_members (project_member_id CHAR(36) PRIMARY KEY);
        CREATE TABLE projects (project_id CHAR(36) PRIMARY KEY);
        """,
        encoding="utf-8",
    )
    output_path = tmp_path / "docs" / "db_crud.gen.csv"

    written = generate(api_sql_dir, ddl_path, output_path)

    assert written == output_path
    assert list(csv.reader(output_path.read_text(encoding="utf-8").splitlines())) == [
        ["api", "project_members", "projects"],
        ["create_project", "", "C"],
    ]


def test_arg_parser_defaults_and_main_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    default_args = build_arg_parser().parse_args([])

    assert default_args.api_sql_dir.as_posix() == "src/app/apis"
    assert default_args.ddl.as_posix() == "src/db/ddl.sql"
    assert default_args.output.as_posix() == "docs/spec/30.crud/db_crud.gen.csv"

    api_sql_dir = tmp_path / "apis"
    sql_dir = api_sql_dir / "projects" / "list_projects" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / "001_select_projects.sql").write_text(
        "SELECT project_id FROM projects;", encoding="utf-8"
    )
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text(
        "CREATE TABLE projects (project_id CHAR(36) PRIMARY KEY);",
        encoding="utf-8",
    )
    output_path = tmp_path / "db_crud.gen.csv"
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_db_crud",
            "--api-sql-dir",
            str(api_sql_dir),
            "--ddl",
            str(ddl_path),
            "--output",
            str(output_path),
        ],
    )

    main()

    assert capsys.readouterr().out == f"Generated {output_path.as_posix()}.\n"
    assert output_path.exists()
