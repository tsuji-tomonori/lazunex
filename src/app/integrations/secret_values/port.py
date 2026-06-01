from __future__ import annotations

from typing import Protocol

from app.integrations.secret_values.schemas import GetHashPepperInput, HashPepperSecret


class SecretValuesPort(Protocol):
    async def get_hash_pepper(self, request: GetHashPepperInput) -> HashPepperSecret: ...
