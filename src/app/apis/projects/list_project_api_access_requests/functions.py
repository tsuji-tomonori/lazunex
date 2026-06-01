from __future__ import annotations

from typing import NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_project_api_access_requests import queries
from app.apis.projects.list_project_api_access_requests.schemas import (
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
                decision="PENDING",
                after_requested_at=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        return SequencePage(
            items=cast(tuple[ProjectApiAccessRequestItemResponse, ...], tuple(rows)),
            next_token=None,
        )
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
