from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_api_descriptions import (
    DescriptionIssue,
    api_description_files,
    build_arg_parser,
    check_api_descriptions,
    check_router_file,
    check_schema_file,
    enum_member_comment,
    enum_member_line_numbers,
    enum_members,
    field_name,
    has_japanese_text,
    is_field_call,
    is_placeholder_description,
    is_router_decorator,
    is_str_enum_class,
    literal_string,
    main,
    render_issues,
)


def write_api_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_has_japanese_text_and_literal_string() -> None:
    assert has_japanese_text("API一覧を取得する")
    assert not has_japanese_text("List APIs")
    assert not has_japanese_text(None)
    assert is_placeholder_description("items の値を指定します。")
    assert is_placeholder_description("SampleResponse のOpenAPIスキーマを説明します。")
    assert not is_placeholder_description("API一覧に含める項目配列です。")
    assert not is_placeholder_description(None)
    assert literal_string(__import__("ast").parse("'説明'").body[0].value) == "説明"
    assert literal_string(__import__("ast").parse("name").body[0].value) is None


def test_is_router_decorator_rejects_non_route_shapes() -> None:
    ast_module = __import__("ast")

    assert not is_router_decorator(ast_module.parse("name").body[0].value)
    assert not is_router_decorator(ast_module.parse("decorator('/x')").body[0].value)
    assert not is_router_decorator(ast_module.parse("router.websocket('/x')").body[0].value)
    assert not is_router_decorator(ast_module.parse("other.get('/x')").body[0].value)
    assert is_router_decorator(ast_module.parse("router.get('/x')").body[0].value)


def test_ast_helpers_accept_supported_shapes() -> None:
    ast_module = __import__("ast")
    field_assign = ast_module.parse("value: str = pydantic.Field()").body[0]
    attribute_assign = ast_module.parse("model.value: str = Field()").body[0]
    enum_class = ast_module.parse(
        """
class Sample(enum.StrEnum):
    # サンプル値です。
    VALUE = 'VALUE'
    dynamic = value
"""
    ).body[0]
    source_lines = ["class Sample(enum.StrEnum):", "    # サンプル値です。", "    VALUE = 'VALUE'"]

    assert is_field_call(field_assign.value)
    assert field_name(attribute_assign) is None
    assert is_str_enum_class(enum_class)
    assert enum_members(enum_class) == {"VALUE": "VALUE"}
    assert enum_member_line_numbers(enum_class) == {"VALUE": 4}
    assert enum_member_comment(source_lines, 3) == "サンプル値です。"
    assert (
        enum_member_comment(["VALUE = 'VALUE'  # インライン説明です。"], 1)
        == "インライン説明です。"
    )


def test_enum_member_comment_rejects_missing_comment() -> None:
    ast_module = __import__("ast")
    enum_class = ast_module.parse(
        """
class Sample(StrEnum):
    VALUE = 'VALUE'
"""
    ).body[0]

    assert enum_member_line_numbers(enum_class) == {"VALUE": 3}
    assert enum_member_comment(["class Sample(StrEnum):", "    VALUE = 'VALUE'"], 2) is None
    assert enum_member_comment([], 0) is None


def test_check_router_file_accepts_japanese_summary_and_description(tmp_path: Path) -> None:
    router = write_api_file(
        tmp_path,
        "apis/list_apis/router.py",
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/apis', summary='API一覧を取得する', description='公開済みAPIを一覧取得します。')
async def list_apis():
    pass
""",
    )

    assert check_router_file(router) == []


def test_check_router_file_reports_missing_and_non_japanese_values(tmp_path: Path) -> None:
    router = write_api_file(
        tmp_path,
        "apis/list_apis/router.py",
        """
from fastapi import APIRouter
router = APIRouter()
DESC = '説明'

@router.post('/apis', summary='Publish API', description=DESC)
def publish_api():
    pass
""",
    )

    issues = check_router_file(router)

    assert [issue.target for issue in issues] == [
        "publish_api.summary",
        "publish_api.description",
    ]
    assert "must contain Japanese" in issues[0].message
    assert "requires Japanese" in issues[1].message


def test_check_router_file_ignores_non_router_decorators(tmp_path: Path) -> None:
    router = write_api_file(
        tmp_path,
        "apis/list_apis/router.py",
        """
from fastapi import APIRouter
router = APIRouter()

@other.get('/apis')
async def ignored():
    pass
""",
    )

    assert check_router_file(router) == []


def test_check_schema_file_accepts_japanese_docstrings(tmp_path: Path) -> None:
    schema = write_api_file(
        tmp_path,
        "apis/list_apis/schemas.py",
        '''
from pydantic import BaseModel, Field

class ListApisResponse(BaseModel):
    """API一覧レスポンスを説明します。"""
    items: list[str] = Field(description="API一覧に含める項目配列です。")
''',
    )

    assert check_schema_file(schema) == []


def test_check_schema_file_reports_missing_and_non_japanese_docstrings(tmp_path: Path) -> None:
    schema = write_api_file(
        tmp_path,
        "apis/list_apis/schemas.py",
        '''
from pydantic import BaseModel, Field

class MissingDescription(BaseModel):
    value: str = Field(description="検証対象の値です。")

class EnglishDescription(BaseModel):
    """English description."""
    value: str = Field(description="検証対象の値です。")
''',
    )

    issues = check_schema_file(schema)

    assert [issue.target for issue in issues] == ["MissingDescription", "EnglishDescription"]
    assert "requires a Japanese docstring" in issues[0].message
    assert "must contain Japanese" in issues[1].message


def test_check_schema_file_reports_placeholder_descriptions(tmp_path: Path) -> None:
    schema = write_api_file(
        tmp_path,
        "apis/list_apis/schemas.py",
        '''
from pydantic import BaseModel, Field

class PlaceholderDocstring(BaseModel):
    """PlaceholderDocstring のOpenAPIスキーマを説明します。"""
    concrete_field: str = Field(description="検証対象の値です。")

class PlaceholderField(BaseModel):
    """具体的な用途を説明する検証モデルです。"""
    value: str = Field(description="value の値を指定します。")
''',
    )

    issues = check_schema_file(schema)

    assert [issue.target for issue in issues] == [
        "PlaceholderDocstring",
        "PlaceholderField.value",
    ]
    assert "model purpose concretely" in issues[0].message
    assert "field purpose concretely" in issues[1].message


def test_check_schema_file_reports_field_description_issues(
    tmp_path: Path,
) -> None:
    schema = write_api_file(
        tmp_path,
        "apis/list_apis/schemas.py",
        '''
from pydantic import BaseModel, Field

class FieldIssues(BaseModel):
    """フィールド検証用モデルを説明します。"""
    missing_field: str
    missing_description: str = Field()
    english_description: str = Field(description="English description.")
''',
    )

    issues = check_schema_file(schema)

    assert [issue.target for issue in issues] == [
        "FieldIssues.missing_field",
        "FieldIssues.missing_description",
        "FieldIssues.english_description",
    ]
    assert "requires Field" in issues[0].message
    assert "requires a Japanese Field description" in issues[1].message
    assert "description must contain Japanese" in issues[2].message


def test_check_schema_file_accepts_enum_value_comments(tmp_path: Path) -> None:
    schema = write_api_file(
        tmp_path,
        "apis/common.py",
        '''
from enum import StrEnum

class ApiVisibility(StrEnum):
    """APIカタログの公開範囲を表す列挙値です。"""
    # 社内利用者に公開されるAPIです。
    INTERNAL = "INTERNAL"
    # 限定された利用者だけに公開されるAPIです。
    RESTRICTED = "RESTRICTED"
''',
    )

    assert check_schema_file(schema) == []


def test_check_schema_file_reports_enum_value_comment_issues(tmp_path: Path) -> None:
    schema = write_api_file(
        tmp_path,
        "apis/common.py",
        '''
from enum import StrEnum

class ApiVisibility(StrEnum):
    """APIカタログの公開範囲を表す列挙値です。"""
    # Internal users only.
    INTERNAL = "INTERNAL"
    # RESTRICTED の値を指定します。
    RESTRICTED = "RESTRICTED"
    LEGACY = "LEGACY"
''',
    )

    issues = check_schema_file(schema)

    assert [issue.target for issue in issues] == [
        "ApiVisibility.INTERNAL",
        "ApiVisibility.RESTRICTED",
        "ApiVisibility.LEGACY",
    ]
    assert "must contain Japanese" in issues[0].message
    assert "value meaning concretely" in issues[1].message
    assert "requires a Japanese comment" in issues[2].message


def test_check_api_descriptions_collects_router_and_schema_files(tmp_path: Path) -> None:
    write_api_file(
        tmp_path,
        "domain/sample/router.py",
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/sample', summary='サンプル取得', description='サンプルを取得します。')
async def sample():
    pass
""",
    )
    write_api_file(
        tmp_path,
        "domain/sample/schemas.py",
        '''
from pydantic import BaseModel, Field

class SampleResponse(BaseModel):
    """サンプルレスポンスを説明します。"""
    value: str = Field(description="サンプルとして返却する文字列です。")
''',
    )
    write_api_file(tmp_path, "domain/sample/samples.py", "SAMPLE = {}\n")

    assert [path.name for path in api_description_files(tmp_path)] == ["router.py", "schemas.py"]
    assert check_api_descriptions(tmp_path) == []


def test_render_issues_and_arg_parser_defaults() -> None:
    assert "All router" in render_issues([])

    rendered = render_issues(
        [
            DescriptionIssue(
                path=Path("src/app/apis/sample/router.py"),
                line=3,
                target="sample.summary",
                message="missing",
            )
        ]
    )
    args = build_arg_parser().parse_args([])

    assert "sample.summary" in rendered
    assert args.api_dir.as_posix() == "src/app/apis"
    assert args.no_fail_on_issue is False


def test_main_exits_nonzero_when_issue_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_api_file(
        tmp_path,
        "domain/sample/schemas.py",
        "from pydantic import BaseModel\nclass SampleResponse(BaseModel):\n    value: str\n",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["check_api_descriptions", "--api-dir", str(tmp_path)],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "SampleResponse" in capsys.readouterr().out


def test_main_can_ignore_issue_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_api_file(
        tmp_path,
        "domain/sample/router.py",
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/sample')
async def sample():
    pass
""",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_api_descriptions",
            "--api-dir",
            str(tmp_path),
            "--no-fail-on-issue",
        ],
    )

    main()

    assert "sample.summary" in capsys.readouterr().out
