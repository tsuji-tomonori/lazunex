from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.apis.types import (
    ApiGatewayId,
    PageToken,
    PrincipalId,
    ResourceId,
    ScopeFullName,
    SecretLast4,
    SecretValue,
    Sha256Hash,
    UrlText,
)


@dataclass(frozen=True)
class CallerIdentity:
    """Sequence stepで参照する呼び出し元認証情報です。"""

    principal_id: PrincipalId
    groups: Sequence[str]
    scopes: Sequence[ScopeFullName]


@dataclass(frozen=True)
class RequestContext:
    """Sequence stepで監査・イベント・冪等性に使うリクエスト文脈です。"""

    correlation_id: str
    source_ip: str
    user_agent: str
    actor_type: str = "USER"


@dataclass(frozen=True)
class SequencePage[T]:
    """Sequence step間で受け渡すページング済み一覧です。"""

    items: Sequence[T]
    next_token: PageToken | None


@dataclass(frozen=True)
class IdempotencyRecordRef:
    """冪等性レコードの参照情報です。"""

    idempotency_key: str
    operation_id: ResourceId | None
    request_hash: str | None = None
    response_payload: dict[str, Any] | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class ProvisioningOperationRef:
    """AWS反映を追跡するprovisioning operationの参照情報です。"""

    operation_id: ResourceId
    target_id: ResourceId | None = None


@dataclass(frozen=True)
class EventRef:
    """追記したイベントの参照情報です。"""

    event_id: ResourceId


@dataclass(frozen=True)
class ApiCatalogMetadataRef:
    """API catalog metadataの参照情報です。"""

    api_id: ResourceId
    api_stage_id: ResourceId | None = None
    api_scope_id: ResourceId | None = None
    api_reviewer_ids: Sequence[ResourceId] = ()


@dataclass(frozen=True)
class ApiScopeRef:
    """API実行認可scopeの参照情報です。"""

    scope_full_name: ScopeFullName


@dataclass(frozen=True)
class ApiReviewerRefs:
    """API reviewerの参照情報です。"""

    reviewer_principal_ids: Sequence[PrincipalId]


@dataclass(frozen=True)
class OpenApiMetadataRef:
    """OpenAPI metadataの参照情報です。"""

    s3_uri: UrlText
    sha256: Sha256Hash


@dataclass(frozen=True)
class ProjectRef:
    """Projectの参照情報です。"""

    project_id: ResourceId
    owner_principal_id: PrincipalId | None = None
    caller_project_role: str | None = None


@dataclass(frozen=True)
class ProjectResourceRefs:
    """Project作成時に払い出すAWS resource群の参照情報です。"""

    project_id: ResourceId
    api_key_id: ResourceId
    usage_plan_id: ResourceId
    public_client_id: ResourceId
    confidential_client_id: ResourceId
    project_code: str = ""
    project_member_id: ResourceId | None = None
    project_api_key_id: ResourceId | None = None
    project_usage_plan_id: ResourceId | None = None
    project_usage_plan_key_id: ResourceId | None = None
    public_project_cognito_client_id: ResourceId | None = None
    confidential_project_cognito_client_id: ResourceId | None = None
    apigw_api_key_id: str = ""
    apigw_usage_plan_id: str = ""
    public_app_client_id: str = ""
    confidential_app_client_id: str = ""


@dataclass(frozen=True)
class SecretHashRefs:
    """保存用にhash化したsecret metadataです。"""

    api_key_last4: SecretLast4
    confidential_client_secret_last4: SecretLast4
    api_key_hash: Sha256Hash | None = None
    confidential_client_secret_hash: Sha256Hash | None = None
    hash_key_version: str | None = None


@dataclass(frozen=True)
class CognitoAppClientRef:
    """Cognito App Clientの参照情報です。"""

    app_client_id: ApiGatewayId
    allowed_scopes: Sequence[ScopeFullName]
    user_pool_id: str | None = None
    callback_urls: Sequence[UrlText] = ()
    logout_urls: Sequence[UrlText] = ()
    access_token_validity: int | None = None
    access_token_unit: str | None = None
    id_token_validity: int | None = None
    id_token_unit: str | None = None
    refresh_token_validity: int | None = None
    refresh_token_unit: str | None = None
    refresh_token_rotation_enabled: bool | None = None
    retry_grace_period_seconds: int | None = None
    allowed_oauth_flows: Sequence[str] = ()
    supported_identity_providers: Sequence[str] = ()


@dataclass(frozen=True)
class CognitoConfidentialClientRef:
    """Cognito confidential App Clientと初回secretの参照情報です。"""

    app_client_id: ApiGatewayId
    client_secret: SecretValue


@dataclass(frozen=True)
class UsagePlanApiStageRef:
    """Usage Planに追加するAPI stageの参照情報です。"""

    usage_plan_api_stage_id: ResourceId


@dataclass(frozen=True)
class ApiAccessRequestRef:
    """利用申請の参照情報です。"""

    access_request_id: ResourceId
    project_id: ResourceId
    api_id: ResourceId
    api_stage_id: ResourceId
    requested_auth_mode: str | None = None
    requested_reason: str | None = None
    requested_by: PrincipalId | None = None
    derived_state: str | None = None
    scope_full_name: ScopeFullName | None = None
    api_scope_id: ResourceId | None = None
    apigw_rest_api_id: ApiGatewayId | None = None
    apigw_stage_name: str | None = None


@dataclass(frozen=True)
class ApiAccessReviewRef:
    """利用申請レビューの参照情報です。"""

    review_id: ResourceId
    reviewed_at: object | None = None


@dataclass(frozen=True)
class ApprovedAccessResourceRefs:
    """承認時に保存した利用権関連resourceの参照情報です。"""

    review_id: ResourceId
    subscription_id: ResourceId
    usage_plan_api_stage_id: ResourceId
    client_scope_ids: Sequence[ResourceId]
