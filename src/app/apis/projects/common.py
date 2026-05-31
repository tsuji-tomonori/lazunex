from enum import StrEnum


class ProjectDerivedState(StrEnum):
    """プロジェクトの現在状態を表す列挙値です。"""

    # プロジェクトが利用可能な状態です。
    ACTIVE = "ACTIVE"


class SubscriptionDerivedState(StrEnum):
    """API利用権の現在状態を表す列挙値です。"""

    # 承認済みのAPI利用権が有効な状態です。
    ACTIVE = "ACTIVE"


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
