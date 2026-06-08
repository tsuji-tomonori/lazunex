from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.apis.common import ApiDerivedState, ApiVisibility, ReviewerRole, ScopeConfigObserved
from app.apis.apis.get_api.generated import queries
from app.apis.apis.get_api.schemas import (
    ApiDetailStageResponse,
    ApiReviewerResponse,
    ApiScopeResponse,
    GetApiResponse,
)
from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
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
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId
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


async def get_api_detail(
    api_id: ResourceId,
    session: AsyncSession | None = None,
) -> GetApiResponse:
    """API 詳細レスポンスに必要な情報を取得する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_id=api_id),
        )
        if not rows:
            raise ApiFunctionError(
                status.HTTP_404_NOT_FOUND,
                "API not found",
                summary="対象 API が存在しない場合。",
            )
        first = rows[0]
        return GetApiResponse(
            api_id=first.api_id,
            api_code=first.api_code,
            name=first.name,
            description=first.description,
            provider_name=first.provider_name,
            provider_contact=first.provider_contact,
            owner_principal_id=first.owner_principal_id,
            visibility=ApiVisibility(first.visibility),
            derived_state=ApiDerivedState.PUBLISHED,
            stage=ApiDetailStageResponse(
                api_stage_id=first.api_stage_id,
                aws_account_id=first.aws_account_id,
                aws_region=first.aws_region,
                rest_api_id=first.apigw_rest_api_id,
                stage_name=first.apigw_stage_name,
                invoke_url=first.invoke_url,
                custom_domain_url=first.custom_domain_url,
                api_key_required_observed=first.api_key_required_observed,
                scope_config_observed=_scope_config_observed(first.scope_config_observed),
            ),
            scope=ApiScopeResponse(
                scope_name=first.scope_name,
                scope_full_name=first.scope_full_name,
            ),
            reviewers=[
                ApiReviewerResponse(
                    reviewer_principal_id=row.reviewer_principal_id,
                    reviewer_role=ReviewerRole(row.reviewer_role),
                )
                for row in rows
            ],
        )
    return raise_missing_runtime_dependency("get_api_detail")


async def is_viewable_api(
    api: GetApiResponse,
    caller: CallerIdentity,
) -> bool:
    """対象 API が呼び出し元から参照可能かを判定する。"""
    if api.visibility == ApiVisibility.INTERNAL:
        return True
    return (
        IdentityGroup.HUB_ADMIN in caller.groups
        or api.owner_principal_id == caller.principal_id
        or any(reviewer.reviewer_principal_id == caller.principal_id for reviewer in api.reviewers)
    )


async def build_api_detail_response(api: GetApiResponse) -> GetApiResponse:
    """API 詳細レスポンスを組み立てる。"""
    return GetApiResponse(
        api_id=api.api_id,
        api_code=api.api_code,
        name=api.name,
        description=api.description,
        provider_name=api.provider_name,
        provider_contact=api.provider_contact,
        owner_principal_id=api.owner_principal_id,
        visibility=api.visibility,
        derived_state=api.derived_state,
        stage=ApiDetailStageResponse(
            api_stage_id=api.stage.api_stage_id,
            aws_account_id=api.stage.aws_account_id,
            aws_region=api.stage.aws_region,
            rest_api_id=api.stage.rest_api_id,
            stage_name=api.stage.stage_name,
            invoke_url=api.stage.invoke_url,
            custom_domain_url=api.stage.custom_domain_url,
            api_key_required_observed=api.stage.api_key_required_observed,
            scope_config_observed=api.stage.scope_config_observed,
        ),
        scope=ApiScopeResponse(
            scope_name=api.scope.scope_name,
            scope_full_name=api.scope.scope_full_name,
        ),
        reviewers=[
            ApiReviewerResponse(
                reviewer_principal_id=reviewer.reviewer_principal_id,
                reviewer_role=reviewer.reviewer_role,
            )
            for reviewer in api.reviewers
        ],
    )


async def build_caller_cannot_view_api_response(
    api_id: ResourceId,
    caller: CallerIdentity,
) -> JSONResponse:
    """API 詳細参照権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "getApi.caller_cannot_view_api",
        catalog_id="M001",
        summary="呼び出し元がAPI詳細を参照できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot view api",
        when="呼び出し元が対象APIを参照できない場合。",
        why_production="API詳細の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            resource_api_id=str(api_id),
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot view api",
        ),
        operator_action="actorPrincipalId、apiId、API参照権限を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot view api",
            caller=caller,
            resource={"apiId": api_id},
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot view api")


async def build_router_error_response(
    api_id: ResourceId,
    caller: CallerIdentity,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("getApi", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりAPI詳細取得が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とapiIdを確認する。",
        remediation_procedure="原因を特定し、再試行可能な処理は同一apiIdで再実行する。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            resource_api_id=str(api_id),
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
            resource={"apiId": api_id},
            error=error,
        ),
    )
    return error_response_for_router_error(error)


def _scope_config_observed(value: str) -> ScopeConfigObserved:
    if value in {"VERIFY_ONLY", "PATCH_ALL_METHODS"}:
        return ScopeConfigObserved.VERIFIED
    return ScopeConfigObserved(value)
