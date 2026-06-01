from __future__ import annotations

from dataclasses import dataclass

from app.apis.types import SecretValue


@dataclass(frozen=True)
class GetHashPepperInput:
    secret_id: str


@dataclass(frozen=True)
class HashPepperSecret:
    secret_value: SecretValue
