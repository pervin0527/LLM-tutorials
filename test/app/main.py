import logging

from fastapi import FastAPI
from fastapi import APIRouter

from src.rag.retriever.vector_retriever import VectorStore

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
    
    base_servers = [
        {"url": "http://localhost:8881", "description": "로컬 환경 서버"},
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
    
    # app.state에 vector_store와 설정값 저장
    cfg = load_config("app/configs/config.yaml")
    app.state.cfg = cfg
    logger.info(f"config: {cfg}")

    app.state.vector_store = VectorStore(cfg)
    logger.info("VectorStore 인스턴스가 app.state에 설정되었습니다.")

    @app.on_event("startup")
    async def startup_event():
        logger.info("Vector DB 초기화.")
        try:
            if cfg['index_load_path'] is None:
                logger.info(f"⚙️  Index Type: {cfg['index_type']}")
                app.state.vector_store.create_vector_db(cfg['index_type'])
                logger.info("✅ Vector DB Created")
                # 생성 후 상태 재확인
                logger.info(f"Vector store after creation: {app.state.vector_store}")

                app.state.vector_store.save_vector_db(app.state.vector_store.vector_db)
            else:
                app.state.vector_store.load_vector_db(cfg['index_load_path'], cfg['model_name'])
                
        except Exception as e:
            logger.error(f"❌ Vector DB Initialization Error: {str(e)}")

    @app.get("/healths")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()