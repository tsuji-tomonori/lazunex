from fastapi import FastAPI

from app.apis.api_access_requests.approve_api_access_request.router import (
    router as approve_api_access_request_router,
)
from app.apis.api_access_requests.reject_api_access_request.router import (
    router as reject_api_access_request_router,
)
from app.apis.apis.get_api.router import router as get_api_router
from app.apis.apis.list_apis.router import router as list_apis_router
from app.apis.apis.publish_api.router import router as publish_api_router
from app.apis.projects.create_api_access_request.router import (
    router as create_api_access_request_router,
)
from app.apis.projects.create_project.router import router as create_project_router
from app.apis.projects.get_project.router import router as get_project_router
from app.apis.projects.list_project_api_access_requests.router import (
    router as list_project_api_access_requests_router,
)
from app.apis.projects.list_project_subscriptions.router import (
    router as list_project_subscriptions_router,
)
from app.apis.projects.list_projects.router import router as list_projects_router
from app.apis.projects.update_project_public_client.router import (
    router as update_project_public_client_router,
)
from app.core.config import settings


async def health() -> dict[str, str]:
    return {"status": "ok"}


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    app.add_api_route("/health", health, methods=["GET"], tags=["system"])
    app.include_router(list_apis_router)
    app.include_router(publish_api_router)
    app.include_router(get_api_router)
    app.include_router(list_projects_router)
    app.include_router(create_project_router)
    app.include_router(get_project_router)
    app.include_router(list_project_subscriptions_router)
    app.include_router(update_project_public_client_router)
    app.include_router(list_project_api_access_requests_router)
    app.include_router(create_api_access_request_router)
    app.include_router(approve_api_access_request_router)
    app.include_router(reject_api_access_request_router)

    return app


app = create_app()
