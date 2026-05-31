from app.apis.common import ProjectDerivedState
from app.apis.projects.list_projects.schemas import ListProjectsResponse, ProjectListItemResponse

LIST_PROJECTS_RESPONSE_SAMPLE = ListProjectsResponse(
    items=[
        ProjectListItemResponse(
            project_id="cb62b5f6-0000-0000-0000-000000000001",
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
