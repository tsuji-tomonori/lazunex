from typing import Any, TypedDict, cast

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

SAMPLE_PATH_VALUES = {
    "accessRequestId": "e540d3e8-0000-0000-0000-000000000001",
    "apiId": "7b0d4a98-0000-0000-0000-000000000001",
    "projectId": "cb62b5f6-0000-0000-0000-000000000001",
}


class ApiBaseModel(BaseModel):
    """APIレスポンスでcamelCaseのJSONキーを生成する共通Pydanticモデルです。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ApiStatusSample(TypedDict):
    """OpenAPI operation のHTTP statusごとのrequest/response sampleです。"""

    request: dict[str, Any]
    response: dict[str, Any]


def sample_value(sample: BaseModel) -> dict[str, Any]:
    return sample.model_dump(by_alias=True, mode="json")


def find_sample_path_value(value: object, name: str) -> str | None:
    if isinstance(value, dict):
        value_object = cast(dict[object, object], value)
        if name in value_object:
            return str(value_object[name])
        for child in value_object.values():
            if found := find_sample_path_value(child, name):
                return found
    if isinstance(value, list):
        value_list = cast(list[object], value)
        for child in value_list:
            if found := find_sample_path_value(child, name):
                return found
    return None


def sample_path_value(sample: BaseModel, name: str) -> str:
    if found := find_sample_path_value(sample_value(sample), name):
        return found
    return SAMPLE_PATH_VALUES.get(name, f"<{name}>")
