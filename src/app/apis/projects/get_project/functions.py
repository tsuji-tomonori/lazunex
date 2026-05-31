from __future__ import annotations

from typing import NoReturn

from app.apis.projects.get_project.schemas import GetProjectResponse
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_project_id(project_id: ResourceId) -> ResourceId:
    """Project ID を検証する。"""
    return _sequence_placeholder("validate_project_id")


async def get_project_detail(project_id: ResourceId) -> GetProjectResponse:
    """Project 詳細レスポンスに必要な情報を取得する。"""
    return _sequence_placeholder("get_project_detail")


async def has_project_view_permission(project: GetProjectResponse, caller: CallerIdentity) -> bool:
    """呼び出し元が Project 詳細を参照できるかを判定する。"""
    return _sequence_placeholder("has_project_view_permission")


async def build_project_detail_response(project: GetProjectResponse) -> GetProjectResponse:
    """secret 値を含めずに Project 詳細レスポンスを組み立てる。"""
    return _sequence_placeholder("build_project_detail_response")
