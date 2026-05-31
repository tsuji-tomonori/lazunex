from __future__ import annotations

from typing import NoReturn

from app.apis.apis.list_apis.schemas import (
    ApiListItemResponse,
    ListApisQuery,
    ListApisResponse,
)
from app.apis.sequence_types import CallerIdentity, SequencePage


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def validate_api_list_query(query: ListApisQuery) -> ListApisQuery:
    """API 一覧取得条件を検証する。"""
    return _sequence_placeholder("validate_api_list_query")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def has_api_list_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が API 一覧を参照できるかを判定する。"""
    return _sequence_placeholder("has_api_list_permission")


async def get_viewable_apis(
    query: ListApisQuery,
    caller: CallerIdentity,
) -> SequencePage[ApiListItemResponse]:
    """呼び出し元が参照可能な公開 API を検索する。"""
    return _sequence_placeholder("get_viewable_apis")


async def apply_pagination(
    page: SequencePage[ApiListItemResponse],
    query: ListApisQuery,
) -> SequencePage[ApiListItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    return _sequence_placeholder("apply_pagination")


async def build_api_list_response(page: SequencePage[ApiListItemResponse]) -> ListApisResponse:
    """API 一覧レスポンスを組み立てる。"""
    return _sequence_placeholder("build_api_list_response")
