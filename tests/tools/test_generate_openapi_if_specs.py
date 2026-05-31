from pathlib import Path
from typing import Any, cast

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from tools.generate_openapi_if_specs import (
    build_arg_parser,
    generate_from_openapi,
    iter_operations,
    load_fastapi_openapi,
    main,
    object_field_rows,
    operation_output_path,
    parameter_rows,
    render_field_table,
    render_operation_markdown,
    render_response_details,
    render_response_summary,
    request_body_rows,
    response_media,
    response_summary_rows,
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
                "required": ["userId", "email", "status", "groups"],
                "properties": {
                    "userId": {"type": "string", "description": "対象ユーザーID。"},
                    "email": {"type": "string", "description": "メールアドレス。"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "deleted"],
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
                        "schema": {"type": "string", "minLength": 1},
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
    assert schema_constraints({"type": "string", "minLength": 1, "enum": ["a", "b"]}, schemas) == (
        "minLength=1, enum=a, b"
    )
    assert schema_components({"components": {"schemas": []}}) == {}
    assert schema_components({}) == {}


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
    )

    assert summary_rows[0] == ["200", "成功。", "application/json", "5 field(s)"]
    assert summary_rows[2] == ["204", "bodyなし。", "-", "-"]
    assert "# DELETE /admin/users/{userId}" in rendered
    assert "## Headers" in rendered
    assert "## Path Parameters" in rendered
    assert "## Query Parameters" in rendered
    assert "## Data" in rendered
    assert "## Responses" in rendered
    assert (
        "| `status` | `enum(active \\| deleted)` | yes | 状態。 | enum=active, deleted |"
        in rendered
    )
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


def test_operation_output_path_falls_back_to_default() -> None:
    assert operation_output_path(Path("out"), {}) == Path("out/default/api/IF.md")
    assert operation_output_path(Path("out"), {"summary": "Some API"}) == Path(
        "out/default/some_api/IF.md"
    )


def test_iter_operations_and_output_path() -> None:
    operations = iter_operations(OPENAPI)
    assert len(operations) == 1
    _path, _method, operation = operations[0]

    assert operation_output_path(Path("docs/spec/40.apis"), operation) == (
        Path("docs/spec/40.apis/admin_users/delete_admin_user/IF.md")
    )


def test_generate_from_openapi_writes_files(tmp_path: Path) -> None:
    written = generate_from_openapi(OPENAPI, tmp_path)

    assert written == [tmp_path / "admin_users" / "delete_admin_user" / "IF.md"]
    assert written[0].read_text(encoding="utf-8").startswith("# DELETE /admin/users/{userId}")


def test_arg_parser_defaults_and_main_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    default_args = build_arg_parser().parse_args([])
    assert default_args.output_dir.as_posix() == "docs/spec/40.apis"

    monkeypatch.setattr("tools.generate_openapi_if_specs.load_fastapi_openapi", lambda: OPENAPI)
    monkeypatch.setattr(
        "sys.argv",
        ["generate_openapi_if_specs", "--output-dir", str(tmp_path)],
    )

    main()

    assert capsys.readouterr().out == "Generated 1 IF spec files.\n"
    assert (tmp_path / "admin_users" / "delete_admin_user" / "IF.md").exists()


def test_load_fastapi_openapi_returns_schema() -> None:
    openapi = load_fastapi_openapi()

    assert "paths" in openapi
