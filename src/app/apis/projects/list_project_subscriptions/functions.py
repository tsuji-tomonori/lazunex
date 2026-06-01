from __future__ import annotations

from typing import NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_project_subscriptions import queries
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
    ProjectSubscriptionItemResponse,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_project_subscription_list_query(
    query: ListProjectSubscriptionsQuery,
) -> ListProjectSubscriptionsQuery:
    """Project subscription 一覧取得条件を検証する。"""
    return _sequence_placeholder("validate_project_subscription_list_query")


async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project を取得する。"""
    return _sequence_placeholder("get_project")


async def has_project_subscription_view_permission(
    project: ProjectRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が Project subscription 一覧を参照できるかを判定する。"""
    return _sequence_placeholder("has_project_subscription_view_permission")


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
                is_hub_admin="hub-admin" in caller.groups,
                after_approved_at=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        return SequencePage(
            items=cast(tuple[ProjectSubscriptionItemResponse, ...], tuple(rows)),
            next_token=None,
        )
    return _sequence_placeholder("get_project_subscriptions")


async def apply_pagination(
    page: SequencePage[ProjectSubscriptionItemResponse],
    query: ListProjectSubscriptionsQuery,
) -> SequencePage[ProjectSubscriptionItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    return _sequence_placeholder("apply_pagination")


async def build_project_subscription_list_response(
    page: SequencePage[ProjectSubscriptionItemResponse],
) -> ListProjectSubscriptionsResponse:
    """secret 値を含めずに Project subscription 一覧レスポンスを組み立てる。"""
    return _sequence_placeholder("build_project_subscription_list_response")
