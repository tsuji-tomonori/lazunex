from pathlib import Path

from tools.generate_api_unit_test_factors import (
    api_unit_test_factors_from_dir,
    generate_unit_test_factors,
    product_cases,
    render_unit_test_markdown,
)


def write_router(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
from fastapi import APIRouter, status

router = APIRouter()

@router.post("/projects", operation_id="createProject")
async def create_project():
    try:
        # Project 作成権限がない場合。
        if not await api_functions.has_project_creation_permission(caller):
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot create project")
        if idempotency_record.operation_id is not None:
            return api_error_response(status.HTTP_409_CONFLICT, "idempotency key is already used")
        return await api_functions.build_create_project_response()
    # DB commit が一時的に失敗した場合。
    except SQLAlchemyError as error:
        return api_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "database commit failed")
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return error_response_for_router_error(error, trace_id=request_context.correlation_id)
""",
        encoding="utf-8",
    )


def write_functions(path: Path) -> None:
    path.write_text(
        '''
async def has_project_creation_permission(caller):
    """呼び出し元が Project を作成できるかを判定する。"""
    return True
''',
        encoding="utf-8",
    )


def test_api_unit_test_factors_from_router_ast(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
    api_dir = api_root / "projects/create_project"
    write_router(api_dir / "router.py")
    write_functions(api_dir / "functions.py")

    doc = api_unit_test_factors_from_dir(api_dir, api_root)

    assert doc.operation_id == "createProject"
    assert doc.method == "POST"
    assert doc.path == "/projects"
    assert [factor.kind for factor in doc.factors] == [
        "条件分岐",
        "条件分岐",
        "例外処理",
        "例外処理",
    ]
    assert doc.factors[0].source == "not await api_functions.has_project_creation_permission(caller)"
    assert doc.factors[0].title.endswith("Project 作成権限がない場合。")
    assert doc.factors[0].elements[0].expected == (
        "HTTP 403 error response: caller cannot create project"
    )
    assert doc.factors[2].source == "SQLAlchemyError"
    assert doc.factors[2].title.endswith("DB commit が一時的に失敗した場合。")
    assert doc.factors[3].elements[1].expected == "router error response"
    assert len(product_cases(doc.factors)) == 5
    assert product_cases(doc.factors)[0][0] == doc.factors[0].elements[0]
    assert product_cases(doc.factors)[0][1:] == (None, None, None)


def test_condition_description_falls_back_to_api_function_docstring(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
    api_dir = api_root / "projects/create_project"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "router.py").write_text(
        """
from fastapi import APIRouter

router = APIRouter()

@router.post("/projects", operation_id="createProject")
async def create_project():
    if not await api_functions.has_project_creation_permission(caller):
        return api_error_response(403, "caller cannot create project")
""",
        encoding="utf-8",
    )
    write_functions(api_dir / "functions.py")

    doc = api_unit_test_factors_from_dir(api_dir, api_root)

    assert doc.factors[0].title.endswith("呼び出し元が Project を作成できない場合。")


def test_render_unit_test_markdown_uses_three_sections(tmp_path: Path) -> None:
    api_root = tmp_path / "src/app/apis"
    docs_root = tmp_path / "docs/spec/40.apis"
    api_dir = api_root / "projects/create_project"
    write_router(api_dir / "router.py")
    write_functions(api_dir / "functions.py")

    rendered = generate_unit_test_factors(api_root, docs_root)
    output_path = docs_root / "projects/create_project/unit-test_gen.md"
    content = rendered[output_path]

    assert render_unit_test_markdown(api_unit_test_factors_from_dir(api_dir, api_root)) == content
    assert "## 1. 要因ごとの要素" in content
    assert "## 2. 直積したテストケース一覧" in content
    assert "## 3. テスト詳細" in content
    assert "| `TC005` |" in content
    assert "| `TC006` |" not in content
    assert "| `TC001` | `成立` | - | - | - |" in content
    assert "`F01` 条件分岐 L" in content
