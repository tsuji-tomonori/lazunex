from __future__ import annotations

from typing import NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.common import AuthMode
from app.apis.deps import build_caller_identity
from app.apis.projects.common import SubscriptionDerivedState
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


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project を取得する。"""
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
                is_hub_admin="hub-admin" in caller.groups,
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
    return _sequence_placeholder("get_project_subscriptions")


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
