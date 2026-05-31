from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    nullable: bool
    primary_key: bool = False
    unique: bool = False
    references: str | None = None
    comment: str = ""

    def with_comment(self, comment: str) -> Column:
        return Column(
            name=self.name,
            data_type=self.data_type,
            nullable=self.nullable,
            primary_key=self.primary_key,
            unique=self.unique,
            references=self.references,
            comment=comment,
        )


@dataclass
class Table:
    name: str
    columns: list[Column]
    comment: str = ""
    table_constraints: list[str] = field(default_factory=lambda: [])


def unescape_sql_comment(value: str) -> str:
    return value.replace("''", "'").replace("\n", " ").strip()


def identifier_name(expression: Any) -> str:
    return str(expression.name)


def table_name(expression: Any) -> str:
    if isinstance(expression, exp.Schema):
        return table_name(expression.this)
    if isinstance(expression, exp.Table):
        return str(expression.name)
    return str(expression.name)


def literal_value(expression: Any | None) -> str:
    if isinstance(expression, exp.Literal):
        return unescape_sql_comment(expression.this)
    return ""


def render_sql(expression: Any) -> str:
    return " ".join(expression.sql(dialect="postgres").split())


def reference_label(reference: exp.Reference) -> str:
    target = reference.this
    if isinstance(target, exp.Schema):
        name = table_name(target)
        columns = ", ".join(identifier_name(column) for column in target.expressions)
        return f"{name}({columns})" if columns else name
    return render_sql(reference)


def parse_column(definition: exp.ColumnDef) -> Column:
    primary_key = False
    not_null = False
    unique = False
    references: str | None = None

    for constraint in definition.constraints:
        kind = constraint.kind
        if isinstance(kind, exp.PrimaryKeyColumnConstraint):
            primary_key = True
        elif isinstance(kind, exp.NotNullColumnConstraint):
            not_null = True
        elif isinstance(kind, exp.UniqueColumnConstraint):
            unique = True
        elif isinstance(kind, exp.Reference):
            references = reference_label(kind)

    return Column(
        name=identifier_name(definition.this),
        data_type=render_sql(definition.kind) if definition.kind is not None else "",
        nullable=not not_null and not primary_key,
        primary_key=primary_key,
        unique=unique or primary_key,
        references=references,
    )


def parse_comments(
    expressions: list[Any],
) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    table_comments: dict[str, str] = {}
    column_comments: dict[tuple[str, str], str] = {}

    for expression in expressions:
        if not isinstance(expression, exp.Comment):
            continue

        comment = literal_value(expression.expression)
        if expression.args.get("kind") == "TABLE":
            table_comments[table_name(expression.this)] = comment
        elif expression.args.get("kind") == "COLUMN" and isinstance(expression.this, exp.Column):
            column_comments[(expression.this.table, expression.this.name)] = comment

    return table_comments, column_comments


def uncomment_comment_on_statements(sql: str) -> str:
    return re.sub(r"^\s*--\s+(COMMENT ON .*)$", r"\1", sql, flags=re.MULTILINE)


def table_like_source(expressions: list[Any]) -> str | None:
    for expression in expressions:
        if isinstance(expression, exp.LikeProperty):
            return table_name(expression.this)
    return None


def parse_create_table(statement: exp.Create) -> tuple[str, list[Column], list[str], str | None]:
    properties = statement.args.get("properties")
    if isinstance(statement.this, exp.Table) and isinstance(properties, exp.Properties):
        like_source = table_like_source(properties.expressions)
        if like_source:
            return table_name(statement.this), [], [], like_source

    if not isinstance(statement.this, exp.Schema):
        raise ValueError(f"CREATE TABLE statement has no schema: {statement.sql()}")

    schema = statement.this
    name = table_name(schema)
    like_source = table_like_source(schema.expressions)
    if like_source:
        return name, [], [], like_source

    columns: list[Column] = []
    constraints: list[str] = []
    for expression in schema.expressions:
        if isinstance(expression, exp.ColumnDef):
            columns.append(parse_column(expression))
        else:
            constraints.append(render_sql(expression))

    return name, columns, constraints, None


def parse_tables(sql: str) -> dict[str, Table]:
    expressions = [expression for expression in sqlglot.parse(sql, read="postgres") if expression]
    comment_expressions = [
        expression
        for expression in sqlglot.parse(uncomment_comment_on_statements(sql), read="postgres")
        if expression
    ]
    table_comments, column_comments = parse_comments(comment_expressions)
    tables: dict[str, Table] = {}

    for statement in expressions:
        if not isinstance(statement, exp.Create) or statement.kind != "TABLE":
            continue

        table_name, columns, constraints, like_source = parse_create_table(statement)
        if like_source:
            source = tables.get(like_source)
            if source is None:
                raise ValueError(f"LIKE source table is not defined: {like_source}")
            tables[table_name] = Table(
                name=table_name,
                columns=list(source.columns),
                table_constraints=list(source.table_constraints),
            )
        else:
            tables[table_name] = Table(
                name=table_name,
                columns=columns,
                table_constraints=constraints,
            )

    for table in tables.values():
        table.comment = table_comments.get(table.name, "")
        table.columns = [
            column.with_comment(column_comments.get((table.name, column.name), column.comment))
            for column in table.columns
        ]

    return tables


def key_label(column: Column) -> str:
    labels: list[str] = []
    if column.primary_key:
        labels.append("PK")
    if column.unique and not column.primary_key:
        labels.append("UNIQUE")
    if column.references:
        labels.append(f"FK -> {column.references}")
    return ", ".join(labels)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_table_markdown(table: Table) -> str:
    lines = [
        f"# {table.name}",
        "",
        table.comment or "説明未設定。",
        "",
        "| カラム | 型 | NULL許可 | キー | 説明 |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for column in table.columns:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{column.name}`",
                    f"`{column.data_type}`",
                    "YES" if column.nullable else "NO",
                    markdown_escape(key_label(column)),
                    markdown_escape(column.comment),
                ]
            )
            + " |"
        )

    if table.table_constraints:
        lines.extend(["", "## テーブル制約", ""])
        lines.extend(f"- `{markdown_escape(constraint)}`" for constraint in table.table_constraints)

    lines.append("")
    return "\n".join(lines)


def write_table_specs(tables: dict[str, Table], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for table_name in sorted(tables):
        output_path = output_dir / f"{table_name}.gen.md"
        output_path.write_text(render_table_markdown(tables[table_name]), encoding="utf-8")
        written.append(output_path)
    return written


def generate(ddl_path: Path, output_dir: Path) -> list[Path]:
    sql = ddl_path.read_text(encoding="utf-8")
    tables = parse_tables(sql)
    return write_table_specs(tables, output_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Markdown table specs from DDL.")
    parser.add_argument("--ddl", type=Path, default=Path("src/db/ddl.sql"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/spec/20.db/tables"))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    written = generate(args.ddl, args.output_dir)
    print(f"Generated {len(written)} table spec files.")


if __name__ == "__main__":  # pragma: no cover
    main()
