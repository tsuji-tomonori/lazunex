from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

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
class SequencePage[T]:
    """Sequence step間で受け渡すページング済み一覧です。"""

    items: Sequence[T]
    next_token: PageToken | None


@dataclass(frozen=True)
class IdempotencyRecordRef:
    """冪等性レコードの参照情報です。"""

    idempotency_key: str
    operation_id: ResourceId | None


@dataclass(frozen=True)
class ProvisioningOperationRef:
    """AWS反映を追跡するprovisioning operationの参照情報です。"""

    operation_id: ResourceId


@dataclass(frozen=True)
class EventRef:
    """追記したイベントの参照情報です。"""

    event_id: ResourceId


@dataclass(frozen=True)
class ApiCatalogMetadataRef:
    """API catalog metadataの参照情報です。"""

    api_id: ResourceId
    api_stage_id: ResourceId | None = None


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


@dataclass(frozen=True)
class ProjectResourceRefs:
    """Project作成時に払い出すAWS resource群の参照情報です。"""

    project_id: ResourceId
    api_key_id: ResourceId
    usage_plan_id: ResourceId
    public_client_id: ResourceId
    confidential_client_id: ResourceId


@dataclass(frozen=True)
class SecretHashRefs:
    """保存用にhash化したsecret metadataです。"""

    api_key_last4: SecretLast4
    confidential_client_secret_last4: SecretLast4


@dataclass(frozen=True)
class CognitoAppClientRef:
    """Cognito App Clientの参照情報です。"""

    app_client_id: ApiGatewayId
    allowed_scopes: Sequence[ScopeFullName]


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


@dataclass(frozen=True)
class ApiAccessReviewRef:
    """利用申請レビューの参照情報です。"""

    review_id: ResourceId


@dataclass(frozen=True)
class ApprovedAccessResourceRefs:
    """承認時に保存した利用権関連resourceの参照情報です。"""

    review_id: ResourceId
    subscription_id: ResourceId
    usage_plan_api_stage_id: ResourceId
    client_scope_ids: Sequence[ResourceId]
