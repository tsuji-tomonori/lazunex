from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _fixtures_dir() -> Path:
    return Path(os.environ.get("AWS_MOCK_FIXTURES_DIR", "/fixtures"))


def _load_fixture(filename: str, default: dict[str, Any]) -> dict[str, Any]:
    fixture_path = _fixtures_dir() / filename
    if not fixture_path.exists():
        return default
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _load_secret(secret_id: str) -> str:
    fixture_path = _fixtures_dir() / "secrets.json"
    if not fixture_path.exists():
        return "local-hash-pepper"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return str(data.get(secret_id, "local-hash-pepper"))


def reset_mock_state() -> None:
    AwsMockHandler.api_gateway_state = None
    AwsMockHandler.resource_server_state = None


class AwsMockHandler(BaseHTTPRequestHandler):
    server_version = "LazunexAwsMock/0.1"
    api_gateway_state: dict[str, Any] | None = None
    resource_server_state: dict[str, Any] | None = None

    def log_message(self, format: str, *args: object) -> None:
        sanitized_args = tuple(
            "<redacted>" if "secret" in str(arg).lower() else arg for arg in args
        )
        super().log_message(format, *sanitized_args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/__health":
            self._send_json({"status": "ok"})
            return
        if not self._has_sigv4_headers():
            self.send_error(HTTPStatus.FORBIDDEN, "missing SigV4 headers")
            return

        parts = self._path_parts(parsed.path)
        if len(parts) == 4 and parts[0] == "restapis" and parts[2] == "stages":
            self._handle_get_stage(parts[1], parts[3])
            return
        if len(parts) == 3 and parts[0] == "restapis" and parts[2] == "resources":
            self._handle_get_resources(parts[1])
            return
        if (
            len(parts) == 6
            and parts[0] == "restapis"
            and parts[2] == "resources"
            and parts[4] == "methods"
        ):
            self._handle_get_method(parts[1], parts[3], parts[5])
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if not self._has_sigv4_headers():
            self.send_error(HTTPStatus.FORBIDDEN, "missing SigV4 headers")
            return

        parsed = urlparse(self.path)
        parts = self._path_parts(parsed.path)
        body = self._read_json()
        if parsed.path == "/apikeys":
            self._send_json(
                {
                    "id": "mock-api-key-id",
                    "name": body.get("name", "mock-api-key"),
                    "value": "mock-api-key-secret-value",
                    "enabled": True,
                },
                status=HTTPStatus.CREATED,
            )
            return
        if parsed.path == "/usageplans":
            self._send_json(
                {"id": "mock-usage-plan-id", "name": body.get("name", "mock-usage-plan")},
                status=HTTPStatus.CREATED,
            )
            return
        if parsed.path.startswith("/usageplans/") and parsed.path.endswith("/keys"):
            self._send_json(
                {"id": "mock-usage-plan-key-id", "keyId": body.get("keyId", "mock-api-key-id")},
                status=HTTPStatus.CREATED,
            )
            return
        if len(parts) == 3 and parts[0] == "restapis" and parts[2] == "deployments":
            self._handle_create_deployment(parts[1], body)
            return

        target = self.headers.get("X-Amz-Target", "")
        if target == "AWSCognitoIdentityProviderService.CreateUserPoolClient":
            generate_secret = bool(body.get("GenerateSecret"))
            response: dict[str, Any] = {
                "UserPoolClient": {
                    "ClientId": "mock-confidential-client-id"
                    if generate_secret
                    else "mock-public-client-id",
                    "ClientName": body.get("ClientName", "mock-client"),
                    "AllowedOAuthScopes": body.get("AllowedOAuthScopes", []),
                }
            }
            if generate_secret:
                response["UserPoolClient"]["ClientSecret"] = "mock-client-secret-value"
            self._send_json(response)
            return
        if target == "AWSCognitoIdentityProviderService.DescribeUserPoolClient":
            self._send_json(
                {
                    "UserPoolClient": {
                        "ClientId": body.get("ClientId", "mock-client-id"),
                        "AllowedOAuthScopes": ["openid", "email", "profile"],
                    }
                }
            )
            return
        if target == "AWSCognitoIdentityProviderService.UpdateUserPoolClient":
            self._send_json(
                {
                    "UserPoolClient": {
                        "ClientId": body.get("ClientId", "mock-client-id"),
                        "AllowedOAuthScopes": body.get("AllowedOAuthScopes", []),
                    }
                }
            )
            return
        if target == "AWSCognitoIdentityProviderService.DescribeResourceServer":
            self._handle_describe_resource_server(body)
            return
        if target == "AWSCognitoIdentityProviderService.UpdateResourceServer":
            self._handle_update_resource_server(body)
            return
        if target == "secretsmanager.GetSecretValue":
            self._send_json(
                {
                    "ARN": "arn:aws:secretsmanager:ap-northeast-1:000000000000:secret:local",
                    "Name": body.get("SecretId", "local/hash-pepper"),
                    "SecretString": _load_secret(str(body.get("SecretId", "local/hash-pepper"))),
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:
        if not self._has_sigv4_headers():
            self.send_error(HTTPStatus.FORBIDDEN, "missing SigV4 headers")
            return

        parsed = urlparse(self.path)
        parts = self._path_parts(parsed.path)
        body = self._read_json()
        if parsed.path.startswith("/usageplans/"):
            usage_plan_id = parts[1]
            self._send_json(
                {
                    "id": usage_plan_id,
                    "apiStages": [{"apiId": "mock-rest-api-id", "stage": "prod"}],
                }
            )
            return
        if (
            len(parts) == 6
            and parts[0] == "restapis"
            and parts[2] == "resources"
            and parts[4] == "methods"
        ):
            self._handle_update_method(parts[1], parts[3], parts[5], body)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _path_parts(self, path: str) -> list[str]:
        return [unquote(part) for part in path.split("/") if part]

    def _api_gateway_state(self) -> dict[str, Any]:
        if AwsMockHandler.api_gateway_state is None:
            AwsMockHandler.api_gateway_state = _load_fixture(
                "api_gateway.json",
                {
                    "restApis": {
                        "abc123def4": {
                            "stages": {
                                "prod": {"stageName": "prod", "deploymentId": "mock-deploy-0"}
                            },
                            "resources": [
                                {
                                    "id": "mock-resource-root",
                                    "path": "/",
                                    "resourceMethods": {"GET": {}},
                                }
                            ],
                            "methods": {
                                "mock-resource-root": {
                                    "GET": {
                                        "httpMethod": "GET",
                                        "apiKeyRequired": False,
                                        "authorizationType": "NONE",
                                        "authorizationScopes": [],
                                    }
                                }
                            },
                            "deployments": [],
                        }
                    }
                },
            )
        return AwsMockHandler.api_gateway_state

    def _resource_server_state(self) -> dict[str, Any]:
        if AwsMockHandler.resource_server_state is None:
            AwsMockHandler.resource_server_state = _load_fixture(
                "resource_servers.json",
                {
                    "resourceServers": {
                        "api-hub": {
                            "Identifier": "api-hub",
                            "Name": "Lazunex API Hub",
                            "Scopes": [],
                        }
                    }
                },
            )
        return AwsMockHandler.resource_server_state

    def _rest_api(self, rest_api_id: str) -> dict[str, Any] | None:
        value = self._api_gateway_state().get("restApis", {}).get(rest_api_id)
        return value if isinstance(value, dict) else None

    def _handle_get_stage(self, rest_api_id: str, stage_name: str) -> None:
        rest_api = self._rest_api(rest_api_id)
        stage = rest_api.get("stages", {}).get(stage_name) if rest_api else None
        if not isinstance(stage, dict):
            self.send_error(HTTPStatus.NOT_FOUND, "stage not found")
            return
        self._send_json(stage)

    def _handle_get_resources(self, rest_api_id: str) -> None:
        rest_api = self._rest_api(rest_api_id)
        if rest_api is None:
            self.send_error(HTTPStatus.NOT_FOUND, "rest api not found")
            return
        self._send_json({"items": list(rest_api.get("resources", []))})

    def _method(
        self,
        rest_api_id: str,
        resource_id: str,
        http_method: str,
    ) -> dict[str, Any] | None:
        rest_api = self._rest_api(rest_api_id)
        if rest_api is None:
            return None
        method = rest_api.get("methods", {}).get(resource_id, {}).get(http_method.upper())
        return method if isinstance(method, dict) else None

    def _handle_get_method(self, rest_api_id: str, resource_id: str, http_method: str) -> None:
        method = self._method(rest_api_id, resource_id, http_method)
        if method is None:
            self.send_error(HTTPStatus.NOT_FOUND, "method not found")
            return
        self._send_json(method)

    def _handle_update_method(
        self,
        rest_api_id: str,
        resource_id: str,
        http_method: str,
        body: dict[str, Any],
    ) -> None:
        method = self._method(rest_api_id, resource_id, http_method)
        if method is None:
            self.send_error(HTTPStatus.NOT_FOUND, "method not found")
            return
        for operation in body.get("patchOperations", []):
            path = operation.get("path")
            value = operation.get("value")
            if path == "/apiKeyRequired":
                method["apiKeyRequired"] = str(value).lower() == "true"
            elif path == "/authorizationType":
                method["authorizationType"] = value
            elif path == "/authorizerId":
                method["authorizerId"] = value
            elif path == "/authorizationScopes":
                scopes = method.setdefault("authorizationScopes", [])
                if value not in scopes:
                    scopes.append(value)
        self._send_json(method)

    def _handle_create_deployment(self, rest_api_id: str, body: dict[str, Any]) -> None:
        rest_api = self._rest_api(rest_api_id)
        if rest_api is None:
            self.send_error(HTTPStatus.NOT_FOUND, "rest api not found")
            return
        deployment_id = f"mock-deployment-{len(rest_api.get('deployments', [])) + 1}"
        deployment = {
            "id": deployment_id,
            "description": body.get("description", "mock deployment"),
        }
        rest_api.setdefault("deployments", []).append(deployment)
        stage_name = body.get("stageName")
        if stage_name:
            rest_api.setdefault("stages", {}).setdefault(stage_name, {"stageName": stage_name})[
                "deploymentId"
            ] = deployment_id
        self._send_json(deployment, status=HTTPStatus.CREATED)

    def _resource_server(self, identifier: str) -> dict[str, Any] | None:
        value = self._resource_server_state().get("resourceServers", {}).get(identifier)
        return value if isinstance(value, dict) else None

    def _handle_describe_resource_server(self, body: dict[str, Any]) -> None:
        resource_server = self._resource_server(str(body.get("Identifier", "api-hub")))
        if resource_server is None:
            self.send_error(HTTPStatus.NOT_FOUND, "resource server not found")
            return
        self._send_json({"ResourceServer": resource_server})

    def _handle_update_resource_server(self, body: dict[str, Any]) -> None:
        identifier = str(body.get("Identifier", "api-hub"))
        resource_server = self._resource_server(identifier)
        if resource_server is None:
            self.send_error(HTTPStatus.NOT_FOUND, "resource server not found")
            return
        resource_server["Name"] = body.get("Name", resource_server.get("Name", "Lazunex API Hub"))
        resource_server["Scopes"] = body.get("Scopes", [])
        self._send_json({"ResourceServer": resource_server})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _has_sigv4_headers(self) -> bool:
        authorization = self.headers.get("Authorization", "")
        return (
            "AWS4-HMAC-SHA256" in authorization
            and bool(self.headers.get("X-Amz-Date"))
            and bool(self.headers.get("X-Amz-Security-Token"))
        )

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/x-amz-json-1.1")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    httpd = ThreadingHTTPServer(("0.0.0.0", 8080), AwsMockHandler)  # noqa: S104
    httpd.serve_forever()


if __name__ == "__main__":
    main()
