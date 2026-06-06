from __future__ import annotations

from pathlib import Path

from tools.check_api_function_resource_usage import (
    check_api_function_resource_usage,
)


def write_api_functions(tmp_path: Path, source: str) -> Path:
    api_dir = tmp_path / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    path = api_dir / "functions.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_reports_non_validation_function_without_resource_usage(tmp_path: Path) -> None:
    path = write_api_functions(
        tmp_path,
        '''
async def append_project_event(project):
    """Project event を追記する。"""
    return project
''',
    )

    issues = check_api_function_resource_usage(tmp_path)

    assert [(issue.path, issue.function_name) for issue in issues] == [
        (path, "append_project_event")
    ]


def test_allows_validation_and_explicit_resource_free_functions(tmp_path: Path) -> None:
    write_api_functions(
        tmp_path,
        '''
async def is_project_active(project):
    """Project が active か判定する。"""
    return True

async def calculate_project_quota(project):
    """@resource-free
    Project quota を算出する。
    """
    return 10
''',
    )

    assert check_api_function_resource_usage(tmp_path) == []


def test_accepts_queries_and_integration_resource_usage(tmp_path: Path) -> None:
    write_api_functions(
        tmp_path,
        '''
async def save_project(project, session):
    """Project を保存する。"""
    await queries.insert_projects(session, project)
    return project

async def create_api_key(project, api_gateway_control):
    """API key を作成する。"""
    return await api_gateway_control.create_api_key(project)
''',
    )

    assert check_api_function_resource_usage(tmp_path) == []
