from __future__ import annotations

import inspect
from datetime import UTC, datetime
from typing import cast, get_args, get_origin
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.approve_api_access_request import queries as approve_queries
from app.apis.api_access_requests.reject_api_access_request import queries as reject_queries
from app.apis.apis.publish_api import queries as publish_queries
from app.apis.projects.create_api_access_request import queries as create_access_queries
from app.apis.projects.create_project import queries as create_project_queries
from app.apis.projects.update_project_public_client import queries as update_public_queries

pytestmark = pytest.mark.anyio


async def test_select_idempotency_query_wrappers(monkeypatch: pytest.MonkeyPatch) -> None:
    session = cast(AsyncSession, object())
    calls: list[str] = []
    row = {
        "idempotency_record_id": uuid4(),
        "idempotency_key": "idem-key",
        "request_hash": "hash",
        "operation_id": uuid4(),
        "response_payload": {"ok": True},
        "expires_at": datetime.now(UTC),
        "created_at": datetime.now(UTC),
    }

    async def fetch_all(
        _session: AsyncSession,
        _sql_path: object,
        _params: BaseModel,
        row_model: type[BaseModel],
    ) -> list[BaseModel]:
        calls.append(row_model.__name__)
        return [row_model.model_validate(row)]

    for module in (
        approve_queries,
        reject_queries,
        publish_queries,
        create_access_queries,
        create_project_queries,
        update_public_queries,
    ):
        monkeypatch.setattr(module, "fetch_all", fetch_all)
        result = await module.select_idempotency_records(
            session,
            module.SelectIdempotencyRecordsParams(idempotency_key="idem-key"),
        )
        assert result[0].idempotency_key == "idem-key"

    assert calls.count("SelectIdempotencyRecordsRow") == 6


async def test_publish_stage_unique_key_query_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    api_id = UUID("7b0d4a98-0000-0000-0000-000000000001")
    api_stage_id = UUID("7b0d4a98-0000-0000-0000-000000000101")

    async def fetch_all(
        _session: AsyncSession,
        _sql_path: object,
        _params: BaseModel,
        row_model: type[BaseModel],
    ) -> list[BaseModel]:
        return [
            row_model.model_validate(
                {
                    "api_stage_id": api_stage_id,
                    "api_id": api_id,
                    "aws_account_id": "local",
                    "aws_region": "ap-northeast-1",
                    "apigw_rest_api_id": "rest-api-id",
                    "apigw_stage_name": "prod",
                }
            )
        ]

    monkeypatch.setattr(publish_queries, "fetch_all", fetch_all)

    result = await publish_queries.select_api_gateway_stages_by_unique_key(
        session,
        publish_queries.SelectApiGatewayStagesByUniqueKeyParams(
            aws_account_id="local",
            aws_region="ap-northeast-1",
            apigw_rest_api_id="rest-api-id",
            apigw_stage_name="prod",
        ),
    )

    assert result[0].api_stage_id == api_stage_id


async def test_create_project_new_insert_query_wrappers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    calls: list[str] = []

    async def execute_sql(
        _session: AsyncSession,
        sql_path: object,
        _params: BaseModel,
    ) -> None:
        calls.append(str(sql_path))

    monkeypatch.setattr(create_project_queries, "execute_sql", execute_sql)

    await create_project_queries.insert_audit_events(
        session,
        create_project_queries.InsertAuditEventsParams(
            audit_event_id=uuid4(),
            actor_principal_id="admin-001",
            project_id=uuid4(),
            operation_id=uuid4(),
            source_ip="127.0.0.1",
            user_agent="pytest",
            details={"ok": True},
            now=datetime.now(UTC),
        ),
    )
    await create_project_queries.insert_project_cognito_client_events(
        session,
        create_project_queries.InsertProjectCognitoClientEventsParams(
            event_id=uuid4(),
            project_cognito_client_id=uuid4(),
            event_name="PROJECT_COGNITO_CLIENT_CREATED",
            actor_principal_id="admin-001",
            actor_type="USER",
            now=datetime.now(UTC),
            reason="created",
            correlation_id="corr-001",
            idempotency_key="idem-key",
            event_payload={"ok": True},
        ),
    )

    assert len(calls) == 2


def _dummy_value(name: str, annotation: object) -> object:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if annotation is str:
        return "value"
    if annotation is datetime or name in {"now", "started_at", "finished_at", "expires_at"}:
        return datetime.now(UTC)
    if annotation is bool:
        return False
    if annotation is int:
        return 1
    if annotation is dict or origin is dict:
        return {"ok": True}
    if origin is list:
        return []
    if origin is tuple:
        return ()
    if origin is type(None):
        return None
    if origin is None and args:
        return _dummy_value(name, args[0])
    if annotation is UUID or "id" in name:
        return uuid4()
    return "value"


def _params_for(params_type: type[BaseModel]) -> BaseModel:
    return params_type.model_validate(
        {
            name: _dummy_value(name, field.annotation)
            for name, field in params_type.model_fields.items()
        }
    )


async def test_changed_api_query_wrappers_are_callable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    calls: list[str] = []

    async def fetch_all(
        _session: AsyncSession,
        sql_path: object,
        _params: BaseModel,
        _row_model: type[BaseModel],
    ) -> list[BaseModel]:
        calls.append(str(sql_path))
        return []

    async def execute_sql(
        _session: AsyncSession,
        sql_path: object,
        _params: BaseModel,
    ) -> None:
        calls.append(str(sql_path))

    for module in (
        approve_queries,
        reject_queries,
        publish_queries,
        create_access_queries,
        create_project_queries,
        update_public_queries,
    ):
        monkeypatch.setattr(module, "fetch_all", fetch_all)
        monkeypatch.setattr(module, "execute_sql", execute_sql)
        for name, function in module.__dict__.items():
            if not name.startswith(("select_", "insert_", "update_", "delete_")):
                continue
            if not inspect.iscoroutinefunction(function):
                continue
            params_name = "".join(part.title() for part in name.split("_")) + "Params"
            params_type = module.__dict__[params_name]
            await function(session, _params_for(params_type))

    assert calls
