from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _load_secret(secret_id: str) -> str:
    fixtures_dir = Path(os.environ.get("AWS_MOCK_FIXTURES_DIR", "/fixtures"))
    fixture_path = fixtures_dir / "secrets.json"
    if not fixture_path.exists():
        return "local-hash-pepper"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return str(data.get(secret_id, "local-hash-pepper"))


class AwsMockHandler(BaseHTTPRequestHandler):
    server_version = "LazunexAwsMock/0.1"

    def log_message(self, format: str, *args: object) -> None:
        sanitized_args = tuple(
            "<redacted>" if "secret" in str(arg).lower() else arg for arg in args
        )
        super().log_message(format, *sanitized_args)

    def do_GET(self) -> None:
        if self.path == "/__health":
            self._send_json({"status": "ok"})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if not self._has_sigv4_headers():
            self.send_error(HTTPStatus.FORBIDDEN, "missing SigV4 headers")
            return
        body = self._read_json()
        if self.path == "/apikeys":
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
        if self.path == "/usageplans":
            self._send_json(
                {"id": "mock-usage-plan-id", "name": body.get("name", "mock-usage-plan")},
                status=HTTPStatus.CREATED,
            )
            return
        if self.path.startswith("/usageplans/") and self.path.endswith("/keys"):
            self._send_json(
                {"id": "mock-usage-plan-key-id", "keyId": body.get("keyId", "mock-api-key-id")},
                status=HTTPStatus.CREATED,
            )
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
        if target == "AWSCognitoIdentityProviderService.UpdateResourceServer":
            self._send_json({"ResourceServer": {"Identifier": body.get("Identifier", "api-hub")}})
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
        if self.path.startswith("/usageplans/"):
            usage_plan_id = self.path.split("/")[2]
            self._send_json(
                {
                    "id": usage_plan_id,
                    "apiStages": [{"apiId": "mock-rest-api-id", "stage": "prod"}],
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)

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
