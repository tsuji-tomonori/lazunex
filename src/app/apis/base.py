from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiBaseModel(BaseModel):
    """APIレスポンスでcamelCaseのJSONキーを生成する共通Pydanticモデルです。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


def sample_value(sample: BaseModel) -> dict[str, Any]:
    return sample.model_dump(by_alias=True, mode="json")
