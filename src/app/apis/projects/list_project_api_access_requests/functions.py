from __future__ import annotations

from typing import NoReturn

from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsQuery,
    ListProjectApiAccessRequestsResponse,
    ProjectApiAccessRequestItemResponse,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def validate_project_access_request_list_query(
    query: ListProjectApiAccessRequestsQuery,
) -> ListProjectApiAccessRequestsQuery:
    """Project 利用申請一覧取得条件を検証する。"""
    return _sequence_placeholder("validate_project_access_request_list_query")


async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project を取得する。"""
    return _sequence_placeholder("get_project")


async def has_project_access_request_view_permission(
    project: ProjectRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が Project 内の利用申請履歴を参照できるかを判定する。"""
    return _sequence_placeholder("has_project_access_request_view_permission")


async def get_project_access_requests(
    project: ProjectRef,
    query: ListProjectApiAccessRequestsQuery,
    caller: CallerIdentity,
) -> SequencePage[ProjectApiAccessRequestItemResponse]:
    """Project に紐づく access request を検索する。"""
    return _sequence_placeholder("get_project_access_requests")


async def apply_pagination(
    page: SequencePage[ProjectApiAccessRequestItemResponse],
    query: ListProjectApiAccessRequestsQuery,
) -> SequencePage[ProjectApiAccessRequestItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    return _sequence_placeholder("apply_pagination")


async def build_project_access_request_list_response(
    page: SequencePage[ProjectApiAccessRequestItemResponse],
) -> ListProjectApiAccessRequestsResponse:
    """Project 利用申請一覧レスポンスを組み立てる。"""
    return _sequence_placeholder("build_project_access_request_list_response")
