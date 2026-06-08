from __future__ import annotations

from pathlib import Path

from tools.check_api_function_exception_policy import check_api_function_exception_policy


def write_api_functions(tmp_path: Path, source: str) -> Path:
    api_dir = tmp_path / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    path = api_dir / "functions.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_reports_wrong_exception_policy(tmp_path: Path) -> None:
    path = write_api_functions(
        tmp_path,
        """
async def get_project(session=None):
    await queries.select_projects(session)
    return object()

async def get_api(session=None):
    return raise_missing_runtime_dependency("get_project")

async def save_project(session=None):
    raise_missing_runtime_dependency("save_project")

async def validate_project():
    raise HTTPException(status_code=400, detail="invalid")

async def validate_runtime_dependency():
    raise ApiFunctionError(
        500,
        "get_project requires runtime dependencies.",
        summary="runtime dependency",
    )
""",
    )

    issues = check_api_function_exception_policy(tmp_path)

    assert [(issue.path, issue.function_name, issue.message) for issue in issues] == [
        (
            path,
            "get_project",
            "runtime dependency function must call raise_missing_runtime_dependency",
        ),
        (
            path,
            "get_api",
            "raise_missing_runtime_dependency argument must match the function name",
        ),
        (
            path,
            "save_project",
            "raise_missing_runtime_dependency must be returned directly",
        ),
        (
            path,
            "validate_project",
            "API functions must not raise HTTPException directly",
        ),
        (
            path,
            "validate_runtime_dependency",
            "runtime dependency errors must use raise_missing_runtime_dependency",
        ),
    ]


def test_accepts_business_errors_and_runtime_dependency_guards(tmp_path: Path) -> None:
    write_api_functions(
        tmp_path,
        """
async def validate_project():
    raise ApiFunctionError(400, "invalid", summary="入力が不正な場合。")

async def get_project(session=None):
    if session is not None:
        await queries.select_projects(session)
        return object()
    return raise_missing_runtime_dependency("get_project")

async def get_caller_identity(principal_id=None):
    return build_caller_identity(principal_id=principal_id)
""",
    )

    assert check_api_function_exception_policy(tmp_path) == []
