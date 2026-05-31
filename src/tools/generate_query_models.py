import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from tools.generate_db_table_specs import Column, Table, parse_tables, table_name

PLACEHOLDER_RE = re.compile(r":(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)")
SQL_PREFIX_RE = re.compile(r"^\d+_")


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_hint: str
    nullable: bool = False


@dataclass(frozen=True)
class QuerySpec:
    class_prefix: str
    params: list[FieldSpec]
    rows: list[FieldSpec]


def python_identifier(value: str) -> str:
    cleaned = re.sub(r"\W+", "_", value).strip("_").lower()
    if not cleaned:
        return "value"
    if cleaned[0].isdigit():
        return f"field_{cleaned}"
    return cleaned


def pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in python_identifier(value).split("_"))


def class_prefix_from_sql_path(sql_path: Path) -> str:
    stem = SQL_PREFIX_RE.sub("", sql_path.stem)
    return pascal_case(stem)


def base_type_from_sql(data_type: str) -> str:
    normalized = data_type.upper()
    if normalized.startswith("UUID"):
        return "UUID"
    if normalized.startswith(("VARCHAR", "TEXT", "CHAR")):
        return "str"
    if normalized.startswith(("INT", "BIGINT", "SMALLINT")):
        return "int"
    if normalized.startswith(("NUMERIC", "DECIMAL", "DOUBLE", "REAL")):
        return "Decimal"
    if normalized.startswith(("BOOL", "BOOLEAN")):
        return "bool"
    if normalized.startswith("DATE") and not normalized.startswith("DATETIME"):
        return "date"
    if normalized.startswith(("TIMESTAMP", "TIMESTAMPTZ", "DATETIME")):
        return "datetime"
    if normalized.startswith(("JSON", "JSONB")):
        return "dict[str, Any]"
    return "Any"


def model_type(type_hint: str, nullable: bool) -> str:
    if nullable and type_hint != "Any":
        return f"{type_hint} | None"
    return type_hint


def ddl_column_index(tables: dict[str, Table]) -> dict[str, dict[str, Column]]:
    return {
        table_name: {column.name: column for column in table.columns}
        for table_name, table in tables.items()
    }


def unique_column_index(tables: dict[str, Table]) -> dict[str, Column]:
    columns: dict[str, list[Column]] = defaultdict(list)
    for table in tables.values():
        for column in table.columns:
            columns[column.name].append(column)
    return {name: matches[0] for name, matches in columns.items() if len(matches) == 1}


def field_from_column(name: str, column: Column | None, nullable: bool | None = None) -> FieldSpec:
    if column is None:
        return FieldSpec(name=python_identifier(name), type_hint="Any", nullable=False)
    return FieldSpec(
        name=python_identifier(name),
        type_hint=base_type_from_sql(column.data_type),
        nullable=column.nullable if nullable is None else nullable,
    )


def table_aliases(statement: Any) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table in statement.find_all(exp.Table):
        aliases[table.name] = table.name
        aliases[table.alias_or_name] = table.name
    return aliases


def resolve_column(
    column: exp.Column, aliases: dict[str, str], columns: dict[str, dict[str, Column]]
) -> Column | None:
    if column.table:
        table = aliases.get(column.table, column.table)
        return columns.get(table, {}).get(column.name)

    alias_tables = set(aliases.values())
    if len(alias_tables) == 1:
        table = next(iter(alias_tables))
        if column.name in columns.get(table, {}):
            return columns[table][column.name]

    matches = [
        table_columns[column.name]
        for table_columns in columns.values()
        if column.name in table_columns
    ]
    return matches[0] if len(matches) == 1 else None


def output_field(
    expression: Any, aliases: dict[str, str], columns: dict[str, dict[str, Column]]
) -> FieldSpec:
    if isinstance(expression, exp.Alias):
        alias = python_identifier(expression.alias)
        if isinstance(expression.this, exp.Column):
            return field_from_column(alias, resolve_column(expression.this, aliases, columns))
        return FieldSpec(name=alias, type_hint="Any")

    if isinstance(expression, exp.Column):
        return field_from_column(
            expression.alias_or_name,
            resolve_column(expression, aliases, columns),
        )

    name = python_identifier(expression.alias_or_name or "value")
    return FieldSpec(name=name, type_hint="Any")


def select_output_fields(
    statement: exp.Select, columns: dict[str, dict[str, Column]]
) -> list[FieldSpec]:
    aliases = table_aliases(statement)
    return [output_field(expression, aliases, columns) for expression in statement.expressions]


def mutation_target_table(statement: Any) -> str | None:
    target = statement.this
    if target is None:
        return None
    return table_name(target)


def returning_output_fields(
    statement: Any, columns: dict[str, dict[str, Column]]
) -> list[FieldSpec]:
    returning = statement.args.get("returning")
    target = mutation_target_table(statement)
    if returning is None:
        return []

    if target is None:
        return [output_field(expression, {}, columns) for expression in returning.expressions]

    target_columns = {target: columns.get(target, {})}
    return [
        output_field(expression, {target: target}, target_columns)
        for expression in returning.expressions
    ]


def placeholder_names(sql: str) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for match in PLACEHOLDER_RE.finditer(sql):
        name = match.group("name")
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def collect_insert_param_columns(
    statement: exp.Insert, columns: dict[str, dict[str, Column]]
) -> dict[str, Column]:
    if not isinstance(statement.this, exp.Schema):
        return {}

    target = table_name(statement.this)
    target_columns = columns.get(target, {})
    insert_columns = [column.name for column in statement.this.expressions]
    values = statement.args.get("expression")
    if not isinstance(values, exp.Values) or not values.expressions:
        return {}

    first_tuple = values.expressions[0]
    if not isinstance(first_tuple, exp.Tuple):
        return {}

    param_columns: dict[str, Column] = {}
    for column_name, value in zip(insert_columns, first_tuple.expressions, strict=False):
        placeholders = list(value.find_all(exp.Placeholder))
        if len(placeholders) == 1 and column_name in target_columns:
            param_columns[placeholders[0].name] = target_columns[column_name]
    return param_columns


def collect_update_param_columns(
    statement: exp.Update, columns: dict[str, dict[str, Column]]
) -> dict[str, Column]:
    param_columns: dict[str, Column] = {}
    target = mutation_target_table(statement)
    target_columns = columns.get(target, {}) if target is not None else {}
    for assignment in statement.expressions:
        if not isinstance(assignment, exp.EQ) or not isinstance(assignment.this, exp.Column):
            continue
        placeholders = list(assignment.expression.find_all(exp.Placeholder))
        column = target_columns.get(assignment.this.name)
        if len(placeholders) == 1 and column is not None:
            param_columns[placeholders[0].name] = column
    return param_columns


def collect_comparison_param_columns(
    statement: Any, columns: dict[str, dict[str, Column]]
) -> dict[str, Column]:
    param_columns: dict[str, Column] = {}
    aliases = table_aliases(statement)
    for comparison in statement.find_all(exp.EQ):
        left = comparison.this
        right = comparison.expression
        if isinstance(left, exp.Column) and isinstance(right, exp.Placeholder):
            column = resolve_column(left, aliases, columns)
            if column is not None:
                param_columns[right.name] = column
        elif isinstance(right, exp.Column) and isinstance(left, exp.Placeholder):
            column = resolve_column(right, aliases, columns)
            if column is not None:
                param_columns[left.name] = column
    return param_columns


def infer_param_fields(
    sql: str,
    statements: list[Any],
    tables: dict[str, Table],
) -> list[FieldSpec]:
    unique_columns = unique_column_index(tables)
    columns = ddl_column_index(tables)
    param_columns: dict[str, Column] = {}

    for statement in statements:
        if isinstance(statement, exp.Insert):
            param_columns.update(collect_insert_param_columns(statement, columns))
        elif isinstance(statement, exp.Update):
            param_columns.update(collect_update_param_columns(statement, columns))
        param_columns.update(collect_comparison_param_columns(statement, columns))

    fields: list[FieldSpec] = []
    for name in placeholder_names(sql):
        column = param_columns.get(name, unique_columns.get(name))
        fields.append(field_from_column(name, column, nullable=False))
    return fields


def infer_row_fields(statements: list[Any], tables: dict[str, Table]) -> list[FieldSpec]:
    columns = ddl_column_index(tables)
    for statement in statements:
        if isinstance(statement, exp.Select):
            return select_output_fields(statement, columns)
        if isinstance(statement, (exp.Insert, exp.Update, exp.Delete)):
            fields = returning_output_fields(statement, columns)
            if fields:
                return fields
    return []


def parse_query_spec(sql_path: Path, tables: dict[str, Table]) -> QuerySpec:
    sql = sql_path.read_text(encoding="utf-8")
    statements = [
        statement for statement in sqlglot.parse(sql, read="postgres") if statement is not None
    ]
    return QuerySpec(
        class_prefix=class_prefix_from_sql_path(sql_path),
        params=infer_param_fields(sql, statements, tables),
        rows=infer_row_fields(statements, tables),
    )


def api_sql_dirs(api_root: Path) -> list[Path]:
    return sorted(path for path in api_root.glob("*/*/sql") if path.is_dir())


def render_model_class(name: str, fields: list[FieldSpec]) -> list[str]:
    lines = [
        f"class {name}(BaseModel):",
        '    model_config = ConfigDict(extra="forbid")',
    ]
    if not fields:
        lines.append("    pass")
        return lines

    for field in fields:
        default = " = None" if field.nullable else ""
        lines.append(f"    {field.name}: {model_type(field.type_hint, field.nullable)}{default}")
    return lines


def required_imports(specs: list[QuerySpec]) -> list[str]:
    type_hints = {field.type_hint for spec in specs for field in [*spec.params, *spec.rows]}
    imports: list[str] = []
    datetime_imports = [name for name in ("date", "datetime") if name in type_hints]
    if datetime_imports:
        imports.append(f"from datetime import {', '.join(datetime_imports)}")
    if "Decimal" in type_hints:
        imports.append("from decimal import Decimal")
    if "Any" in type_hints or "dict[str, Any]" in type_hints:
        imports.append("from typing import Any")
    if "UUID" in type_hints:
        imports.append("from uuid import UUID")
    imports.extend(["", "from pydantic import BaseModel, ConfigDict", ""])
    return imports


def render_queries_py(specs: list[QuerySpec]) -> str:
    lines = required_imports(specs)
    lines.extend(
        [
            "# This file is generated from SQL files in the sibling sql directory.",
            "# Do not edit generated models by hand.",
            "",
        ]
    )

    for index, spec in enumerate(specs):
        if index > 0:
            lines.append("")
        lines.extend(render_model_class(f"{spec.class_prefix}Params", spec.params))
        if spec.rows:
            lines.append("")
            lines.extend(render_model_class(f"{spec.class_prefix}Row", spec.rows))

    lines.append("")
    return "\n".join(lines)


def generate_queries(api_root: Path, ddl_path: Path) -> list[Path]:
    tables = parse_tables(ddl_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for sql_dir in api_sql_dirs(api_root):
        specs = [parse_query_spec(sql_path, tables) for sql_path in sorted(sql_dir.glob("*.sql"))]
        output_path = sql_dir.parent / "queries.py"
        output_path.write_text(render_queries_py(specs), encoding="utf-8")
        written.append(output_path)

    return written


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Pydantic query models from API SQL files."
    )
    parser.add_argument("--api-root", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--ddl", type=Path, default=Path("src/db/ddl.sql"))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    written = generate_queries(args.api_root, args.ddl)
    print(f"Generated {len(written)} queries.py files.")


if __name__ == "__main__":  # pragma: no cover
    main()
