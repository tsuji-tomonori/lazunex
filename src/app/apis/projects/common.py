from collections.abc import Sequence
from enum import StrEnum


class ProjectDerivedState(StrEnum):
    """プロジェクトの現在状態を表す列挙値です。"""

    # プロジェクトが利用可能な状態です。
    ACTIVE = "ACTIVE"


class SubscriptionDerivedState(StrEnum):
    """API利用権の現在状態を表す列挙値です。"""

    # 承認済みのAPI利用権が有効な状態です。
    ACTIVE = "ACTIVE"


class ProjectCognitoClientType(StrEnum):
    """Project に紐づく Cognito app client 種別です。"""

    # PKCE を利用する public client です。
    PUBLIC_PKCE = "PUBLIC_PKCE"
    # 旧データ互換の public client 種別です。
    PUBLIC = "PUBLIC"
    # client credentials を利用する confidential client です。
    CONFIDENTIAL_CLIENT_CREDENTIALS = "CONFIDENTIAL_CLIENT_CREDENTIALS"
    # 旧データ互換の confidential client 種別です。
    CONFIDENTIAL = "CONFIDENTIAL"


class ProjectCognitoClientUrlType(StrEnum):
    """Project Cognito app client に紐づく URL 種別です。"""

    # OAuth callback URL です。
    CALLBACK = "CALLBACK"
    # logout URL です。
    LOGOUT = "LOGOUT"


class QuotaPeriod(StrEnum):
    """API Gateway Usage Planのquota集計期間を表す列挙値です。"""

    # quotaを1日単位で集計します。
    DAY = "DAY"
    # quotaを1週間単位で集計します。
    WEEK = "WEEK"
    # quotaを1か月単位で集計します。
    MONTH = "MONTH"


class TokenValidityUnit(StrEnum):
    """Cognito app client token有効期間の単位を表す列挙値です。"""

    # token有効期間を分単位で指定します。
    MINUTES = "minutes"
    # token有効期間を時間単位で指定します。
    HOURS = "hours"
    # token有効期間を日単位で指定します。
    DAYS = "days"


_TOKEN_UNIT_SECONDS = {
    TokenValidityUnit.MINUTES: 60,
    TokenValidityUnit.HOURS: 60 * 60,
    TokenValidityUnit.DAYS: 24 * 60 * 60,
}


def _duration_seconds(value: int, unit: TokenValidityUnit | str) -> int:
    return value * _TOKEN_UNIT_SECONDS[TokenValidityUnit(unit)]


def validate_cognito_url_list(field_name: str, urls: Sequence[str]) -> None:
    if len(urls) > 100:
        raise ValueError(f"{field_name} must contain 100 or fewer URLs")
    if len(set(urls)) != len(urls):
        raise ValueError(f"{field_name} must not contain duplicate URLs")
    too_long = [url for url in urls if len(url) > 1024]
    if too_long:
        raise ValueError(f"{field_name} URLs must be 1024 characters or fewer")


def validate_access_or_id_token_validity(
    field_name: str,
    value: int,
    unit: TokenValidityUnit | str,
) -> None:
    seconds = _duration_seconds(value, unit)
    if not 5 * 60 <= seconds <= 24 * 60 * 60:
        raise ValueError(f"{field_name} must be between 5 minutes and 1 day")


def validate_refresh_token_validity(value: int, unit: TokenValidityUnit | str) -> None:
    seconds = _duration_seconds(value, unit)
    if not 60 * 60 <= seconds <= 10 * 365 * 24 * 60 * 60:
        raise ValueError("refresh_token_validity must be between 60 minutes and 10 years")


def validate_retry_grace_period_seconds(value: int) -> None:
    if value > 60:
        raise ValueError("retry_grace_period_seconds must be 60 seconds or fewer")
