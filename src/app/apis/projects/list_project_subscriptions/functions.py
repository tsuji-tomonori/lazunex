from __future__ import annotations

from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.common import AuthMode
from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.common import SubscriptionDerivedState
from app.apis.projects.list_project_subscriptions.generated import queries
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
    ProjectSubscriptionItemResponse,
)
from app.apis.router_errors import (
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
    router_error_message_id,
    router_error_summary,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


# @resource-free
async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project の参照を組み立てる。"""
    return ProjectRef(project_id=project_id)


async def has_project_subscription_view_permission(
    project: ProjectRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が Project subscription 一覧を参照できるかを判定する。"""
    _ = project
    return bool(caller.principal_id.strip())


async def get_project_subscriptions(
    project: ProjectRef,
    query: ListProjectSubscriptionsQuery,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> SequencePage[ProjectSubscriptionItemResponse]:
    """Project の active subscription を検索する。"""
    if session is not None and caller is not None:
        rows = await queries.select_subscriptions(
            session,
            queries.SelectSubscriptionsParams(
                actor_principal_id=caller.principal_id,
                project_id=project.project_id,
                app_client_id="",
                is_hub_admin=IdentityGroup.HUB_ADMIN in caller.groups,
                after_approved_at=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        row_objects = cast(tuple[object, ...], tuple(rows))
        items = tuple(
            _to_response_item(row)
            if isinstance(row, queries.SelectSubscriptionsRow)
            else cast(ProjectSubscriptionItemResponse, row)
            for row in row_objects
        )
        return SequencePage(items=items, next_token=None)
    return raise_missing_runtime_dependency("get_project_subscriptions")


# @resource-free
async def apply_pagination(
    page: SequencePage[ProjectSubscriptionItemResponse],
    query: ListProjectSubscriptionsQuery,
) -> SequencePage[ProjectSubscriptionItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    _ = query
    return page


async def build_project_subscription_list_response(
    page: SequencePage[ProjectSubscriptionItemResponse],
) -> ListProjectSubscriptionsResponse:
    """secret 値を含めずに Project subscription 一覧レスポンスを組み立てる。"""
    return ListProjectSubscriptionsResponse(items=list(page.items), next_token=page.next_token)


async def build_caller_cannot_list_project_subscriptions_response(
    project_id: ResourceId,
    caller: CallerIdentity,
) -> JSONResponse:
    """Project subscription 一覧参照権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "listProjectSubscriptions.caller_cannot_list_project_subscriptions",
        catalog_id="M001",
        summary="呼び出し元がProjectの利用可能API一覧を参照できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot list project subscriptions",
        when="呼び出し元が対象Projectのsubscription一覧を参照できない場合。",
        why_production="Project subscription一覧の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot list project subscriptions",
        ),
        operator_action="actorPrincipalId、projectId、Project権限を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot list project subscriptions",
            caller=caller,
            resource={"projectId": project_id},
        ),
    )
    return api_error_response(
        status.HTTP_403_FORBIDDEN,
        "caller cannot list project subscriptions",
    )


async def build_router_error_response(
    project_id: ResourceId,
    caller: CallerIdentity,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("listProjectSubscriptions", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりProject subscription一覧取得が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とprojectIdを確認する。",
        remediation_procedure="原因を特定し、再試行可能な処理は同一projectIdで再実行する。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            resource_project_id=str(project_id),
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
            resource={"projectId": project_id},
            error=error,
        ),
    )
    return error_response_for_router_error(error)


def _to_response_item(
    row: queries.SelectSubscriptionsRow,
) -> ProjectSubscriptionItemResponse:
    return ProjectSubscriptionItemResponse(
        subscription_id=row.subscription_id,
        api_id=row.api_id,
        api_code=row.api_code,
        api_name=row.api_name,
        api_stage_id=row.api_stage_id,
        stage_name=row.stage_name,
        invoke_url=row.invoke_url,
        scope_full_name=row.scope_full_name,
        approved_auth_mode=AuthMode(row.approved_auth_mode),
        derived_state=SubscriptionDerivedState.ACTIVE,
        approved_at=row.approved_at,
    )
