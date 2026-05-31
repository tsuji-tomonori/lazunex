from enum import StrEnum


class AccessRequestDerivedState(StrEnum):
    """API利用申請の現在状態を表す列挙値です。"""

    # API利用申請が審査待ちの状態です。
    PENDING = "PENDING"
    # API利用申請が承認された状態です。
    APPROVED = "APPROVED"
    # API利用申請が却下された状態です。
    REJECTED = "REJECTED"


class AuthMode(StrEnum):
    """API利用時に許可する認証方式を表す列挙値です。"""

    # PKCEを利用するpublic client向けの認証方式です。
    PUBLIC_PKCE = "PUBLIC_PKCE"
    # client credentialsを利用するconfidential client向けの認証方式です。
    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"
    # public clientとconfidential clientの両方を許可する認証方式です。
    BOTH = "BOTH"
