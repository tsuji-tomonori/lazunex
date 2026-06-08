from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from .models import RuleItem

NORMATIVE_RE = re.compile(
    r"^\s*-\s+\*\*(MUST NOT|SHOULD NOT|MUST|SHOULD|MAY)\*\*\s*:??\s*(?P<body>.*)$"
)
CHECKER_RE = re.compile(r"\[checker:([^\]]+)\]")
CHECKER_CELL_RE = re.compile(r"`?([^`,\s]+)`?")
GENERATED_BLOCK_RE = re.compile(
    r"\n?<!-- rulecheck:generated-checklist:start -->.*?<!-- rulecheck:generated-checklist:end -->\n?",
    re.DOTALL,
)


def strip_generated_blocks(text: str) -> str:
    return GENERATED_BLOCK_RE.sub("\n", text)


def checker_names(body: str) -> tuple[str, ...]:
    names: list[str] = []
    for match in CHECKER_RE.finditer(body):
        for name in match.group(1).split(","):
            cleaned = name.strip().strip("` ")
            if cleaned:
                names.append(cleaned)
    return tuple(dict.fromkeys(names))


def clean_rule_text(body: str) -> str:
    body = re.sub(r"`?\[checker:[^\]]+\]`?", "", body)
    body = body.replace("``", "`")
    return body.strip(" :-")


def clean_table_cell(value: str) -> str:
    return value.strip().replace(r"\|", "|")


def table_checker_names(value: str) -> tuple[str, ...]:
    names: list[str] = []
    for raw in value.split(","):
        match = CHECKER_CELL_RE.fullmatch(clean_table_cell(raw).strip("` "))
        if match:
            names.append(match.group(1))
    return tuple(dict.fromkeys(names))


def _rule_id(path: Path, line_number: int, index: int) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_").upper()
    return f"RULE-{stem}-L{line_number:03d}-{index:02d}"


def _table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped.strip("|"))]
    return cells if len(cells) >= 5 else None


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _parse_table_rule(
    path: Path,
    line_number: int,
    index: int,
    cells: list[str],
) -> RuleItem | None:
    if _is_separator_row(cells):
        return None
    first = clean_table_cell(cells[0]).strip("` ")
    if first.lower() in {"rule id", "id"}:
        return None
    level = clean_table_cell(cells[1]).strip("` ")
    if level not in {"MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY"}:
        return None
    checkers = table_checker_names(cells[2])
    target = clean_table_cell(cells[3])
    condition = clean_table_cell(cells[4])
    text = f"{target}: {condition}" if target and target != "-" else condition
    return RuleItem(
        id=first or _rule_id(path, line_number, index),
        level=level,  # type: ignore[arg-type]
        text=text,
        source_path=path,
        line_number=line_number,
        checkers=checkers,
    )


def parse_rule_file(path: Path, root: Path | None = None) -> list[RuleItem]:
    text = strip_generated_blocks(path.read_text(encoding="utf-8"))
    relative = path.relative_to(root) if root is not None else path
    items: list[RuleItem] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = NORMATIVE_RE.match(line)
        if not match:
            continue
        level = match.group(1)
        body = match.group("body")
        item = RuleItem(
            id=_rule_id(relative, line_number, len(items) + 1),
            level=level,  # type: ignore[arg-type]
            text=clean_rule_text(body),
            source_path=relative,
            line_number=line_number,
            checkers=checker_names(body),
        )
        items.append(item)
        continue
    for line_number, line in enumerate(text.splitlines(), start=1):
        cells = _table_cells(line)
        if cells is None:
            continue
        item = _parse_table_rule(relative, line_number, len(items) + 1, cells)
        if item is not None:
            items.append(item)
    return items


def rule_markdown_files(rules_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in rules_dir.glob("*.md")
        if "review_checklist" not in path.name
        and not path.name.endswith(".generated.md")
        and path.name != "README_FOR_DEVELOPERS.md"
    )


def parse_rules_dir(rules_dir: Path) -> tuple[RuleItem, ...]:
    items: list[RuleItem] = []
    for path in rule_markdown_files(rules_dir):
        items.extend(parse_rule_file(path, rules_dir))
    return tuple(items)


def normative_lines_without_checker(rules_dir: Path) -> list[tuple[Path, int, str]]:
    missing: list[tuple[Path, int, str]] = []
    for path in rule_markdown_files(rules_dir):
        text = strip_generated_blocks(path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = NORMATIVE_RE.match(line)
            if not match:
                cells = _table_cells(line)
                if cells is None:
                    continue
                item = _parse_table_rule(path, line_number, 1, cells)
                if item is not None and not item.checkers:
                    missing.append((path, line_number, line.strip()))
                continue
            if not checker_names(match.group("body")):
                missing.append((path, line_number, line.strip()))
    return missing


def iter_normative_lines(rules_dir: Path) -> Iterable[tuple[Path, int, str]]:
    for path in rule_markdown_files(rules_dir):
        text = strip_generated_blocks(path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), start=1):
            if NORMATIVE_RE.match(line):
                yield path, line_number, line.strip()
                continue
            cells = _table_cells(line)
            if cells is None:
                continue
            item = _parse_table_rule(path, line_number, 1, cells)
            if item is not None:
                yield path, line_number, item.text
