from __future__ import annotations

from typing import NoReturn

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
) -> SequencePage[ProjectSubscriptionItemResponse]:
    """Project の active subscription を検索する。"""
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
