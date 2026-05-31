from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture

from tools.check_api_mermaid_sequences import (
    main,
    mermaid_blocks,
    validate_file,
)


def write_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_mermaid_blocks_extracts_body_and_start_line() -> None:
    blocks = mermaid_blocks(
        """
# sequence

```mermaid
sequenceDiagram
  autonumber
```
"""
    )

    assert blocks == [(5, ["sequenceDiagram", "  autonumber"])]


def test_validate_file_accepts_generated_sequence_shape(tmp_path: Path) -> None:
    path = write_file(
        tmp_path,
        "docs/spec/40.apis/projects/list_projects/sequence_gen.md",
        """
```mermaid
sequenceDiagram
  autonumber
  participant API as API: listProjects
  participant DB as DB
  API->>API: Project 一覧取得条件を検証する。 引数 query ListProjectsQuery
  alt 呼び出し元が Project 一覧を参照できるかを判定する。
    API->>API: 呼び出し元が Project 一覧を参照できるかを判定する。 戻り値 bool
  end
  API->>DB: DBを参照する SQL 001_select_projects.sql テーブル projects, project_members
```
""",
    )

    assert validate_file(path) == []


def test_validate_file_rejects_message_colons_and_split_sql(tmp_path: Path) -> None:
    path = write_file(
        tmp_path,
        "sequence_gen.md",
        """
```mermaid
sequenceDiagram
  autonumber
  participant API as API: listProjects
  participant DB as DB
  API->>API: Project 一覧取得条件を検証する。(引数 query: ListProjectsQuery)
  API->>DB: DBを参照する SQL 001_select_projects.sql テーブル projects
  API->>DB: DBを参照する SQL 001_select_projects.sql テーブル project_members
```
""",
    )

    issues = validate_file(path)

    assert [issue.message for issue in issues] == [
        "Message label must not contain ':' or fullwidth colon.",
        "Message label must not contain parentheses or semicolons.",
        "SQL file '001_select_projects.sql' is rendered more than once.",
    ]


def test_main_reports_issues(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    docs_root = tmp_path / "docs/spec/40.apis"
    write_file(
        docs_root,
        "projects/list_projects/sequence_gen.md",
        """
```mermaid
sequenceDiagram
  API->>Missing: broken
```
""",
    )

    assert main(["--docs-root", str(docs_root)]) == 1
    output = capsys.readouterr().out
    assert "Unknown message source participant 'API'." in output
    assert "Unknown message target participant 'Missing'." in output
