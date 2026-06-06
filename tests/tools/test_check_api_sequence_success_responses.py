from __future__ import annotations

from pathlib import Path

from tools.check_api_sequence_success_responses import check_api_sequence_success_responses


def write_sequence(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_check_api_sequence_success_responses_reports_missing_2xx(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs/spec/40.apis"
    write_sequence(
        docs_root,
        "projects/create_project/sequence_gen.md",
        """
```mermaid
sequenceDiagram
  API-->>User: HTTP 400 Bad Request
```
""",
    )

    issues = check_api_sequence_success_responses(docs_root)

    assert [(issue.path.name, issue.message) for issue in issues] == [
        ("sequence_gen.md", "sequence must include a successful 2xx response")
    ]


def test_check_api_sequence_success_responses_accepts_2xx(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs/spec/40.apis"
    write_sequence(
        docs_root,
        "projects/create_project/sequence_gen.md",
        """
```mermaid
sequenceDiagram
  API-->>User: HTTP 201 Created
```
""",
    )

    assert check_api_sequence_success_responses(docs_root) == []


def test_check_api_sequence_success_responses_reports_early_2xx(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs/spec/40.apis"
    write_sequence(
        docs_root,
        "projects/create_project/sequence_gen.md",
        """
```mermaid
sequenceDiagram
  API-->>User: HTTP 201 Created
  API->>DB: Project を追加する。<br/>SQL 001_insert_projects.sql<br/>テーブル projects
```
""",
    )

    issues = check_api_sequence_success_responses(docs_root)

    assert [(issue.path.name, issue.message) for issue in issues] == [
        (
            "sequence_gen.md",
            "successful 2xx response must be rendered after normal processing",
        )
    ]
