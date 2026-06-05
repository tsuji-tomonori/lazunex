from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_api_managed_literals import (
    ManagedLiteralIssue,
    build_arg_parser,
    check_api_managed_literal_roots,
    check_api_managed_literals,
    main,
    render_issues,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_check_api_managed_literals_reports_disallowed_literals(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_file(
        api_root / "projects" / "get_project" / "functions.py",
        '''
async def get_project_detail() -> object:
    """CALLBACK in docstring is allowed."""
    return "CALLBACK", "LOGOUT", "hub-admin"
''',
    )
    write_file(
        api_root / "common.py",
        """
from enum import StrEnum


class IdentityGroup(StrEnum):
    HUB_ADMIN = "hub-admin"
""",
    )
    write_file(
        api_root / "projects" / "common.py",
        """
CALLBACK = "CALLBACK"
LOGOUT = "LOGOUT"
""",
    )

    issues = check_api_managed_literals(api_root)

    assert [(issue.literal, issue.line) for issue in issues] == [
        ("CALLBACK", 4),
        ("LOGOUT", 4),
        ("hub-admin", 4),
    ]


def test_check_api_managed_literals_accepts_repository_usage() -> None:
    assert check_api_managed_literal_roots([Path("src/app/apis"), Path("tests/app/apis")]) == []


def test_render_issues_and_main(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    issue = ManagedLiteralIssue(
        path=Path("src/app/apis/projects/get_project/functions.py"),
        line=10,
        literal="CALLBACK",
        message="managed literal must be referenced through a shared constant or enum",
    )
    assert "CALLBACK" in render_issues([issue])

    api_root = tmp_path / "apis"
    write_file(
        api_root / "projects" / "get_project" / "functions.py",
        'VALUE = "CALLBACK"\n',
    )

    assert main(["--api-root", str(api_root)]) == 1
    assert "CALLBACK" in capsys.readouterr().out


def test_build_arg_parser_defaults() -> None:
    args = build_arg_parser().parse_args([])

    assert args.api_roots is None
