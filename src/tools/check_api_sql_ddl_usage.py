from __future__ import annotations

import argparse
import bisect
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.expressions.core import Expression

from tools.generate_db_table_specs import parse_tables

DDL_ONLY_TABLE_EXCEPTIONS = frozenset({"hub_users"})


@dataclass(frozen=True, order=True)
class SqlReference:
    path: Path
    line: int
    detail: str


@dataclass
class SqlUsage:
    tables: dict[str, set[SqlReference]] = field(default_factory=lambda: defaultdict(set))
    columns: dict[str, dict[str, set[SqlReference]]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(set))
    )
    unresolved_qualifiers: dict[str, set[SqlReference]] = field(
        default_factory=lambda: defaultdict(set)
    )

    def add_table(self, table: str, reference: SqlReference) -> None:
        self.tables[table].add(reference)

    def add_column(self, table: str, column: str, reference: SqlReference) -> None:
        self.add_table(table, reference)
        self.columns[table][column].add(reference)

    def merge(self, other: SqlUsage) -> None:
        for table, references in other.tables.items():
            self.tables[table].update(references)
        for table, columns in other.columns.items():
            for column, references in columns.items():
                self.columns[table][column].update(references)
        for qualifier, references in other.unresolved_qualifiers.items():
            self.unresolved_qualifiers[qualifier].update(references)


@dataclass(frozen=True)
class DriftReport:
    missing_tables: set[str]
    missing_columns: dict[str, set[str]]
    ddl_only_tables: set[str]
    ddl_only_columns: dict[str, set[str]]
    unresolved_qualifiers: dict[str, set[SqlReference]]

    def has_drift(self) -> bool:
        return any(
            [
                self.missing_tables,
                self.missing_columns,
                self.ddl_only_tables,
                self.ddl_only_columns,
                self.unresolved_qualifiers,
            ]
        )


def line_index(sql: str) -> list[int]:
    return [0, *[match.end() for match in re.finditer("\n", sql)]]


def line_number(starts: list[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def expression_start(expression: Expression) -> int | None:
    meta_start = expression.meta.get("start")
    if isinstance(meta_start, int):
        return meta_start

    child = expression.this
    if isinstance(child, Expression):
        return expression_start(child)
    return None


def reference(
    path: Path,
    starts: list[int],
    expression: Expression,
    detail: str,
) -> SqlReference:
    start = expression_start(expression)
    line = line_number(starts, start) if start is not None else 1
    return SqlReference(path=path, line=line, detail=detail)


def table_aliases(tree: Expression) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table in tree.find_all(exp.Table):
        table_name = table.name
        if not table_name:
            continue
        aliases[table_name] = table_name
        if table.alias:
            aliases[table.alias] = table_name
    return aliases


def target_tables(tree: Expression) -> set[str]:
    return {table.name for table in tree.find_all(exp.Table) if table.name}


def add_table_references(
    tree: Expression,
    path: Path,
    starts: list[int],
    usage: SqlUsage,
) -> None:
    for table in tree.find_all(exp.Table):
        table_name = table.name
        if table_name:
            usage.add_table(table_name, reference(path, starts, table, "table reference"))


def add_insert_schema_columns(
    tree: Expression,
    path: Path,
    starts: list[int],
    usage: SqlUsage,
) -> None:
    if not isinstance(tree, exp.Insert) or not isinstance(tree.this, exp.Schema):
        return
    if not isinstance(tree.this.this, exp.Table):
        return

    table_name = tree.this.this.name
    for identifier in tree.this.expressions:
        if isinstance(identifier, exp.Identifier):
            usage.add_column(
                table_name,
                identifier.name,
                reference(path, starts, identifier, "insert column"),
            )


def resolved_table_for_column(
    column: exp.Column,
    aliases: dict[str, str],
    tables: set[str],
) -> str | None:
    qualifier = column.table
    if qualifier:
        return aliases.get(qualifier)
    if len(tables) == 1:
        return next(iter(tables))
    return None


def add_column_references(
    tree: Expression,
    path: Path,
    starts: list[int],
    usage: SqlUsage,
) -> None:
    aliases = table_aliases(tree)
    tables = target_tables(tree)

    for column in tree.find_all(exp.Column):
        table_name = resolved_table_for_column(column, aliases, tables)
        if table_name is None:
            if column.table:
                usage.unresolved_qualifiers[column.table].add(
                    reference(path, starts, column, f"{column.table}.{column.name}")
                )
            continue
        usage.add_column(
            table_name,
            column.name,
            reference(path, starts, column, column.sql(dialect="mysql")),
        )


def parse_sql_usage(sql: str, path: str | PathLike[str]) -> SqlUsage:
    sql_path = Path(path)
    starts = line_index(sql)
    usage = SqlUsage()

    for tree in sqlglot.parse(sql, read="mysql"):
        if tree is None:
            continue
        if not isinstance(tree, Expression):
            raise TypeError(f"SQLGlot returned unsupported expression: {type(tree).__name__}")
        add_table_references(tree, sql_path, starts, usage)
        add_insert_schema_columns(tree, sql_path, starts, usage)
        add_column_references(tree, sql_path, starts, usage)
    return usage


def collect_sql_usage(sql_dir: Path) -> SqlUsage:
    usage = SqlUsage()
    for sql_path in sorted(sql_dir.rglob("*.sql")):
        usage.merge(parse_sql_usage(sql_path.read_text(encoding="utf-8"), sql_path))
    return usage


def ddl_like_sources(ddl_sql: str) -> set[str]:
    sources: set[str] = set()
    for statement in sqlglot.parse(ddl_sql, read="mysql"):
        if not isinstance(statement, exp.Create) or statement.kind != "TABLE":
            continue
        properties = statement.args.get("properties")
        if not isinstance(properties, exp.Properties):
            continue
        for expression in properties.expressions:
            if isinstance(expression, exp.LikeProperty) and isinstance(expression.this, exp.Table):
                sources.add(expression.this.name)
    return sources


def compare_usage_to_ddl(usage: SqlUsage, ddl_sql: str) -> DriftReport:
    ddl_tables = parse_tables(ddl_sql)
    like_sources = ddl_like_sources(ddl_sql)
    ddl_columns = {
        table_name: {column.name for column in table.columns}
        for table_name, table in ddl_tables.items()
    }
    used_tables = set(usage.tables)

    missing_tables = used_tables - set(ddl_tables)
    missing_columns = {
        table: set(columns) - ddl_columns[table]
        for table, columns in usage.columns.items()
        if table in ddl_columns and set(columns) - ddl_columns[table]
    }
    ddl_only_tables = set(ddl_tables) - used_tables - like_sources - DDL_ONLY_TABLE_EXCEPTIONS
    ddl_only_columns = {
        table: ddl_columns[table] - set(usage.columns.get(table, {}))
        for table in sorted(set(ddl_tables) & used_tables)
        if ddl_columns[table] - set(usage.columns.get(table, {}))
    }

    return DriftReport(
        missing_tables=missing_tables,
        missing_columns=missing_columns,
        ddl_only_tables=ddl_only_tables,
        ddl_only_columns=ddl_only_columns,
        unresolved_qualifiers=dict(usage.unresolved_qualifiers),
    )


def format_references(references: set[SqlReference], limit: int = 3) -> str:
    rendered = [
        f"{reference.path.as_posix()}:{reference.line} ({reference.detail})"
        for reference in sorted(references)[:limit]
    ]
    remaining = len(references) - len(rendered)
    if remaining > 0:
        rendered.append(f"... +{remaining}")
    return ", ".join(rendered)


def render_report(report: DriftReport, usage: SqlUsage) -> str:
    lines: list[str] = ["# API SQL / DDL usage check", ""]

    if not report.has_drift():
        lines.append("No table or column drift found.")
        return "\n".join(lines)

    if report.missing_tables:
        lines.extend(["## SQL references missing DDL tables", ""])
        for table in sorted(report.missing_tables):
            lines.append(f"- `{table}`: {format_references(usage.tables[table])}")
        lines.append("")

    if report.missing_columns:
        lines.extend(["## SQL references missing DDL columns", ""])
        for table in sorted(report.missing_columns):
            columns = ", ".join(f"`{column}`" for column in sorted(report.missing_columns[table]))
            lines.append(f"- `{table}`: {columns}")
        lines.append("")

    if report.unresolved_qualifiers:
        lines.extend(["## SQL qualifiers that could not be resolved to tables", ""])
        for qualifier in sorted(report.unresolved_qualifiers):
            references = format_references(report.unresolved_qualifiers[qualifier])
            lines.append(f"- `{qualifier}`: {references}")
        lines.append("")

    if report.ddl_only_tables:
        lines.extend(["## DDL tables not referenced by API SQL", ""])
        for table in sorted(report.ddl_only_tables):
            lines.append(f"- `{table}`")
        lines.append("")

    if report.ddl_only_columns:
        lines.extend(["## DDL columns not referenced by API SQL", ""])
        for table in sorted(report.ddl_only_columns):
            columns = ", ".join(f"`{column}`" for column in sorted(report.ddl_only_columns[table]))
            lines.append(f"- `{table}`: {columns}")
        lines.append("")

    return "\n".join(lines).rstrip()


def check(api_sql_dir: Path, ddl_path: Path) -> tuple[DriftReport, SqlUsage]:
    usage = collect_sql_usage(api_sql_dir)
    report = compare_usage_to_ddl(usage, ddl_path.read_text(encoding="utf-8"))
    return report, usage


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check tables and columns used by API SQL against DDL definitions."
    )
    parser.add_argument("--api-sql-dir", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--ddl", type=Path, default=Path("src/db/ddl.sql"))
    parser.add_argument(
        "--no-fail-on-drift",
        action="store_true",
        help="Print the report but return exit code 0 even when drift is found.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    report, usage = check(args.api_sql_dir, args.ddl)
    print(render_report(report, usage))
    if report.has_drift() and not args.no_fail_on_drift:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
