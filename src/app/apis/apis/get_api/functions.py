from __future__ import annotations

from typing import NoReturn

from app.apis.apis.get_api.schemas import (
    ApiDetailStageResponse,
    ApiReviewerResponse,
    ApiScopeResponse,
    GetApiResponse,
)
from app.apis.sequence_types import (
    ApiCatalogMetadataRef,
    CallerIdentity,
    OpenApiMetadataRef,
)
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def validate_api_id(api_id: ResourceId) -> ResourceId:
    """API ID を検証する。"""
    return _sequence_placeholder("validate_api_id")


async def get_api_catalog_metadata(api_id: ResourceId) -> ApiCatalogMetadataRef:
    """対象 API の catalog metadata を取得する。"""
    return _sequence_placeholder("get_api_catalog_metadata")


async def is_viewable_api(
    api: ApiCatalogMetadataRef,
    caller: CallerIdentity,
) -> bool:
    """対象 API が呼び出し元から参照可能かを判定する。"""
    return _sequence_placeholder("is_viewable_api")


async def get_api_gateway_stage(api: ApiCatalogMetadataRef) -> ApiDetailStageResponse:
    """API Gateway REST API stage 情報を取得する。"""
    return _sequence_placeholder("get_api_gateway_stage")


async def get_api_scope(api: ApiCatalogMetadataRef) -> ApiScopeResponse:
    """API 実行に必要な Cognito custom scope を取得する。"""
    return _sequence_placeholder("get_api_scope")


async def get_api_reviewer(api: ApiCatalogMetadataRef) -> list[ApiReviewerResponse]:
    """対象 API の reviewer 情報を取得する。"""
    return _sequence_placeholder("get_api_reviewer")


async def get_openapi_metadata(api: ApiCatalogMetadataRef) -> OpenApiMetadataRef:
    """OpenAPI metadata と利用条件を取得する。"""
    return _sequence_placeholder("get_openapi_metadata")


async def build_api_detail_response(
    api: ApiCatalogMetadataRef,
    stage: ApiDetailStageResponse,
    scope: ApiScopeResponse,
    reviewers: list[ApiReviewerResponse],
    openapi_metadata: OpenApiMetadataRef,
) -> GetApiResponse:
    """API 詳細レスポンスを組み立てる。"""
    return _sequence_placeholder("build_api_detail_response")
