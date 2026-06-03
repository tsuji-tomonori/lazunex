from __future__ import annotations

from typing import NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.common import AccessRequestDerivedState, AuthMode
from app.apis.projects.list_project_api_access_requests import queries
from app.apis.projects.list_project_api_access_requests.schemas import (
    AccessRequestReviewResponse,
    ListProjectApiAccessRequestsQuery,
    ListProjectApiAccessRequestsResponse,
    ProjectApiAccessRequestItemResponse,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_project_access_request_list_query(
    query: ListProjectApiAccessRequestsQuery,
) -> ListProjectApiAccessRequestsQuery:
    """Project 利用申請一覧取得条件を検証する。"""
    return query


async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project を取得する。"""
    return ProjectRef(project_id=project_id)


async def has_project_access_request_view_permission(
    project: ProjectRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が Project 内の利用申請履歴を参照できるかを判定する。"""
    _ = project, caller
    return True


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
                is_hub_admin="hub-admin" in caller.groups,
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
    return _sequence_placeholder("get_project_access_requests")


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
