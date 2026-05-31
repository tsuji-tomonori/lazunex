from enum import StrEnum


class ApiVisibility(StrEnum):
    """APIカタログの公開範囲を表す列挙値です。"""

    # 社内利用者に公開されるAPIです。
    INTERNAL = "INTERNAL"
    # 限定された利用者だけに公開されるAPIです。
    RESTRICTED = "RESTRICTED"


class ApiDerivedState(StrEnum):
    """APIカタログの現在状態を表す列挙値です。"""

    # APIカタログで公開済みの状態です。
    PUBLISHED = "PUBLISHED"


class ReviewerRole(StrEnum):
    """API利用申請を審査する担当者の役割を表す列挙値です。"""

    # 主担当としてAPI利用申請を審査する役割です。
    PRIMARY = "PRIMARY"
    # 主担当の代替としてAPI利用申請を審査する役割です。
    BACKUP = "BACKUP"
    # 管理者としてAPI利用申請を審査できる役割です。
    ADMIN = "ADMIN"


class ScopeConfigObserved(StrEnum):
    """API Gateway stageで検出したCognito scope設定状態を表す列挙値です。"""

    # API Gateway methodに必要なCognito scope設定が確認済みです。
    VERIFIED = "VERIFIED"
    # API Gateway methodに必要なCognito scope設定がありません。
    NOT_CONFIGURED = "NOT_CONFIGURED"
    # API Gateway methodのCognito scope設定を確認できていない状態です。
    UNKNOWN = "UNKNOWN"


class ScopeAttachmentMode(StrEnum):
    """API Gateway methodへのscope反映方法を表す列挙値です。"""

    # scope設定を検証するだけでAPI Gateway methodには反映しません。
    VERIFY_ONLY = "VERIFY_ONLY"
    # API Gatewayの全methodへscope設定を反映します。
    PATCH_ALL_METHODS = "PATCH_ALL_METHODS"
