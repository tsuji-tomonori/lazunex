from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.secret_values.port import SecretValuesPort
from app.integrations.secret_values.schemas import GetHashPepperInput, HashPepperSecret


@dataclass
class FakeSecretValuesClient(SecretValuesPort):
    pepper: HashPepperSecret = field(
        default_factory=lambda: HashPepperSecret(
            secret_value="local-hash-pepper"  # noqa: S106
        )
    )
    calls: list[object] = field(default_factory=lambda: [])

    async def get_hash_pepper(self, request: GetHashPepperInput) -> HashPepperSecret:
        self.calls.append(request)
        return self.pepper
