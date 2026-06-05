from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from tools.generate_db_table_specs import Column, Table, parse_tables


@dataclass(frozen=True)
class Relationship:
    child_table: str
    child_columns: tuple[str, ...]
    parent_table: str
    parent_columns: tuple[str, ...]
    constraint_name: str = ""


def normalize_identifier(value: str) -> str:
    """Normalize a DDL identifier to the repository's table/column naming form."""

    normalized = value.strip().strip('"')
    if "." in normalized:
        normalized = normalized.split(".")[-1].strip().strip('"')
    return normalized.lower()


def split_identifier_list(value: str) -> tuple[str, ...]:
    """Split a comma-separated identifier list from a FK/unique constraint."""

    return tuple(
        normalize_identifier(identifier) for identifier in value.split(",") if identifier.strip()
    )


def strip_sql_line_comments(sql: str) -> str:
    """Remove SQL line comments before regex-based constraint extraction."""

    return re.sub(r"--.*$", "", sql, flags=re.MULTILINE)


def parse_reference_target(reference: str) -> tuple[str, tuple[str, ...]] | None:
    """Parse a sqlglot reference label such as ``apis(api_id)``."""

    match = re.match(
        r"^(?:REFERENCES\s+)?(?P<table>[\w\".]+)\s*(?:\((?P<columns>[^)]*)\))?$",
        reference.strip(),
        flags=re.IGNORECASE,
    )
    if match is None:
        return None

    columns = match.group("columns")
    return (
        normalize_identifier(match.group("table")),
        split_identifier_list(columns) if columns else (),
    )


def primary_key_columns(table: Table) -> tuple[str, ...]:
    """Return primary-key columns for a table."""

    return tuple(column.name for column in table.columns if column.primary_key)


def table_column(table: Table, column_name: str) -> Column | None:
    """Return one column by name."""

    for column in table.columns:
        if column.name == column_name:
            return column
    return None


def relationship_with_default_parent_columns(
    relationship: Relationship,
    tables: dict[str, Table],
) -> Relationship:
    """Fill omitted parent columns with the parent table primary key."""

    if relationship.parent_columns:
        return relationship

    parent = tables.get(relationship.parent_table)
    if parent is None:
        return relationship

    return Relationship(
        child_table=relationship.child_table,
        child_columns=relationship.child_columns,
        parent_table=relationship.parent_table,
        parent_columns=primary_key_columns(parent),
        constraint_name=relationship.constraint_name,
    )


def add_relationship(
    relationships: dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship],
    relationship: Relationship,
    tables: dict[str, Table],
) -> None:
    """Add one relationship after filling defaults and removing duplicates."""

    normalized = relationship_with_default_parent_columns(relationship, tables)
    key = (
        normalized.child_table,
        normalized.child_columns,
        normalized.parent_table,
        normalized.parent_columns,
    )

    current = relationships.get(key)
    if current is None or (not current.constraint_name and normalized.constraint_name):
        relationships[key] = normalized


def parse_inline_relationships(
    tables: dict[str, Table],
) -> dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship]:
    """Extract inline ``REFERENCES`` relationships from parsed table columns."""

    relationships: dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship] = {}

    for table in tables.values():
        for column in table.columns:
            if column.references is None:
                continue

            target = parse_reference_target(column.references)
            if target is None:
                continue

            parent_table, parent_columns = target
            add_relationship(
                relationships,
                Relationship(
                    child_table=table.name,
                    child_columns=(column.name,),
                    parent_table=parent_table,
                    parent_columns=parent_columns,
                ),
                tables,
            )

    return relationships


FOREIGN_KEY_CONSTRAINT_RE = re.compile(
    r"(?:CONSTRAINT\s+(?P<constraint>[\w\"]+)\s+)?"
    r"FOREIGN\s+KEY\s*\((?P<child_columns>[^)]*)\)\s+"
    r"REFERENCES\s+(?P<parent_table>[\w\".]+)\s*"
    r"(?:\((?P<parent_columns>[^)]*)\))?",
    flags=re.IGNORECASE | re.DOTALL,
)

ALTER_TABLE_FOREIGN_KEY_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<child_table>[\w\".]+)\s+"
    r"ADD\s+"
    r"(?:CONSTRAINT\s+(?P<constraint>[\w\"]+)\s+)?"
    r"FOREIGN\s+KEY\s*\((?P<child_columns>[^)]*)\)\s+"
    r"REFERENCES\s+(?P<parent_table>[\w\".]+)\s*"
    r"(?:\((?P<parent_columns>[^)]*)\))?",
    flags=re.IGNORECASE | re.DOTALL,
)


def parse_table_constraint_relationships(
    tables: dict[str, Table],
) -> dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship]:
    """Extract table-level FK relationships inside ``CREATE TABLE`` bodies."""

    relationships: dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship] = {}

    for table in tables.values():
        for constraint in table.table_constraints:
            match = FOREIGN_KEY_CONSTRAINT_RE.search(constraint)
            if match is None:
                continue

            add_relationship(
                relationships,
                Relationship(
                    child_table=table.name,
                    child_columns=split_identifier_list(match.group("child_columns")),
                    parent_table=normalize_identifier(match.group("parent_table")),
                    parent_columns=split_identifier_list(match.group("parent_columns") or ""),
                    constraint_name=normalize_identifier(match.group("constraint") or ""),
                ),
                tables,
            )

    return relationships


def parse_alter_table_relationships(
    sql: str,
    tables: dict[str, Table],
) -> dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship]:
    """Extract FK relationships declared by ``ALTER TABLE ... ADD CONSTRAINT``."""

    relationships: dict[tuple[str, tuple[str, ...], str, tuple[str, ...]], Relationship] = {}

    for match in ALTER_TABLE_FOREIGN_KEY_RE.finditer(strip_sql_line_comments(sql)):
        add_relationship(
            relationships,
            Relationship(
                child_table=normalize_identifier(match.group("child_table")),
                child_columns=split_identifier_list(match.group("child_columns")),
                parent_table=normalize_identifier(match.group("parent_table")),
                parent_columns=split_identifier_list(match.group("parent_columns") or ""),
                constraint_name=normalize_identifier(match.group("constraint") or ""),
            ),
            tables,
        )

    return relationships


def parse_relationships(sql: str, tables: dict[str, Table]) -> list[Relationship]:
    """Extract all FK relationships that should appear on the ER diagram."""

    relationships = parse_inline_relationships(tables)

    for source in (
        parse_table_constraint_relationships(tables),
        parse_alter_table_relationships(sql, tables),
    ):
        for relationship in source.values():
            add_relationship(relationships, relationship, tables)

    return sorted(
        relationships.values(),
        key=lambda relationship: (
            relationship.parent_table,
            relationship.child_table,
            relationship.child_columns,
            relationship.parent_columns,
        ),
    )


def unique_key_column_sets(table: Table) -> set[tuple[str, ...]]:
    """Return all single and composite unique key column sets for a table."""

    column_sets: set[tuple[str, ...]] = {
        (column.name,) for column in table.columns if column.primary_key or column.unique
    }

    for constraint in table.table_constraints:
        match = re.search(
            r"(?:PRIMARY\s+KEY|UNIQUE)\s*\((?P<columns>[^)]*)\)",
            constraint,
            flags=re.IGNORECASE,
        )
        if match is not None:
            column_sets.add(split_identifier_list(match.group("columns")))

    return column_sets


def child_columns_are_unique(table: Table, column_names: tuple[str, ...]) -> bool:
    """Return whether the FK columns identify at most one child row per parent row."""

    return column_names in unique_key_column_sets(table)


def child_columns_are_nullable(table: Table, column_names: tuple[str, ...]) -> bool:
    """Return whether at least one FK column is nullable."""

    for column_name in column_names:
        column = table_column(table, column_name)
        if column is None or column.nullable:
            return True
    return False


def relationship_cardinality(
    relationship: Relationship,
    tables: dict[str, Table],
) -> tuple[str, str]:
    """Return Mermaid cardinalities as ``(parent_side, child_side)``."""

    child_table = tables[relationship.child_table]
    parent_side = (
        "o|" if child_columns_are_nullable(child_table, relationship.child_columns) else "||"
    )
    child_side = "o|" if child_columns_are_unique(child_table, relationship.child_columns) else "o{"
    return parent_side, child_side


def mermaid_data_type(data_type: str) -> str:
    """Normalize a SQL type into a Mermaid-safe ER attribute type."""

    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", data_type.lower()).strip("_")
    return re.sub(r"_+", "_", normalized) or "unknown"


def column_key_label(column: Column, fk_columns: set[str]) -> str:
    """Render Mermaid PK/FK/UK markers for one column."""

    keys: list[str] = []
    if column.primary_key:
        keys.append("PK")
    if column.unique and not column.primary_key:
        keys.append("UK")
    if column.name in fk_columns:
        keys.append("FK")
    return f" {', '.join(keys)}" if keys else ""


def relationship_label(relationship: Relationship) -> str:
    """Render a compact Mermaid relationship label."""

    if relationship.constraint_name:
        return relationship.constraint_name
    if relationship.child_columns:
        return "_".join(relationship.child_columns)
    return "rel"


def fk_columns_by_table(relationships: list[Relationship]) -> dict[str, set[str]]:
    """Map table names to columns that participate in FK relationships."""

    columns_by_table: dict[str, set[str]] = {}
    for relationship in relationships:
        columns_by_table.setdefault(relationship.child_table, set()).update(
            relationship.child_columns,
        )
    return columns_by_table


def render_mermaid(tables: dict[str, Table], relationships: list[Relationship]) -> str:
    """Render a Mermaid ER diagram from parsed DDL tables and relationships."""

    fk_columns = fk_columns_by_table(relationships)
    lines = ["erDiagram"]

    for table_name in sorted(tables):
        table = tables[table_name]
        lines.append(f"  {table.name} {{")
        for column in table.columns:
            lines.append(
                "    "
                f"{mermaid_data_type(column.data_type)} "
                f"{column.name}"
                f"{column_key_label(column, fk_columns.get(table.name, set()))}"
            )
        lines.append("  }")

    for relationship in relationships:
        parent_side, child_side = relationship_cardinality(relationship, tables)
        lines.append(
            "  "
            f"{relationship.parent_table} {parent_side}--{child_side} "
            f"{relationship.child_table} : {relationship_label(relationship)}"
        )

    lines.append("")
    return "\n".join(lines)


def render_markdown(
    tables: dict[str, Table],
    relationships: list[Relationship],
    ddl_path: Path,
) -> str:
    """Render a Markdown wrapper around the Mermaid ER diagram."""

    return "\n".join(
        [
            "<!-- AUTO-GENERATED by src/tools/generate_db_er_diagram.py. DO NOT EDIT. -->",
            "",
            "# ER図",
            "",
            f"正本DDL: `{ddl_path.as_posix()}`",
            "",
            "```mermaid",
            render_mermaid(tables, relationships).rstrip(),
            "```",
            "",
        ]
    )


def infer_output_format(output_path: Path) -> str:
    """Infer output format from the file suffix."""

    if output_path.suffix.lower() in {".mmd", ".mermaid"}:
        return "mermaid"
    return "markdown"


def write_er_diagram(
    tables: dict[str, Table],
    relationships: list[Relationship],
    ddl_path: Path,
    output_path: Path,
    output_format: str,
) -> Path:
    """Write the ER diagram to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "mermaid":
        content = render_mermaid(tables, relationships)
    else:
        content = render_markdown(tables, relationships, ddl_path)

    output_path.write_text(content, encoding="utf-8")
    return output_path


def generate(ddl_path: Path, output_path: Path, output_format: str | None = None) -> Path:
    """Generate an ER diagram from the DDL file."""

    sql = ddl_path.read_text(encoding="utf-8")
    tables = parse_tables(sql)
    relationships = parse_relationships(sql, tables)
    return write_er_diagram(
        tables,
        relationships,
        ddl_path,
        output_path,
        output_format or infer_output_format(output_path),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Mermaid ER diagram from DDL.")
    parser.add_argument("--ddl", type=Path, default=Path("src/db/ddl.sql"))
    parser.add_argument("--output", type=Path, default=Path("docs/spec/20.db/er.gen.md"))
    parser.add_argument(
        "--format",
        choices=["markdown", "mermaid"],
        help="Output format. Defaults to mermaid for .mmd/.mermaid, otherwise markdown.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    output_path = generate(args.ddl, args.output, args.format)
    print(f"Generated ER diagram: {output_path.as_posix()}")


if __name__ == "__main__":  # pragma: no cover
    main()
