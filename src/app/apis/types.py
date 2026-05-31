from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

ResourceId = UUID
Timestamp = datetime

AccessTokenValidity = Annotated[int, Field(ge=1)]
ApiCode = Annotated[str, Field(min_length=1, max_length=100)]
ApiGatewayId = Annotated[str, Field(min_length=1, max_length=128)]
ApiKeyLast4 = Annotated[str, Field(min_length=1, max_length=8)]
AwsAccountId = Annotated[str, Field(min_length=12, max_length=12, pattern=r"^\d{12}$")]
AwsRegion = Annotated[str, Field(min_length=1, max_length=32)]
DepartmentCode = Annotated[str, Field(min_length=1, max_length=64)]
DescriptionText = Annotated[str, Field(min_length=1)]
DisplayName = Annotated[str, Field(min_length=1, max_length=200)]
EmailLikeText = Annotated[str, Field(min_length=1, max_length=320)]
IdTokenValidity = Annotated[int, Field(ge=1)]
NonNegativeCount = Annotated[int, Field(ge=0)]
PageToken = Annotated[str, Field(min_length=1)]
PrincipalId = Annotated[str, Field(min_length=1, max_length=256)]
ProjectCode = Annotated[str, Field(min_length=1, max_length=100)]
RefreshTokenValidity = Annotated[int, Field(ge=1)]
ResourceServerIdentifier = Annotated[str, Field(min_length=1, max_length=256)]
RetryGracePeriodSeconds = Annotated[int, Field(ge=0)]
RowVersion = Annotated[int, Field(ge=1)]
ScopeFullName = Annotated[str, Field(min_length=1, max_length=600)]
ScopeName = Annotated[str, Field(min_length=1, max_length=256)]
SearchKeyword = Annotated[str, Field(min_length=1, max_length=200)]
SecretLast4 = Annotated[str, Field(min_length=1, max_length=8)]
SecretValue = Annotated[str, Field(min_length=1)]
Sha256Hash = Annotated[str, Field(min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")]
StageName = Annotated[str, Field(min_length=1, max_length=128)]
UrlText = Annotated[str, Field(min_length=1)]
