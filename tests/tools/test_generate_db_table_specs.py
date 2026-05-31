from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from sqlglot import exp, parse_one

from tools.generate_db_table_specs import (
    Column,
    build_arg_parser,
    generate,
    key_label,
    literal_value,
    main,
    markdown_escape,
    parse_column,
    parse_create_table,
    parse_tables,
    reference_label,
    render_table_markdown,
    table_name,
    unescape_sql_comment,
)


def test_parse_column_extracts_key_nullability_and_reference() -> None:
    statement = parse_one(
        "CREATE TABLE sample (api_id uuid NOT NULL UNIQUE REFERENCES apis(api_id));",
        read="postgres",
    )
    assert isinstance(statement.this, exp.Schema)
    column_def = statement.this.expressions[0]
    assert isinstance(column_def, exp.ColumnDef)

    column = parse_column(column_def)

    assert column == Column(
        name="api_id",
        data_type="UUID",
        nullable=False,
        primary_key=False,
        unique=True,
        references="apis(api_id)",
    )


def test_sqlglot_helper_fallbacks() -> None:
    assert table_name(exp.to_identifier("fallback_name")) == "fallback_name"
    assert literal_value(exp.to_identifier("not_literal")) == ""
    assert reference_label(exp.Reference(this=exp.Table(this=exp.to_identifier("apis")))) == (
        "REFERENCES apis"
    )


def test_parse_column_marks_primary_key_as_unique_and_not_nullable() -> None:
    statement = parse_one("CREATE TABLE sample (sample_id uuid PRIMARY KEY);", read="postgres")
    assert isinstance(statement.this, exp.Schema)
    column_def = statement.this.expressions[0]
    assert isinstance(column_def, exp.ColumnDef)

    column = parse_column(column_def)

    assert column.primary_key is True
    assert column.unique is True
    assert column.nullable is False


def test_parse_create_table_rejects_non_schema_create() -> None:
    statement = parse_one("CREATE VIEW sample AS SELECT 1", read="postgres")
    assert isinstance(statement, exp.Create)

    with pytest.raises(ValueError, match="CREATE TABLE statement has no schema"):
        parse_create_table(statement)


def test_parse_tables_supports_comments_and_like_tables() -> None:
    sql = """
    CREATE TABLE base_events (
        event_id uuid PRIMARY KEY,
        aggregate_id uuid NOT NULL,
        event_payload json,
        UNIQUE (aggregate_id, event_id)
    );
    CREATE TABLE api_events (LIKE base_events INCLUDING ALL);
    COMMENT ON TABLE api_events IS 'APIイベント。';
    COMMENT ON COLUMN api_events.event_id IS 'イベントID。';
    COMMENT ON COLUMN api_events.aggregate_id IS '集約ID。';
    """

    tables = parse_tables(sql)

    assert tables["api_events"].comment == "APIイベント。"
    assert [column.name for column in tables["api_events"].columns] == [
        "event_id",
        "aggregate_id",
        "event_payload",
    ]
    assert tables["api_events"].columns[0].comment == "イベントID。"
    assert tables["api_events"].table_constraints == ["UNIQUE (aggregate_id, event_id)"]


def test_parse_tables_raises_for_missing_like_source() -> None:
    with pytest.raises(ValueError, match="LIKE source table"):
        parse_tables("CREATE TABLE child_events (LIKE missing_events INCLUDING ALL);")


def test_render_table_markdown_includes_columns_constraints_and_escapes_pipe() -> None:
    table = parse_tables(
        """
        CREATE TABLE sample (
            sample_id uuid PRIMARY KEY,
            api_id uuid REFERENCES apis(api_id),
            label text,
            UNIQUE (label)
        );
        COMMENT ON TABLE sample IS 'sample説明。';
        COMMENT ON COLUMN sample.sample_id IS '主キー。';
        COMMENT ON COLUMN sample.api_id IS 'API|ID。';
        """
    )["sample"]

    markdown = render_table_markdown(table)

    assert markdown.startswith("# sample")
    assert "| `sample_id` | `UUID` | NO | PK | 主キー。 |" in markdown
    assert "| `api_id` | `UUID` | YES | FK -> apis(api_id) | API\\|ID。 |" in markdown
    assert "- `UNIQUE (label)`" in markdown


def test_generate_writes_sorted_table_specs(tmp_path: Path) -> None:
    ddl_path = tmp_path / "ddl.sql"
    output_dir = tmp_path / "tables"
    ddl_path.write_text(
        """
        CREATE TABLE zeta (zeta_id uuid PRIMARY KEY);
        CREATE TABLE alpha (alpha_id uuid PRIMARY KEY);
        COMMENT ON TABLE alpha IS 'アルファ。';
        COMMENT ON COLUMN alpha.alpha_id IS 'アルファID。';
        """,
        encoding="utf-8",
    )

    written = generate(ddl_path, output_dir)

    assert [path.name for path in written] == ["alpha.gen.md", "zeta.gen.md"]
    assert (output_dir / "alpha.gen.md").read_text(encoding="utf-8").startswith("# alpha")


def test_arg_parser_defaults_and_main_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    default_args = build_arg_parser().parse_args([])

    assert default_args.ddl.as_posix() == "src/db/ddl.sql"
    assert default_args.output_dir.as_posix() == "docs/spec/20.db/tables"

    ddl_path = tmp_path / "ddl.sql"
    output_dir = tmp_path / "tables"
    ddl_path.write_text("CREATE TABLE sample (sample_id uuid PRIMARY KEY);", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_db_table_specs",
            "--ddl",
            str(ddl_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    main()

    assert capsys.readouterr().out == "Generated 1 table spec files.\n"
    assert (output_dir / "sample.gen.md").exists()


def test_small_helpers() -> None:
    assert unescape_sql_comment("Bob''s table\ncomment") == "Bob's table comment"
    assert markdown_escape("a|b\nc") == "a\\|b c"
    assert key_label(Column("id", "uuid", False, primary_key=True)) == "PK"
    assert key_label(Column("code", "text", False, unique=True)) == "UNIQUE"
    assert (
        key_label(Column("api_id", "uuid", True, references="apis(api_id)")) == "FK -> apis(api_id)"
    )
