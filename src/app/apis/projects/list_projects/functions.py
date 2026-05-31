from __future__ import annotations

from typing import NoReturn

from app.apis.projects.list_projects.schemas import (
    ListProjectsQuery,
    ListProjectsResponse,
    ProjectListItemResponse,
)
from app.apis.sequence_types import CallerIdentity, SequencePage


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def validate_project_list_query(query: ListProjectsQuery) -> ListProjectsQuery:
    """Project 一覧取得条件を検証する。"""
    return _sequence_placeholder("validate_project_list_query")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def has_project_list_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が Project 一覧を参照できるかを判定する。"""
    return _sequence_placeholder("has_project_list_permission")


async def get_viewable_projects(
    query: ListProjectsQuery,
    caller: CallerIdentity,
) -> SequencePage[ProjectListItemResponse]:
    """呼び出し元が参照可能な Project を検索する。"""
    return _sequence_placeholder("get_viewable_projects")


async def apply_pagination(
    page: SequencePage[ProjectListItemResponse],
    query: ListProjectsQuery,
) -> SequencePage[ProjectListItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    return _sequence_placeholder("apply_pagination")


async def build_project_list_response(
    page: SequencePage[ProjectListItemResponse],
) -> ListProjectsResponse:
    """Project 一覧レスポンスを組み立てる。"""
    return _sequence_placeholder("build_project_list_response")
