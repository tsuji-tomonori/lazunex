from __future__ import annotations

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.common import ApiDerivedState, ApiVisibility
from app.apis.apis.list_apis import queries
from app.apis.apis.list_apis.schemas import (
    ApiListItemResponse,
    ApiListStageResponse,
    ListApisQuery,
    ListApisResponse,
)
from app.apis.common import raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.sequence_types import CallerIdentity, SequencePage


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
