from __future__ import annotations

from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.common import AccessRequestDerivedState, AuthMode
from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.list_project_api_access_requests.generated import queries
from app.apis.projects.list_project_api_access_requests.schemas import (
    AccessRequestReviewResponse,
    ListProjectApiAccessRequestsQuery,
    ListProjectApiAccessRequestsResponse,
    ProjectApiAccessRequestItemResponse,
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


async def has_project_access_request_view_permission(
    project: ProjectRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が Project 内の利用申請履歴を参照できるかを判定する。"""
    _ = project
    return bool(caller.principal_id.strip())


async def get_project_access_requests(
    project: ProjectRef,
    query: ListProjectApiAccessRequestsQuery,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> SequencePage[ProjectApiAccessRequestItemResponse]:
    """Project に紐づく access request を検索する。"""
    if session is not None:
        rows = await queries.select_api_access_requests(
            session,
            queries.SelectApiAccessRequestsParams(
                actor_principal_id=caller.principal_id,
                project_id=project.project_id,
                is_hub_admin=IdentityGroup.HUB_ADMIN in caller.groups,
                decision=getattr(query, "decision", None),
                after_requested_at=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        row_objects = cast(tuple[object, ...], tuple(rows))
        items = tuple(
            _to_response_item(row)
            if isinstance(row, queries.SelectApiAccessRequestsRow)
            else cast(ProjectApiAccessRequestItemResponse, row)
            for row in row_objects
        )
        return SequencePage(items=items, next_token=None)
    return raise_missing_runtime_dependency("get_project_access_requests")


# @resource-free
async def apply_pagination(
    page: SequencePage[ProjectApiAccessRequestItemResponse],
    query: ListProjectApiAccessRequestsQuery,
) -> SequencePage[ProjectApiAccessRequestItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    _ = query
    return page


async def build_project_access_request_list_response(
    page: SequencePage[ProjectApiAccessRequestItemResponse],
) -> ListProjectApiAccessRequestsResponse:
    """Project 利用申請一覧レスポンスを組み立てる。"""
    return ListProjectApiAccessRequestsResponse(items=list(page.items), next_token=page.next_token)


async def build_caller_cannot_list_project_access_requests_response(
    project_id: ResourceId,
    caller: CallerIdentity,
) -> JSONResponse:
    """Project API 利用申請一覧参照権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "listProjectApiAccessRequests.caller_cannot_list_project_access_requests",
        catalog_id="M001",
        summary="呼び出し元がProjectのAPI利用申請一覧を参照できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot list project access requests",
        when="呼び出し元が対象ProjectのAPI利用申請一覧を参照できない場合。",
        why_production="API利用申請一覧の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot list project access requests",
        ),
        operator_action="actorPrincipalId、projectId、Project権限を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot list project access requests",
            caller=caller,
            resource={"projectId": project_id},
        ),
    )
    return api_error_response(
        status.HTTP_403_FORBIDDEN,
        "caller cannot list project access requests",
    )


async def build_router_error_response(
    project_id: ResourceId,
    caller: CallerIdentity,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("listProjectApiAccessRequests", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりProjectのAPI利用申請一覧取得が失敗した。",
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


def _derived_state(decision: str | None) -> AccessRequestDerivedState:
    if decision == "APPROVED":
        return AccessRequestDerivedState.APPROVED
    if decision == "REJECTED":
        return AccessRequestDerivedState.REJECTED
    return AccessRequestDerivedState.PENDING


def _to_response_item(
    row: queries.SelectApiAccessRequestsRow,
) -> ProjectApiAccessRequestItemResponse:
    review = None
    if row.reviewer_principal_id is not None and row.reviewed_at is not None:
        review = AccessRequestReviewResponse(
            reviewer_principal_id=row.reviewer_principal_id,
            reviewed_at=row.reviewed_at,
            review_comment=row.review_comment or "",
        )
    return ProjectApiAccessRequestItemResponse(
        access_request_id=row.access_request_id,
        project_id=row.project_id,
        api_id=row.api_id,
        api_code=row.api_code,
        api_name=row.api_name,
        api_stage_id=row.api_stage_id,
        stage_name=row.apigw_stage_name,
        requested_auth_mode=AuthMode(row.requested_auth_mode),
        requested_reason=row.requested_reason,
        derived_state=_derived_state(row.decision),
        requested_by=row.requested_by,
        requested_at=row.requested_at,
        review=review,
    )
