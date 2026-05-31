from __future__ import annotations

import argparse
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

MERMAID_BLOCK_PATTERN = re.compile(r"```mermaid\n(?P<body>.*?)\n```", re.DOTALL)
PARTICIPANT_PATTERN = re.compile(
    r"^\s*participant\s+(?P<id>[A-Za-z][A-Za-z0-9_]*)\s+as\s+[^:]+(?::\s+.+)?$"
)
MESSAGE_PATTERN = re.compile(
    r"^\s*(?P<source>[A-Za-z][A-Za-z0-9_]*)"
    r"(?:->>|-->>|->|-->|-\)|--\)|-x|--x)"
    r"(?P<target>[A-Za-z][A-Za-z0-9_]*):\s*(?P<label>.+)$"
)
SQL_MESSAGE_PATTERN = re.compile(
    r"^\s*API->>DB:\s*レコードを(?:参照|追加|更新|削除)する"
    r"\s+SQL\s+(?P<filename>\S+)<br/>テーブル\s+(?P<tables>.+)$"
)
ALLOWED_SEQUENCE_LINES = {
    "sequenceDiagram",
    "autonumber",
    "end",
}


@dataclass(frozen=True)
class MermaidIssue:
    path: Path
    line: int
    message: str


def mermaid_blocks(source: str) -> list[tuple[int, list[str]]]:
    blocks: list[tuple[int, list[str]]] = []
    for match in MERMAID_BLOCK_PATTERN.finditer(source):
        start_line = source.count("\n", 0, match.start("body")) + 1
        blocks.append((start_line, match.group("body").splitlines()))
    return blocks


def has_message_separator(label: str) -> bool:
    return ":" in label or "\uff1a" in label


def has_unsafe_label_delimiter(label: str) -> bool:
    return any(character in label for character in ("(", ")", ";"))


def has_signature_detail(label: str) -> bool:
    return "引数" in label or "戻り値" in label


def validate_sequence_block(
    path: Path,
    start_line: int,
    lines: list[str],
) -> list[MermaidIssue]:
    issues: list[MermaidIssue] = []
    participants: set[str] = set()
    sql_filenames: set[str] = set()

    if not lines or lines[0].strip() != "sequenceDiagram":
        return [
            MermaidIssue(
                path=path,
                line=start_line,
                message="Mermaid block must start with sequenceDiagram.",
            )
        ]

    for index, line in enumerate(lines, start=start_line):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in ALLOWED_SEQUENCE_LINES:
            continue
        if stripped.startswith("alt "):
            if has_message_separator(stripped.removeprefix("alt ")):
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message="alt condition must not contain ':' or fullwidth colon.",
                    )
                )
            continue

        participant_match = PARTICIPANT_PATTERN.match(line)
        if participant_match:
            participant_id = participant_match.group("id")
            if participant_id in participants:
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message=f"Duplicate participant '{participant_id}'.",
                    )
                )
            participants.add(participant_id)
            continue

        message_match = MESSAGE_PATTERN.match(line)
        if message_match:
            source = message_match.group("source")
            target = message_match.group("target")
            label = message_match.group("label")
            if source not in participants:
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message=f"Unknown message source participant '{source}'.",
                    )
                )
            if target not in participants:
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message=f"Unknown message target participant '{target}'.",
                    )
                )
            if has_message_separator(label):
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message="Message label must not contain ':' or fullwidth colon.",
                    )
                )
            if has_unsafe_label_delimiter(label):
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message="Message label must not contain parentheses or semicolons.",
                    )
                )
            if has_signature_detail(label):
                issues.append(
                    MermaidIssue(
                        path=path,
                        line=index,
                        message="Message label must not contain argument or return details.",
                    )
                )
            sql_match = SQL_MESSAGE_PATTERN.match(line)
            if sql_match:
                filename = sql_match.group("filename")
                if filename in sql_filenames:
                    issues.append(
                        MermaidIssue(
                            path=path,
                            line=index,
                            message=f"SQL file '{filename}' is rendered more than once.",
                        )
                    )
                sql_filenames.add(filename)
            continue

        issues.append(
            MermaidIssue(
                path=path,
                line=index,
                message=f"Unsupported Mermaid sequence line: {stripped}",
            )
        )

    return issues


def sequence_markdown_paths(docs_root: Path) -> list[Path]:
    return sorted(docs_root.glob("*/*/sequence_gen.md"))


def validate_file(path: Path) -> list[MermaidIssue]:
    source = path.read_text(encoding="utf-8")
    blocks = mermaid_blocks(source)
    if not blocks:
        return [
            MermaidIssue(
                path=path,
                line=1,
                message="Mermaid block is not found.",
            )
        ]
    issues: list[MermaidIssue] = []
    for start_line, lines in blocks:
        issues.extend(validate_sequence_block(path, start_line, lines))
    return issues


def validate_paths(paths: Iterable[Path]) -> list[MermaidIssue]:
    issues: list[MermaidIssue] = []
    for path in paths:
        issues.extend(validate_file(path))
    return issues


def render_issues(issues: Iterable[MermaidIssue]) -> str:
    return "\n".join(
        f"{issue.path}:{issue.line}: {issue.message}" for issue in issues
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check generated API Mermaid sequences.")
    parser.add_argument("--docs-root", type=Path, default=Path("docs/spec/40.apis"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    issues = validate_paths(sequence_markdown_paths(args.docs_root))
    if issues:
        print(render_issues(issues))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
