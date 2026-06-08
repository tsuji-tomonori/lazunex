from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .models import RuleItem
from .rule_parser import parse_rules_dir, rule_markdown_files, strip_generated_blocks

START = "<!-- rulecheck:generated-checklist:start -->"
END = "<!-- rulecheck:generated-checklist:end -->"


def render_item(item: RuleItem) -> str:
    checker_text = ",".join(item.checkers) if item.checkers else "NO_CHECKER"
    return (
        f"- [ ] `{item.id}` **{item.level}** `[checker:{checker_text}]` "
        f"{item.text}  "
        f"`source:{item.source_ref}`"
    )


def render_embedded_block(items: list[RuleItem]) -> str:
    lines = [START, "", "## 自動生成チェックリスト", ""]
    if not items:
        lines.append("- [ ] `NO_RULES` このファイルに規約行はありません。")
    else:
        lines.extend(render_item(item) for item in items)
    lines.extend(["", END, ""])
    return "\n".join(lines)


def update_embedded_checklist(path: Path, rules_dir: Path, items: tuple[RuleItem, ...]) -> None:
    relative = path.relative_to(rules_dir)
    file_items = [item for item in items if item.source_path == relative]
    original = path.read_text(encoding="utf-8")
    stripped = strip_generated_blocks(original).rstrip() + "\n\n"
    path.write_text(stripped + render_embedded_block(file_items), encoding="utf-8")


def render_central_checklist(items: tuple[RuleItem, ...]) -> str:
    by_file: dict[Path, list[RuleItem]] = defaultdict(list)
    for item in items:
        by_file[item.source_path].append(item)

    lines = [
        "# 自動生成レビュー・チェックリスト",
        "",
        "このファイルは `rulecheck generate` で生成する。手動編集しない。",
        "",
        START,
        "",
    ]
    for source_path in sorted(by_file):
        lines.extend([f"## {source_path.as_posix()}", ""])
        lines.extend(render_item(item) for item in by_file[source_path])
        lines.append("")
    lines.extend([END, ""])
    return "\n".join(lines)


def generate(rules_dir: Path, checklist_path: Path) -> tuple[RuleItem, ...]:
    items = parse_rules_dir(rules_dir)
    for path in rule_markdown_files(rules_dir):
        update_embedded_checklist(path, rules_dir, items)
    checklist_path.parent.mkdir(parents=True, exist_ok=True)
    checklist_path.write_text(render_central_checklist(items), encoding="utf-8")
    return items


def expected_outputs(rules_dir: Path) -> tuple[tuple[RuleItem, ...], dict[Path, str], str]:
    items = parse_rules_dir(rules_dir)
    embedded: dict[Path, str] = {}
    for path in rule_markdown_files(rules_dir):
        relative = path.relative_to(rules_dir)
        file_items = [item for item in items if item.source_path == relative]
        stripped = strip_generated_blocks(path.read_text(encoding="utf-8")).rstrip() + "\n\n"
        embedded[path] = stripped + render_embedded_block(file_items)
    return items, embedded, render_central_checklist(items)


def verify_generated(rules_dir: Path, checklist_path: Path) -> list[str]:
    _, embedded, central = expected_outputs(rules_dir)
    errors: list[str] = []
    for path, expected in embedded.items():
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"{path}: embedded checklist is stale")
    if not checklist_path.exists():
        errors.append(f"{checklist_path}: checklist file is missing")
    elif checklist_path.read_text(encoding="utf-8") != central:
        errors.append(f"{checklist_path}: central checklist is stale")
    return errors
