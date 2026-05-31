from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_api_sql_ddl_usage import (
    build_arg_parser,
    check,
    compare_usage_to_ddl,
    main,
    parse_sql_usage,
    render_report,
)


def test_parse_sql_usage_collects_tables_aliases_and_mutation_columns() -> None:
    usage = parse_sql_usage(
        """
        INSERT INTO projects (
            project_id,
            project_code
        ) VALUES (
            :project_id,
            :project_code
        )
        RETURNING project_id;

        SELECT p.project_code, pm.project_member_id
        FROM projects AS p
        LEFT JOIN project_members AS pm
            ON pm.project_id = p.project_id;

        UPDATE project_members
        SET member_role = :member_role,
            updated_at = :now
        WHERE project_member_id = :project_member_id
        RETURNING project_member_id;

        DELETE FROM project_member_events
        WHERE event_id = :event_id;
        """,
        path="sample.sql",
    )

    assert set(usage.tables) == {"projects", "project_members", "project_member_events"}
    assert set(usage.columns["projects"]) == {"project_id", "project_code"}
    assert set(usage.columns["project_members"]) == {
        "member_role",
        "project_id",
        "project_member_id",
        "updated_at",
    }


def test_compare_usage_to_ddl_reports_both_directions() -> None:
    usage = parse_sql_usage(
        """
        SELECT p.project_id, p.missing_column
        FROM projects AS p
        JOIN missing_table AS mt
            ON mt.id = p.project_id;
        """,
        path="sample.sql",
    )
    ddl = """
    CREATE TABLE projects (
        project_id uuid PRIMARY KEY,
        ddl_only text
    );
    CREATE TABLE ddl_only_table (
        id uuid PRIMARY KEY
    );
    """

    report = compare_usage_to_ddl(usage, ddl)

    assert report.missing_tables == {"missing_table"}
    assert report.missing_columns == {"projects": {"missing_column"}}
    assert report.ddl_only_tables == {"ddl_only_table"}
    assert report.ddl_only_columns == {"projects": {"ddl_only"}}


def test_compare_usage_to_ddl_ignores_like_source_tables() -> None:
    usage = parse_sql_usage(
        "INSERT INTO api_events (event_id) VALUES (@event_id);",
        path="sample.sql",
    )
    ddl = """
    CREATE TABLE hub_user_events (
        event_id uuid PRIMARY KEY
    );
    CREATE TABLE api_events LIKE hub_user_events;
    """

    report = compare_usage_to_ddl(usage, ddl)

    assert report.ddl_only_tables == set()


def test_compare_usage_to_ddl_ignores_hub_users_table() -> None:
    report = compare_usage_to_ddl(
        parse_sql_usage("SELECT p.project_id FROM projects AS p;", path="sample.sql"),
        """
        CREATE TABLE hub_users (
            user_id uuid PRIMARY KEY
        );
        CREATE TABLE projects (
            project_id uuid PRIMARY KEY
        );
        """,
    )

    assert report.ddl_only_tables == set()


def test_parse_sql_usage_collects_single_table_unqualified_columns() -> None:
    usage = parse_sql_usage(
        """
        SELECT
            project_id,
            project_code
        FROM projects
        WHERE project_code = :project_code;

        DELETE FROM project_cognito_client_urls
        WHERE project_cognito_client_id = :project_cognito_client_id
          AND url_type = :url_type;
        """,
        path="sample.sql",
    )

    assert set(usage.columns["projects"]) == {"project_id", "project_code"}
    assert set(usage.columns["project_cognito_client_urls"]) == {
        "project_cognito_client_id",
        "url_type",
    }


def test_render_report_includes_locations_and_no_drift_message() -> None:
    matching_usage = parse_sql_usage(
        "SELECT p.project_id FROM projects AS p;",
        path="src/app/apis/sample.sql",
    )
    matching_report = compare_usage_to_ddl(
        matching_usage,
        "CREATE TABLE projects (project_id uuid PRIMARY KEY);",
    )

    assert render_report(matching_report, matching_usage) == (
        "# API SQL / DDL usage check\n\nNo table or column drift found."
    )

    drift_usage = parse_sql_usage(
        "SELECT p.missing_column FROM projects AS p;",
        path="src/app/apis/sample.sql",
    )
    drift_report = compare_usage_to_ddl(
        drift_usage,
        "CREATE TABLE projects (project_id uuid PRIMARY KEY);",
    )

    rendered = render_report(drift_report, drift_usage)

    assert "## SQL references missing DDL columns" in rendered
    assert "`missing_column`" in rendered


def test_check_and_arg_parser_defaults(tmp_path: Path) -> None:
    api_sql_dir = tmp_path / "apis"
    sql_dir = api_sql_dir / "projects" / "sample" / "sql"
    sql_dir.mkdir(parents=True)
    (sql_dir / "001_select_projects.sql").write_text(
        "SELECT p.project_id FROM projects AS p;",
        encoding="utf-8",
    )
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text("CREATE TABLE projects (project_id uuid PRIMARY KEY);", encoding="utf-8")

    report, usage = check(api_sql_dir, ddl_path)
    args = build_arg_parser().parse_args([])

    assert not report.has_drift()
    assert set(usage.tables) == {"projects"}
    assert args.api_sql_dir.as_posix() == "src/app/apis"
    assert args.ddl.as_posix() == "src/db/ddl.sql"
    assert args.no_fail_on_drift is False


def test_main_exits_nonzero_when_drift_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api_sql_dir = tmp_path / "apis"
    api_sql_dir.mkdir()
    (api_sql_dir / "missing.sql").write_text("SELECT m.id FROM missing AS m;", encoding="utf-8")
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_api_sql_ddl_usage",
            "--api-sql-dir",
            str(api_sql_dir),
            "--ddl",
            str(ddl_path),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "missing" in capsys.readouterr().out


def test_main_can_ignore_drift_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api_sql_dir = tmp_path / "apis"
    api_sql_dir.mkdir()
    (api_sql_dir / "missing.sql").write_text("SELECT m.id FROM missing AS m;", encoding="utf-8")
    ddl_path = tmp_path / "ddl.sql"
    ddl_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_api_sql_ddl_usage",
            "--api-sql-dir",
            str(api_sql_dir),
            "--ddl",
            str(ddl_path),
            "--no-fail-on-drift",
        ],
    )

    main()

    assert "missing" in capsys.readouterr().out
