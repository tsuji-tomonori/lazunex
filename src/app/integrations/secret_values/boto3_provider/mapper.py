from __future__ import annotations

from typing import Any

from app.integrations.secret_values.schemas import HashPepperSecret


def map_hash_pepper_secret(response: dict[str, Any]) -> HashPepperSecret:
    return HashPepperSecret(secret_value=str(response["SecretString"]))
