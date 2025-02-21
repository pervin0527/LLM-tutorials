import logging

from fastapi import FastAPI
from fastapi import APIRouter

from app.utils.logging import logger
from app.handler.errorhandler import ErrorHandler
from app.utils.execution_time import ExecutionTimeMiddleware

from app.core.api_version import APIVersion, APIVersionManager
from app.router.v1.api import culture_api_router_v1
from app.utils.configs import load_config, save_config

# 로거 설정
logger = logging.getLogger("Culture Backoffice Logger")

def create_app():
    error_handler = ErrorHandler()
    version_manager = APIVersionManager()
    
    cfg = load_config("app/configs/config.yaml")
    base_servers = [
        {"url": "http://0.0.0.0:8000", "description": "로컬 환경 서버"},
        # {"url": cfg["data_server"], "description": "개발 환경 서버"},
    ]
        
    version_manager.add_version(
        APIVersion(
            prefix="/api/v1",
            title="Culture Backoffice API V1",
            version="1.0.0",
            description="Legacy API version with basic features",
            servers=[{**server, "url": f"{server['url']}/api/v1"} for server in base_servers],
            router=culture_api_router_v1,
            error_handler=error_handler
        )
    )

    app = version_manager.create_apps(
        cors_origins=["*"],
        middlewares=[ExecutionTimeMiddleware]
    )

    app.state.cfg = cfg
    logger.info(f"config: {cfg}")

    @app.get("/healths")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()