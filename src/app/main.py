from fastapi import FastAPI

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

    return app


app = create_app()
