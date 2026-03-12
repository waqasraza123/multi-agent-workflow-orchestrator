from fastapi import FastAPI

from multi_agent_platform.api.routes.health import router as health_router
from multi_agent_platform.api.routes.runs import router as runs_router


def create_app() -> FastAPI:
    application = FastAPI(title="Multi-Agent Platform", version="0.0.0")
    application.include_router(health_router)
    application.include_router(runs_router)
    return application
