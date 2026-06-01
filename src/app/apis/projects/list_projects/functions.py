from __future__ import annotations

from typing import NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_projects import queries
from app.apis.projects.list_projects.schemas import (
    ListProjectsQuery,
    ListProjectsResponse,
    ProjectListItemResponse,
)
from app.apis.sequence_types import CallerIdentity, SequencePage


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def validate_project_list_query(query: ListProjectsQuery) -> ListProjectsQuery:
    """Project 一覧取得条件を検証する。"""
    return query


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def has_project_list_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が Project 一覧を参照できるかを判定する。"""
    _ = caller
    return True


async def get_viewable_projects(
    query: ListProjectsQuery,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> SequencePage[ProjectListItemResponse]:
    """呼び出し元が参照可能な Project を検索する。"""
    if session is not None:
        rows = await queries.select_projects(
            session,
            queries.SelectProjectsParams(
                actor_principal_id=caller.principal_id,
                is_hub_admin="hub-admin" in caller.groups,
                after_project_code=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        return SequencePage(
            items=cast(tuple[ProjectListItemResponse, ...], tuple(rows)),
            next_token=None,
        )
    return _sequence_placeholder("get_viewable_projects")


async def apply_pagination(
    page: SequencePage[ProjectListItemResponse],
    query: ListProjectsQuery,
) -> SequencePage[ProjectListItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    _ = query
    return page


async def build_project_list_response(
    page: SequencePage[ProjectListItemResponse],
) -> ListProjectsResponse:
    """Project 一覧レスポンスを組み立てる。"""
    return ListProjectsResponse(items=list(page.items), next_token=page.next_token)
