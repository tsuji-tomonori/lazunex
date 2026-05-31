from __future__ import annotations

from typing import NoReturn

from app.apis.projects.get_project.schemas import (
    ProjectApiKeyResponse,
    ProjectCognitoClientsResponse,
)
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
    ProjectSubscriptionItemResponse,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


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


async def get_active_subscriptions(
    project: ProjectRef,
    query: ListProjectSubscriptionsQuery,
) -> SequencePage[ProjectSubscriptionItemResponse]:
    """Project の active subscription を検索する。"""
    return _sequence_placeholder("get_active_subscriptions")


async def get_subscription_api_metadata(
    page: SequencePage[ProjectSubscriptionItemResponse],
) -> SequencePage[ProjectSubscriptionItemResponse]:
    """subscription 一覧に必要な API metadata、stage、scope を取得する。"""
    return _sequence_placeholder("get_subscription_api_metadata")


async def get_project_api_key_metadata(project: ProjectRef) -> ProjectApiKeyResponse:
    """Project の API key metadata を取得する。"""
    return _sequence_placeholder("get_project_api_key_metadata")


async def get_project_client_metadata(project: ProjectRef) -> ProjectCognitoClientsResponse:
    """Project の Cognito App Client metadata を取得する。"""
    return _sequence_placeholder("get_project_client_metadata")


async def build_project_subscription_list_response(
    page: SequencePage[ProjectSubscriptionItemResponse],
    api_key: ProjectApiKeyResponse,
    cognito: ProjectCognitoClientsResponse,
) -> ListProjectSubscriptionsResponse:
    """secret 値を含めずに Project subscription 一覧レスポンスを組み立てる。"""
    return _sequence_placeholder("build_project_subscription_list_response")
