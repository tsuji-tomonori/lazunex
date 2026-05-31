import ast
from pathlib import Path
from typing import Any, ClassVar, cast

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from tools.generate_openapi_if_specs import (
    OperationSamples,
    build_arg_parser,
    enum_comment_descriptions,
    generate_from_openapi,
    implementation_operation_paths,
    implementation_operation_samples,
    iter_operations,
    keyword_value,
    literal_string,
    load_fastapi_openapi,
    load_operation_sample,
    main,
    module_sample,
    object_field_rows,
    operation_output_path,
    parameter_default,
    parameter_rows,
    render_curl_sample,
    render_field_table,
    render_json,
    render_operation_markdown,
    render_response_details,
    render_response_summary,
    render_samples_section,
    request_body_rows,
    response_media,
    response_summary_rows,
    router_operation_id,
    sample_module_name,
    schema_components,
    schema_constraints,
    schema_type,
    snake_case,
)

OPENAPI: dict[str, Any] = {
    "openapi": "3.1.0",
    "components": {
        "schemas": {
            "DeleteUserRequest": {
                "type": "object",
                "required": ["reason"],
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "削除理由。",
                        "minLength": 1,
                    },
                    "notify": {
                        "type": "boolean",
                        "description": "通知するかどうか。",
                    },
                },
            },
            "UserResponse": {
                "type": "object",
                "required": ["userId", "email", "status", "groups", "profile"],
                "properties": {
                    "userId": {"type": "string", "description": "対象ユーザーID。"},
                    "email": {"type": "string", "description": "メールアドレス。"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "deleted"],
                        "title": "UserStatus",
                        "description": "状態。",
                    },
                    "groups": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "所属グループ。",
                    },
                    "details": {
                        "anyOf": [{"type": "object"}, {"type": "null"}],
                        "description": "補足。",
                    },
                    "profile": {
                        "$ref": "#/components/schemas/UserProfileResponse",
                    },
                    "addresses": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/UserAddressResponse"},
                        "description": "住所一覧。",
                    },
                },
            },
            "UserProfileResponse": {
                "type": "object",
                "required": ["displayName"],
                "description": "ユーザー表示情報です。",
                "properties": {
                    "displayName": {
                        "type": "string",
                        "description": "画面に表示するユーザー名。",
                    },
                    "department": {
                        "type": "string",
                        "description": "所属部署。",
                    },
                },
            },
            "UserAddressResponse": {
                "type": "object",
                "required": ["postalCode"],
                "description": "ユーザー住所情報です。",
                "properties": {
                    "postalCode": {
                        "type": "string",
                        "description": "郵便番号。",
                    },
                },
            },
            "ErrorResponse": {
                "type": "object",
                "required": ["error"],
                "properties": {
                    "error": {"type": "string", "description": "エラー内容。"},
                    "details": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "詳細。",
                    },
                },
            },
        }
    },
    "paths": {
        "/admin/users/{userId}": {
            "delete": {
                "tags": ["admin_users"],
                "operationId": "deleteAdminUser",
                "summary": "ユーザーを削除する",
                "description": "指定した管理対象ユーザーを削除します。",
                "parameters": [
                    {
                        "name": "Authorization",
                        "in": "header",
                        "required": True,
                        "description": "Bearer token。",
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "Idempotency-Key",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "description": "対象ユーザーID。",
                        "schema": {
                            "type": "string",
                            "minLength": 1,
                            "default": "user-1",
                        },
                    },
                    {
                        "name": "force",
                        "in": "query",
                        "required": False,
                        "description": "強制削除するか。",
                        "schema": {"type": "boolean"},
                    },
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/DeleteUserRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "成功。",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserResponse"}
                            }
                        },
                    },
                    "401": {
                        "description": "認証が必要です。",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                    "204": {"description": "bodyなし。"},
                },
            }
        },
        "/internal": {"parameters": []},
    },
}


def components() -> dict[str, Any]:
    return cast(dict[str, Any], OPENAPI["components"]["schemas"])


def delete_operation() -> dict[str, Any]:
    return cast(dict[str, Any], OPENAPI["paths"]["/admin/users/{userId}"]["delete"])


def test_schema_type_and_constraints() -> None:
    schemas = components()

    assert snake_case("deleteAdminUser") == "delete_admin_user"
    assert schema_type({"$ref": "#/components/schemas/UserResponse"}, schemas) == "UserResponse"
    assert schema_type({"type": "array", "items": {"type": "string"}}, schemas) == "array<string>"
    assert schema_type({"type": "array", "items": True}, schemas) == "array<object>"
    assert (
        schema_type({"anyOf": [{"type": "string"}, {"type": "null"}]}, schemas) == "string | null"
    )
    assert (
        schema_type({"oneOf": [{"type": "integer"}, {"type": "null"}]}, schemas) == "integer | null"
    )
    assert schema_type(
        {"type": "object", "additionalProperties": {"type": "integer"}}, schemas
    ) == ("object<string, integer>")
    assert schema_type({"type": "object", "additionalProperties": True}, schemas) == "object"
    assert (
        schema_type(
            {"type": "string", "enum": ["active", "deleted"], "title": "UserStatus"}, schemas
        )
        == "string(active, deleted)"
    )
    assert schema_constraints(
        {"type": "string", "minLength": 1, "enum": ["active", "deleted"], "title": "UserStatus"},
        schemas,
    ) == (
        "minLength=1, active=列挙値として指定可能な値です。"
        "<br>deleted=列挙値として指定可能な値です。"
    )
    assert (
        schema_constraints(
            {"type": "string", "enum": ["INTERNAL"], "title": "ApiVisibility"},
            schemas,
        )
        == "INTERNAL=社内利用者に公開されるAPIです。"
    )
    assert schema_components({"components": {"schemas": []}}) == {}
    assert schema_components({}) == {}


def test_enum_comment_descriptions_reads_enum_member_comments(tmp_path: Path) -> None:
    common = tmp_path / "common.py"
    common.write_text(
        '''
from enum import StrEnum

class SampleStatus(StrEnum):
    """サンプル状態です。"""
    # 処理を継続できる状態です。
    ACTIVE = "active"
    # 処理を終了した状態です。
    CLOSED = "closed"
''',
        encoding="utf-8",
    )

    descriptions = enum_comment_descriptions(common)

    assert descriptions == {
        "SampleStatus": {
            "active": "処理を継続できる状態です。",
            "closed": "処理を終了した状態です。",
        }
    }
    assert enum_comment_descriptions(tmp_path / "missing.py") == {}


def test_parameter_and_request_body_rows() -> None:
    operation = delete_operation()
    schemas = components()

    headers = parameter_rows(operation, "header", schemas)
    paths = parameter_rows(operation, "path", schemas)
    queries = parameter_rows(operation, "query", schemas)
    data = request_body_rows(operation, schemas)

    assert [(row.name, row.type_name, row.required) for row in headers] == [
        ("Authorization", "string", True),
        ("Idempotency-Key", "string", True),
    ]
    assert headers[1].description.startswith("同じ更新系リクエストの重複処理を防ぐため")
    assert paths[0].constraints == "minLength=1"
    assert [(row.name, row.type_name, row.required) for row in queries] == [
        ("force", "boolean", False)
    ]
    assert [(row.name, row.type_name, row.required) for row in data] == [
        ("reason", "string", True),
        ("notify", "boolean", False),
    ]


def test_response_summary_and_render_markdown() -> None:
    operation = delete_operation()
    schemas = components()

    summary_rows = response_summary_rows(operation, schemas)
    rendered = render_operation_markdown(
        "/admin/users/{userId}",
        "delete",
        operation,
        schemas,
        OperationSamples(
            request={"reason": "退職に伴う削除", "notify": True},
            response={"userId": "user-1", "email": "user@example.com"},
        ),
    )

    assert summary_rows[0] == ["200", "成功。", "application/json", "10 field(s)"]
    assert summary_rows[2] == ["204", "bodyなし。", "-", "-"]
    assert "# DELETE /admin/users/{userId}" in rendered
    assert "## Headers" in rendered
    assert "## Path Parameters" in rendered
    assert "## Query Parameters" in rendered
    assert "## Data" in rendered
    assert "## Responses" in rendered
    assert "## Samples" in rendered
    assert "curl -X DELETE 'https://api.example.com/admin/users/user-1?force=<force>'" in rendered
    assert "-H 'Authorization: <Authorization>'" in rendered
    assert '"reason": "退職に伴う削除"' in rendered
    assert '"email": "user@example.com"' in rendered
    assert (
        "| `status` | `string(active, deleted)` | yes | 状態。 | "
        "active=列挙値として指定可能な値です。"
        "<br>deleted=列挙値として指定可能な値です。 |" in rendered
    )
    assert "| `profile.displayName` | `string` | yes | 画面に表示するユーザー名。 | - |" in rendered
    assert "| `addresses[].postalCode` | `string` | yes | 郵便番号。 | - |" in rendered
    assert "##### `401` 認証が必要です。" in rendered


def test_empty_and_invalid_sections_render_none() -> None:
    schemas = components()

    assert parameter_rows({"parameters": ["invalid"]}, "header", schemas) == []
    assert request_body_rows({}, schemas) == []
    assert request_body_rows({"requestBody": []}, schemas) == []
    assert request_body_rows({"requestBody": {"content": []}}, schemas) == []
    assert request_body_rows({"requestBody": {"content": {"text/plain": []}}}, schemas) == []
    assert object_field_rows({"type": "object", "properties": []}, schemas) == []
    assert object_field_rows({"type": "object", "properties": {"x": []}}, schemas) == []
    assert response_media({"content": []}) == ("-", {})
    assert response_media({"content": {"text/plain": []}}) == ("text/plain", {})
    assert response_media({"content": {"text/plain": {"schema": []}}}) == ("text/plain", {})
    assert response_summary_rows({"responses": []}, schemas) == []
    assert response_summary_rows({"responses": {"default": []}}, schemas) == []
    assert render_field_table([]) == ["_なし_"]
    assert render_response_summary([]) == ["_なし_"]
    assert render_response_details({"responses": []}, schemas) == []
    assert render_response_details({"responses": {"default": []}}, schemas) == []
    assert iter_operations({"paths": []}) == []
    assert iter_operations({"paths": {"/bad": []}}) == []


def test_render_operation_markdown_handles_missing_description() -> None:
    rendered = render_operation_markdown("/ping", "get", {"responses": {}}, {})

    assert "Summary: -" in rendered
    assert "## Responses" in rendered
    assert "### Out\n\n_なし_" in rendered


def test_sample_renderers_format_curl_and_json() -> None:
    operation = delete_operation()

    assert parameter_default(operation, "path", "userId") == "user-1"
    assert parameter_default(operation, "path", "missing") is None
    assert render_json({"message": "成功"}) == '{\n  "message": "成功"\n}'
    assert "curl -X DELETE" in render_curl_sample(
        "/admin/users/{userId}",
        "delete",
        operation,
        {"reason": "不要"},
    )
    assert render_samples_section(
        "/admin/users/{userId}",
        "delete",
        operation,
        OperationSamples(request=None, response=None),
    )[-2] == "_なし_"


def test_operation_output_path_falls_back_to_default() -> None:
    assert operation_output_path(Path("out"), {}) == Path("out/default/api/if_gen.md")
    assert operation_output_path(Path("out"), {"summary": "Some API"}) == Path(
        "out/default/some_api/if_gen.md"
    )


def test_implementation_operation_paths_reads_router_operation_ids(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    router_path = api_root / "projects/create_api_access_request/router.py"
    cached_router_path = api_root / "projects/__pycache__/router.py"
    no_operation_router_path = api_root / "projects/no_operation/router.py"
    router_path.parent.mkdir(parents=True, exist_ok=True)
    cached_router_path.parent.mkdir(parents=True, exist_ok=True)
    no_operation_router_path.parent.mkdir(parents=True, exist_ok=True)
    source = """
from fastapi import APIRouter
router = APIRouter()

@router.post('/projects/{projectId}/api-access-requests', operation_id='createApiAccessRequest')
async def create_api_access_request():
    return {}
"""
    router_path.write_text(source, encoding="utf-8")
    cached_router_path.write_text(
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/cached', operation_id='cachedOperation')
async def cached():
    return {}
""",
        encoding="utf-8",
    )
    no_operation_router_path.write_text(
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/no-operation')
async def no_operation():
    return {}
""",
        encoding="utf-8",
    )

    assert router_operation_id(source, router_path) == "createApiAccessRequest"
    assert implementation_operation_paths(api_root) == {
        "createApiAccessRequest": Path("projects/create_api_access_request")
    }


def test_operation_samples_are_loaded_from_samples_module() -> None:
    api_path = Path("projects/create_api_access_request")

    assert sample_module_name(api_path) == "app.apis.projects.create_api_access_request.samples"
    sample = load_operation_sample(api_path)
    assert sample is not None
    assert sample.request is not None
    assert sample.response is not None
    assert sample.request["requestedReason"] == "決済画面から請求情報を参照するため"
    assert sample.response["derivedState"] == "PENDING"
    assert implementation_operation_samples({"createApiAccessRequest": api_path})[
        "createApiAccessRequest"
    ] == sample
    assert load_operation_sample(Path("missing/api")) is None


def test_module_sample_handles_missing_suffix() -> None:
    class SampleModule:
        VALUE: ClassVar[dict[str, int]] = {"x": 1}

    assert module_sample(SampleModule, "_REQUEST_SAMPLE") is None


def test_router_operation_helpers_handle_non_matches(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    router_path = api_root / "projects/bad/router.py"
    router_path.parent.mkdir(parents=True, exist_ok=True)
    source = """
from fastapi import APIRouter
router = APIRouter()

@router.get('/bad')
async def bad():
    return {}
"""
    router_path.write_text(source, encoding="utf-8")

    call = ast.parse("router.get('/bad')", mode="eval").body
    assert isinstance(call, ast.Call)
    assert literal_string(ast.parse("value", mode="eval").body) is None
    assert literal_string(None) is None
    assert keyword_value(call, "operation_id") is None
    assert router_operation_id(source, router_path) is None
    assert router_operation_id(
        """
@decorator
async def bad():
    return {}
""",
        router_path,
    ) is None
    assert router_operation_id(
        """
from fastapi import APIRouter
router = APIRouter()

@router.get('/bad', operation_id='')
async def bad():
    return {}
""",
        router_path,
    ) is None
    assert router_operation_id("VALUE = 'not a function'", router_path) is None
    assert implementation_operation_paths(api_root) == {}


def test_iter_operations_and_output_path() -> None:
    operations = iter_operations(OPENAPI)
    assert len(operations) == 1
    _path, _method, operation = operations[0]

    assert operation_output_path(Path("docs/spec/40.apis"), operation) == (
        Path("docs/spec/40.apis/admin_users/delete_admin_user/if_gen.md")
    )
    assert operation_output_path(
        Path("docs/spec/40.apis"),
        operation,
        {"deleteAdminUser": Path("admin/delete_user")},
    ) == Path("docs/spec/40.apis/admin/delete_user/if_gen.md")


def test_generate_from_openapi_writes_files(tmp_path: Path) -> None:
    written = generate_from_openapi(
        OPENAPI,
        tmp_path,
        {"deleteAdminUser": Path("admin/delete_user")},
        {
            "deleteAdminUser": OperationSamples(
                request={"reason": "不要", "notify": False},
                response={"userId": "user-1"},
            )
        },
    )

    assert written == [tmp_path / "admin" / "delete_user" / "if_gen.md"]
    content = written[0].read_text(encoding="utf-8")
    assert content.startswith("# DELETE /admin/users/{userId}")
    assert '"reason": "不要"' in content
    assert '"userId": "user-1"' in content


def test_arg_parser_defaults_and_main_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    default_args = build_arg_parser().parse_args([])
    assert default_args.output_dir.as_posix() == "docs/spec/40.apis"
    assert default_args.api_root.as_posix() == "src/app/apis"

    def operation_paths(_api_root: Path) -> dict[str, Path]:
        return {"deleteAdminUser": Path("admin/delete_user")}

    def operation_samples(_operation_paths: dict[str, Path]) -> dict[str, OperationSamples]:
        return {"deleteAdminUser": OperationSamples(request=None, response={"ok": True})}

    monkeypatch.setattr("tools.generate_openapi_if_specs.load_fastapi_openapi", lambda: OPENAPI)
    monkeypatch.setattr(
        "tools.generate_openapi_if_specs.implementation_operation_paths",
        operation_paths,
    )
    monkeypatch.setattr(
        "tools.generate_openapi_if_specs.implementation_operation_samples",
        operation_samples,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["generate_openapi_if_specs", "--output-dir", str(tmp_path)],
    )

    main()

    assert capsys.readouterr().out == "Generated 1 IF spec files.\n"
    assert (tmp_path / "admin" / "delete_user" / "if_gen.md").exists()
    assert '"ok": true' in (tmp_path / "admin" / "delete_user" / "if_gen.md").read_text(
        encoding="utf-8"
    )


def test_load_fastapi_openapi_returns_schema() -> None:
    openapi = load_fastapi_openapi()

    assert "paths" in openapi
