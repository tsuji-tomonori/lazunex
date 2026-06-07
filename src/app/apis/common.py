from enum import StrEnum
from typing import NoReturn

from fastapi import HTTPException, status

from app.apis.api_access_requests.common import AccessRequestDerivedState, AuthMode
from app.apis.apis.common import (
    ApiDerivedState,
    ApiDocumentSourceFilename,
    ApiDocumentType,
    ApiDocumentVersionLabel,
    ApiLifecycleReason,
    ApiVisibility,
    ReviewerRole,
    ScopeAttachmentMode,
    ScopeConfigObserved,
)
from app.apis.base import ApiBaseModel, sample_value
from app.apis.projects.common import (
    ProjectCognitoClientType,
    ProjectCognitoClientUrlType,
    ProjectDerivedState,
    QuotaPeriod,
    SubscriptionDerivedState,
    TokenValidityUnit,
)
from app.apis.responses import (
    COMMON_ERROR_SAMPLE,
    ERROR_RESPONSES,
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    PageQuery,
    ValidationErrorDetail,
    empty_error_details,
    error_responses,
    not_implemented,
    success_response,
)
from app.apis.types import (
    AccessTokenValidity,
    ApiCode,
    ApiGatewayId,
    ApiKeyLast4,
    AwsAccountId,
    AwsRegion,
    DepartmentCode,
    DescriptionText,
    DisplayName,
    EmailLikeText,
    IdTokenValidity,
    NonNegativeCount,
    PageToken,
    PrincipalId,
    ProjectCode,
    RefreshTokenValidity,
    ResourceId,
    ResourceServerIdentifier,
    RetryGracePeriodSeconds,
    RowVersion,
    ScopeFullName,
    ScopeName,
    SearchKeyword,
    SecretLast4,
    SecretValue,
    Sha256Hash,
    StageName,
    Timestamp,
    UrlText,
)


class IdentityGroup(StrEnum):
    """CallerIdentity.groups に含まれる認可グループです。"""

    # Lazunex Hub 全体の管理者です。
    HUB_ADMIN = "hub-admin"


def raise_missing_runtime_dependency(function_name: str) -> NoReturn:
    """Sequence function に runtime dependency が注入されていない場合の 500 を返す。"""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{function_name} requires runtime dependencies.",
    )


__all__ = [
    "COMMON_ERROR_SAMPLE",
    "ERROR_RESPONSES",
    "AccessRequestDerivedState",
    "AccessTokenValidity",
    "ApiBaseModel",
    "ApiCode",
    "ApiDerivedState",
    "ApiDocumentSourceFilename",
    "ApiDocumentType",
    "ApiDocumentVersionLabel",
    "ApiGatewayId",
    "ApiKeyLast4",
    "ApiLifecycleReason",
    "ApiVisibility",
    "AuthMode",
    "AwsAccountId",
    "AwsRegion",
    "DepartmentCode",
    "DescriptionText",
    "DisplayName",
    "EmailLikeText",
    "ErrorBody",
    "ErrorDetail",
    "ErrorResponse",
    "IdTokenValidity",
    "IdentityGroup",
    "NonNegativeCount",
    "PageQuery",
    "PageToken",
    "PrincipalId",
    "ProjectCode",
    "ProjectCognitoClientType",
    "ProjectCognitoClientUrlType",
    "ProjectDerivedState",
    "QuotaPeriod",
    "RefreshTokenValidity",
    "ResourceId",
    "ResourceServerIdentifier",
    "RetryGracePeriodSeconds",
    "ReviewerRole",
    "RowVersion",
    "ScopeAttachmentMode",
    "ScopeConfigObserved",
    "ScopeFullName",
    "ScopeName",
    "SearchKeyword",
    "SecretLast4",
    "SecretValue",
    "Sha256Hash",
    "StageName",
    "SubscriptionDerivedState",
    "Timestamp",
    "TokenValidityUnit",
    "UrlText",
    "ValidationErrorDetail",
    "empty_error_details",
    "error_responses",
    "not_implemented",
    "raise_missing_runtime_dependency",
    "sample_value",
    "success_response",
]
