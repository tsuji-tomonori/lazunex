from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.common import ApiDerivedState, ApiVisibility, ReviewerRole, ScopeConfigObserved
from app.apis.apis.get_api import queries
from app.apis.apis.get_api.schemas import (
    ApiDetailStageResponse,
    ApiReviewerResponse,
    ApiScopeResponse,
    GetApiResponse,
)
from app.apis.deps import build_caller_identity
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def get_api_detail(
    api_id: ResourceId,
    session: AsyncSession | None = None,
) -> GetApiResponse:
    """API 詳細レスポンスに必要な情報を取得する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_id=api_id),
        )
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API not found")
        first = rows[0]
        return GetApiResponse(
            api_id=first.api_id,
            api_code=first.api_code,
            name=first.name,
            description=first.description,
            provider_name=first.provider_name,
            provider_contact=first.provider_contact,
            owner_principal_id=first.owner_principal_id,
            visibility=ApiVisibility(first.visibility),
            derived_state=ApiDerivedState.PUBLISHED,
            stage=ApiDetailStageResponse(
                api_stage_id=first.api_stage_id,
                aws_account_id=first.aws_account_id,
                aws_region=first.aws_region,
                rest_api_id=first.apigw_rest_api_id,
                stage_name=first.apigw_stage_name,
                invoke_url=first.invoke_url,
                custom_domain_url=first.custom_domain_url,
                api_key_required_observed=first.api_key_required_observed,
                scope_config_observed=_scope_config_observed(first.scope_config_observed),
            ),
            scope=ApiScopeResponse(
                scope_name=first.scope_name,
                scope_full_name=first.scope_full_name,
            ),
            reviewers=[
                ApiReviewerResponse(
                    reviewer_principal_id=row.reviewer_principal_id,
                    reviewer_role=ReviewerRole(row.reviewer_role),
                )
                for row in rows
            ],
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="get_api_detail requires session.",
    )


async def is_viewable_api(
    api: GetApiResponse,
    caller: CallerIdentity,
) -> bool:
    """対象 API が呼び出し元から参照可能かを判定する。"""
    if api.visibility == ApiVisibility.INTERNAL:
        return True
    return (
        "hub-admin" in caller.groups
        or api.owner_principal_id == caller.principal_id
        or any(reviewer.reviewer_principal_id == caller.principal_id for reviewer in api.reviewers)
    )


async def build_api_detail_response(api: GetApiResponse) -> GetApiResponse:
    """API 詳細レスポンスを組み立てる。"""
    return GetApiResponse(
        api_id=api.api_id,
        api_code=api.api_code,
        name=api.name,
        description=api.description,
        provider_name=api.provider_name,
        provider_contact=api.provider_contact,
        owner_principal_id=api.owner_principal_id,
        visibility=api.visibility,
        derived_state=api.derived_state,
        stage=ApiDetailStageResponse(
            api_stage_id=api.stage.api_stage_id,
            aws_account_id=api.stage.aws_account_id,
            aws_region=api.stage.aws_region,
            rest_api_id=api.stage.rest_api_id,
            stage_name=api.stage.stage_name,
            invoke_url=api.stage.invoke_url,
            custom_domain_url=api.stage.custom_domain_url,
            api_key_required_observed=api.stage.api_key_required_observed,
            scope_config_observed=api.stage.scope_config_observed,
        ),
        scope=ApiScopeResponse(
            scope_name=api.scope.scope_name,
            scope_full_name=api.scope.scope_full_name,
        ),
        reviewers=[
            ApiReviewerResponse(
                reviewer_principal_id=reviewer.reviewer_principal_id,
                reviewer_role=reviewer.reviewer_role,
            )
            for reviewer in api.reviewers
        ],
    )


def _scope_config_observed(value: str) -> ScopeConfigObserved:
    if value in {"VERIFY_ONLY", "PATCH_ALL_METHODS"}:
        return ScopeConfigObserved.VERIFIED
    return ScopeConfigObserved(value)
