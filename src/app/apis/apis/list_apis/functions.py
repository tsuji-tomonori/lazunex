from __future__ import annotations

from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.apis.common import ApiDerivedState, ApiVisibility
from app.apis.apis.list_apis.generated import queries
from app.apis.apis.list_apis.schemas import (
    ApiListItemResponse,
    ApiListStageResponse,
    ListApisQuery,
    ListApisResponse,
)
from app.apis.common import raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.router_errors import (
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
    router_error_message_id,
    router_error_summary,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, SequencePage
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def has_api_list_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が API 一覧を参照できるかを判定する。"""
    return bool(caller.principal_id.strip())


async def get_viewable_apis(
    query: ListApisQuery,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> SequencePage[ApiListItemResponse]:
    """呼び出し元が参照可能な公開 API を検索する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(
                visibility=None,
                keyword=getattr(query, "keyword", None),
                after_api_code=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        _ = caller
        row_objects = cast(tuple[object, ...], tuple(rows))
        items = tuple(
            _to_response_item(row)
            if isinstance(row, queries.SelectApisRow)
            else cast(ApiListItemResponse, row)
            for row in row_objects
        )
        return SequencePage(items=items, next_token=None)
    return raise_missing_runtime_dependency("get_viewable_apis")


# @resource-free
async def apply_pagination(
    page: SequencePage[ApiListItemResponse],
    query: ListApisQuery,
) -> SequencePage[ApiListItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    _ = query
    return page


async def build_api_list_response(page: SequencePage[ApiListItemResponse]) -> ListApisResponse:
    """API 一覧レスポンスを組み立てる。"""
    return ListApisResponse(items=list(page.items), next_token=page.next_token)


async def build_caller_cannot_list_apis_response(
    query: ListApisQuery,
    caller: CallerIdentity,
) -> JSONResponse:
    """API 一覧参照権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "listApis.caller_cannot_list_apis",
        catalog_id="M001",
        summary="呼び出し元がAPI一覧を参照できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot list apis",
        when="呼び出し元がAPI一覧を参照できない場合。",
        why_production="API一覧の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot list apis",
        ),
        operator_action="actorPrincipalIdと認可条件を確認し、API一覧参照権限の不足を切り分ける。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot list apis",
            caller=caller,
            resource={
                "derivedState": query.derived_state,
                "keyword": query.keyword,
                "providerName": query.provider_name,
            },
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot list apis")


async def build_router_error_response(
    query: ListApisQuery,
    caller: CallerIdentity,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("listApis", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりAPI一覧取得が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別と直前の処理を確認する。",
        remediation_procedure="原因を特定し、再試行可能な処理は同一条件で再実行する。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            error_code=error_code_for_status(status_code_for_router_error(error)),
            error_message=str(error),
            error_exception_type=type(error).__name__,
        ),
        operator_action="同一routeの5xx率、直近deploy、DB状態を確認する。",
        runbook="RUNBOOK-unexpected-api-failure",
        context=router_log_context(
            status_code=status_code_for_router_error(error),
            detail=str(error),
            caller=caller,
            resource={
                "derivedState": query.derived_state,
                "keyword": query.keyword,
                "providerName": query.provider_name,
            },
            error=error,
        ),
    )
    return error_response_for_router_error(error)


def _to_response_item(row: queries.SelectApisRow) -> ApiListItemResponse:
    return ApiListItemResponse(
        api_id=row.api_id,
        api_code=row.api_code,
        name=row.name,
        description=row.description,
        provider_name=row.provider_name,
        visibility=ApiVisibility(row.visibility),
        derived_state=ApiDerivedState.PUBLISHED,
        stage=ApiListStageResponse(
            api_stage_id=row.api_stage_id,
            stage_name=row.apigw_stage_name,
            invoke_url=row.invoke_url,
        ),
        scope_full_name=row.scope_full_name,
    )
