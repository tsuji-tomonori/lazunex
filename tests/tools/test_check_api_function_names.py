from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.check_api_function_names import (
    FunctionNameIssue,
    build_arg_parser,
    check_api_function_file,
    check_api_function_names,
    load_rule_names,
    load_rules,
    main,
    render_issues,
)


def write_rules(rule_dir: Path) -> None:
    rule_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "sequence_function_actions.json": {
            "entries": [
                {"name": "get", "description": "取得する。"},
                {"name": "create", "description": "作成する。"},
            ]
        },
        "sequence_function_targets.json": {
            "entries": [
                {"name": "project", "description": "Project を対象にします。"},
                {"name": "api_key", "description": "API key を対象にします。"},
            ]
        },
        "sequence_function_predicates.json": {
            "entries": [
                {"name": "is", "description": "状態を判定します。"},
                {"name": "has", "description": "有無を判定します。"},
            ]
        },
        "sequence_function_conditions.json": {
            "entries": [
                {"name": "project_owner_permission", "description": "owner 権限を判定します。"},
                {"name": "published_api", "description": "公開済み API を判定します。"},
            ]
        },
    }
    for filename, payload in payloads.items():
        (rule_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )


def write_api_function_file(root: Path, content: str) -> Path:
    path = root / "projects" / "get_project" / "functions.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_load_rule_names_requires_descriptions(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text('{"entries": [{"name": "get"}]}', encoding="utf-8")

    with pytest.raises(ValueError, match="description"):
        load_rule_names(path)


def test_check_api_function_file_accepts_action_and_condition_names(tmp_path: Path) -> None:
    rule_dir = tmp_path / "rules"
    write_rules(rule_dir)
    path = write_api_function_file(
        tmp_path / "apis",
        '''
async def get_project() -> object:
    """Project を取得する。"""
    return object()

async def create_api_key() -> object:
    """API key を作成する。"""
    return object()

async def has_project_owner_permission() -> bool:
    """Project owner 権限を判定する。"""
    return True

async def is_published_api() -> bool:
    """API が公開済みかを判定する。"""
    return True
''',
    )

    assert check_api_function_file(path, load_rules(rule_dir)) == []


def test_check_api_function_file_reports_unknown_words_and_missing_docstring(
    tmp_path: Path,
) -> None:
    rule_dir = tmp_path / "rules"
    write_rules(rule_dir)
    path = write_api_function_file(
        tmp_path / "apis",
        """
async def fetch_project() -> object:
    return object()

async def get_user() -> object:
    return object()

async def is_enabled_project() -> bool:
    return True
""",
    )

    issues = check_api_function_file(path, load_rules(rule_dir))

    assert [issue.target for issue in issues] == [
        "fetch_project",
        "fetch_project",
        "get_user",
        "get_user",
        "is_enabled_project",
        "is_enabled_project",
    ]
    assert "action or predicate 'fetch' is not defined" in issues[0].message
    assert "requires a docstring" in issues[1].message
    assert "target 'user' is not defined" in issues[2].message
    assert "condition 'enabled_project' is not defined" in issues[4].message


def test_check_api_function_names_accepts_repository_definitions() -> None:
    assert (
        check_api_function_names(
            Path("src/app/apis"),
            Path("docs/rule/docs"),
        )
        == []
    )


def test_render_issues_and_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    issue = FunctionNameIssue(
        path=Path("src/app/apis/projects/get_project/functions.py"),
        line=10,
        target="fetch_project",
        message="action or predicate 'fetch' is not defined",
    )
    assert "fetch_project" in render_issues([issue])

    rule_dir = tmp_path / "rules"
    write_rules(rule_dir)
    api_root = tmp_path / "apis"
    write_api_function_file(
        api_root,
        """
async def fetch_project() -> object:
    return object()
""",
    )

    assert main(["--api-root", str(api_root), "--rule-dir", str(rule_dir)]) == 1
    assert "fetch_project" in capsys.readouterr().out


def test_build_arg_parser_defaults() -> None:
    args = build_arg_parser().parse_args([])

    assert args.api_root == Path("src/app/apis")
    assert args.rule_dir == Path("docs/rule/docs")
