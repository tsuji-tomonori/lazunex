from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import sqlglot
from sqlglot import exp

from tools.generate_db_table_specs import parse_tables, table_name
from tools.generation_io import check_outputs, write_outputs

CRUD_ORDER = ("C", "R", "U", "D")


def string_set() -> set[str]:
    return set()


@runtime_checkable
class HasFindAll(Protocol):
    def find_all(self, expression_type: type[Any]) -> Any: ...


@dataclass
class CrudMatrix:
    apis: set[str] = field(default_factory=string_set)
    tables: set[str] = field(default_factory=string_set)
    cells: dict[str, dict[str, set[str]]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(set))
    )

    def add(self, api: str, table: str, operation: str) -> None:
        self.apis.add(api)
        self.tables.add(table)
        self.cells[api][table].add(operation)


def operation_label(operations: set[str]) -> str:
    return "".join(operation for operation in CRUD_ORDER if operation in operations)


def statement_table_name(expression: Any) -> str:
    return table_name(expression)


def read_tables_from_ddl(ddl_path: Path) -> list[str]:
    tables = parse_tables(ddl_path.read_text(encoding="utf-8"))
    return sorted(tables)


def api_name_from_sql_path(sql_path: Path, api_sql_dir: Path) -> str:
    relative = sql_path.relative_to(api_sql_dir)
    parts = relative.parts
    if len(parts) < 3 or parts[-2] != "sql":
        raise ValueError(f"SQL file must be under an API sql directory: {sql_path}")
    return parts[-3]


def select_tables(statement: exp.Select) -> set[str]:
    return {statement_table_name(table) for table in statement.find_all(exp.Table)}


def mutation_target(statement: Any) -> str | None:
    target = statement.this
    if target is None:
        return None
    return statement_table_name(target)


def expression_tables(value: object) -> set[str]:
    if isinstance(value, list):
        expressions = cast(list[Any], value)  # type: ignore[redundant-cast]
        return {
            statement_table_name(table)
            for expression in expressions
            if isinstance(expression, HasFindAll)
            for table in expression.find_all(exp.Table)
        }
    if isinstance(value, HasFindAll):
        return {statement_table_name(table) for table in value.find_all(exp.Table)}
    return set()


def statement_operations(statement: Any) -> dict[str, set[str]]:
    operations: dict[str, set[str]] = defaultdict(set)

    for select in statement.find_all(exp.Select):
        for table in select_tables(select):
            operations[table].add("R")

    if isinstance(statement, exp.Insert):
        target = mutation_target(statement)
        if target is not None:
            operations[target].add("C")
    elif isinstance(statement, exp.Update):
        target = mutation_target(statement)
        if target is not None:
            operations[target].add("U")
    elif isinstance(statement, exp.Delete):
        target = mutation_target(statement)
        if target is not None:
            operations[target].add("D")

        using = statement.args.get("using")
        for table in expression_tables(using):
            operations[table].add("R")

    return operations


def sql_operations(sql: str) -> dict[str, set[str]]:
    operations: dict[str, set[str]] = defaultdict(set)
    for statement in sqlglot.parse(sql, read="mysql"):
        if statement is None:
            continue
        for table, table_operations in statement_operations(statement).items():
            operations[table].update(table_operations)
    return operations


def collect_crud(api_sql_dir: Path, tables: list[str]) -> CrudMatrix:
    matrix = CrudMatrix(tables=set(tables))
    known_tables = set(tables)

    for sql_path in sorted(api_sql_dir.rglob("*.sql")):
        api = api_name_from_sql_path(sql_path, api_sql_dir)
        matrix.apis.add(api)
        operations = sql_operations(sql_path.read_text(encoding="utf-8"))
        for table, table_operations in operations.items():
            if table not in known_tables:
                continue
            for operation in table_operations:
                matrix.add(api, table, operation)

    return matrix


def render_csv(matrix: CrudMatrix, tables: list[str]) -> str:
    rows: list[list[str]] = [["api", *tables]]
    for api in sorted(matrix.apis):
        api_cells = matrix.cells.get(api, {})
        rows.append(
            [
                api,
                *[operation_label(api_cells.get(table, set())) for table in tables],
            ]
        )

    output: list[str] = []
    for row in rows:
        output.append(",".join(csv_escape(value) for value in row))
    return "\n".join(output) + "\n"


def csv_escape(value: str) -> str:
    if any(char in value for char in {",", '"', "\n"}):
        return '"' + value.replace('"', '""') + '"'
    return value


def write_crud_csv(matrix: CrudMatrix, tables: list[str], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_csv(matrix, tables), encoding="utf-8")
    return output_path


def generate(api_sql_dir: Path, ddl_path: Path, output_path: Path) -> Path:
    rendered = render_output(api_sql_dir, ddl_path, output_path)
    write_outputs(rendered)
    return output_path


def render_output(api_sql_dir: Path, ddl_path: Path, output_path: Path) -> dict[Path, str]:
    tables = read_tables_from_ddl(ddl_path)
    matrix = collect_crud(api_sql_dir, tables)
    return {output_path: render_csv(matrix, tables)}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate API x DB table CRUD CSV from SQL files.")
    parser.add_argument("--api-sql-dir", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--ddl", type=Path, default=Path("src/db/ddl.sql"))
    parser.add_argument("--output", type=Path, default=Path("docs/spec/30.crud/db_crud.gen.csv"))
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    rendered = render_output(args.api_sql_dir, args.ddl, args.output)
    if args.check:
        return check_outputs(rendered)
    write_outputs(rendered)
    print(f"Generated {args.output.as_posix()}.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
