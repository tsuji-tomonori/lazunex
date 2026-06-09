from __future__ import annotations

import importlib.util
import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

_SERVER_PATH = Path(__file__).parents[2] / "local" / "aws_mock" / "server.py"
_SERVER_SPEC = importlib.util.spec_from_file_location("aws_mock_server", _SERVER_PATH)
assert _SERVER_SPEC is not None
assert _SERVER_SPEC.loader is not None
_SERVER_MODULE = importlib.util.module_from_spec(_SERVER_SPEC)
_SERVER_SPEC.loader.exec_module(_SERVER_MODULE)
AwsMockHandler = _SERVER_MODULE.AwsMockHandler
reset_mock_state = _SERVER_MODULE.reset_mock_state


@contextmanager
def aws_mock_server(fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    monkeypatch.setenv("AWS_MOCK_FIXTURES_DIR", str(fixtures_dir))
    reset_mock_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), AwsMockHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = httpd.server_address
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()
        reset_mock_state()


def signed_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "Authorization": (
            "AWS4-HMAC-SHA256 "
            "Credential=local/20260609/ap-northeast-1/service/aws4_request"
        ),
        "X-Amz-Date": "20260609T000000Z",
        "X-Amz-Security-Token": "local-session-token",
    }
    headers.update(extra or {})
    return headers


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload or {}).encode() if payload is not None else None
    request = Request(  # noqa: S310
        f"{base_url}{path}",
        data=body,
        headers=signed_headers(headers),
        method=method,
    )
    with urlopen(request, timeout=5) as response:  # noqa: S310
        return json.loads(response.read().decode())


def write_fixtures(fixtures_dir: Path) -> None:
    fixtures_dir.mkdir(exist_ok=True)
    (fixtures_dir / "api_gateway.json").write_text(
        json.dumps(
            {
                "restApis": {
                    "abc123def4": {
                        "stages": {
                            "prod": {
                                "stageName": "prod",
                                "deploymentId": "mock-deployment-0",
                            }
                        },
                        "resources": [
                            {
                                "id": "resource-1",
                                "path": "/invoices",
                                "resourceMethods": {"GET": {}},
                            }
                        ],
                        "methods": {
                            "resource-1": {
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
            }
        ),
        encoding="utf-8",
    )
    (fixtures_dir / "resource_servers.json").write_text(
        json.dumps(
            {
                "resourceServers": {
                    "api-hub": {
                        "Identifier": "api-hub",
                        "Name": "Lazunex API Hub",
                        "Scopes": [],
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_api_gateway_publish_api_routes_keep_mutated_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_fixtures(tmp_path)
    with aws_mock_server(tmp_path, monkeypatch) as base_url:
        stage = request_json(base_url, "GET", "/restapis/abc123def4/stages/prod")
        assert stage == {"stageName": "prod", "deploymentId": "mock-deployment-0"}

        resources = request_json(base_url, "GET", "/restapis/abc123def4/resources?limit=500")
        assert resources["items"][0]["resourceMethods"] == {"GET": {}}

        method = request_json(
            base_url,
            "GET",
            "/restapis/abc123def4/resources/resource-1/methods/GET",
        )
        assert method["apiKeyRequired"] is False

        updated = request_json(
            base_url,
            "PATCH",
            "/restapis/abc123def4/resources/resource-1/methods/GET",
            {
                "patchOperations": [
                    {"op": "replace", "path": "/apiKeyRequired", "value": "true"},
                    {
                        "op": "replace",
                        "path": "/authorizationType",
                        "value": "COGNITO_USER_POOLS",
                    },
                    {"op": "replace", "path": "/authorizerId", "value": "auth123"},
                    {
                        "op": "add",
                        "path": "/authorizationScopes",
                        "value": "api-hub/api:billing-api-v1:invoke",
                    },
                ]
            },
        )
        assert updated["apiKeyRequired"] is True
        assert updated["authorizationType"] == "COGNITO_USER_POOLS"
        assert updated["authorizerId"] == "auth123"
        assert updated["authorizationScopes"] == ["api-hub/api:billing-api-v1:invoke"]

        deployment = request_json(
            base_url,
            "POST",
            "/restapis/abc123def4/deployments",
            {"stageName": "prod", "description": "publishApi local smoke"},
        )
        assert deployment["id"] == "mock-deployment-1"
        stage_after_deployment = request_json(base_url, "GET", "/restapis/abc123def4/stages/prod")
        assert stage_after_deployment["deploymentId"] == "mock-deployment-1"


def test_cognito_resource_server_describe_and_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_fixtures(tmp_path)
    with aws_mock_server(tmp_path, monkeypatch) as base_url:
        described = request_json(
            base_url,
            "POST",
            "/",
            {"UserPoolId": "local-user-pool", "Identifier": "api-hub"},
            {"X-Amz-Target": "AWSCognitoIdentityProviderService.DescribeResourceServer"},
        )
        assert described["ResourceServer"]["Identifier"] == "api-hub"
        assert described["ResourceServer"]["Scopes"] == []

        updated = request_json(
            base_url,
            "POST",
            "/",
            {
                "UserPoolId": "local-user-pool",
                "Identifier": "api-hub",
                "Name": "Lazunex API Hub",
                "Scopes": [
                    {
                        "ScopeName": "api:billing-api-v1:invoke",
                        "ScopeDescription": "Billing API invoke",
                    }
                ],
            },
            {"X-Amz-Target": "AWSCognitoIdentityProviderService.UpdateResourceServer"},
        )
        assert updated["ResourceServer"]["Scopes"] == [
            {
                "ScopeName": "api:billing-api-v1:invoke",
                "ScopeDescription": "Billing API invoke",
            }
        ]


def test_sigv4_headers_are_required_for_aws_operations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_fixtures(tmp_path)
    with aws_mock_server(tmp_path, monkeypatch) as base_url:
        with (
            pytest.raises(HTTPError) as error,
            urlopen(f"{base_url}/restapis/abc123def4/resources", timeout=5),  # noqa: S310
        ):
            pass
        assert error.value.code == 403
