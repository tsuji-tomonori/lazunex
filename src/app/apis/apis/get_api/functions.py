from __future__ import annotations

from typing import NoReturn

from app.apis.apis.get_api.schemas import GetApiResponse
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_api_id(api_id: ResourceId) -> ResourceId:
    """API ID を検証する。"""
    return _sequence_placeholder("validate_api_id")


async def get_api_detail(api_id: ResourceId) -> GetApiResponse:
    """API 詳細レスポンスに必要な情報を取得する。"""
    return _sequence_placeholder("get_api_detail")


async def is_viewable_api(
    api: GetApiResponse,
    caller: CallerIdentity,
) -> bool:
    """対象 API が呼び出し元から参照可能かを判定する。"""
    return _sequence_placeholder("is_viewable_api")


async def build_api_detail_response(api: GetApiResponse) -> GetApiResponse:
    """API 詳細レスポンスを組み立てる。"""
    return _sequence_placeholder("build_api_detail_response")
