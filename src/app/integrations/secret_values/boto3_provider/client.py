from __future__ import annotations

from typing import Any

from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from app.integrations._aws_boto3 import run_boto3_call
from app.integrations.common_errors import map_provider_error
from app.integrations.secret_values.boto3_provider.mapper import map_hash_pepper_secret
from app.integrations.secret_values.schemas import GetHashPepperInput, HashPepperSecret

_PROVIDER_ERRORS = (ClientError, ConnectTimeoutError, ReadTimeoutError, EndpointConnectionError)


class Boto3SecretValuesClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def get_hash_pepper(self, request: GetHashPepperInput) -> HashPepperSecret:
        try:
            response = await run_boto3_call(
                lambda: self._client.get_secret_value(SecretId=request.secret_id)
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_hash_pepper_secret(response)
