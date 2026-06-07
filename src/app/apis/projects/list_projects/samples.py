from uuid import UUID

from app.apis.projects.common import ProjectDerivedState
from app.apis.projects.list_projects.schemas import (
    ErrorResource,
    ListProjectsResponse,
    ProjectListItemResponse,
)
from app.apis.sample_cases import request_sample, status_samples

LIST_PROJECTS_RESPONSE_SAMPLE = ListProjectsResponse(
    items=[
        ProjectListItemResponse(
            project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
            project_code="payment-frontend",
            name="Payment Frontend",
            description="決済画面プロジェクト",
            owner_principal_id="user-12345",
            department_code="FIN",
            derived_state=ProjectDerivedState.ACTIVE,
            subscription_count=3,
        )
    ],
    next_token=None,
)
LIST_PROJECTS_STATUS_SAMPLES = status_samples(
    request=request_sample(
        query={"limit": 50, "derivedState": "ACTIVE", "keyword": "payment"},
        headers={"X-Principal-Id": "user-12345"},
    ),
    success_status=200,
    success_response=LIST_PROJECTS_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元にProject一覧を参照する権限がない場合。",
        422: "queryがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
    },
)
