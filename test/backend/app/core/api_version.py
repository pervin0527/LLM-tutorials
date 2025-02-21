from dataclasses import dataclass
from typing import List, Optional, Dict, Callable
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from h11 import LocalProtocolError

from app.handler.errorhandler import ErrorHandler, InternalServerError, ErrorResponse

@dataclass
class APIVersion:
    prefix: str  # API 경로의 접두사
    title: str  # API의 제목
    version: str  # API의 버전 정보
    description: str  # API에 대한 설명
    servers: List[dict]  # API가 배포될 서버 목록
    router: object  # FastAPI 라우터 객체
    error_handler: ErrorHandler  # 에러 처리 핸들러
    enabled: bool = True  # API 활성화 여부, 기본값은 True

class APIVersionManager:
    def __init__(self):
        self.versions: List[APIVersion] = []
        
    def add_version(self, version: APIVersion):
        self.versions.append(version)
        
    def _add_exception_handlers(self, app: FastAPI, error_handler: ErrorHandler):
        internal_error_handler = InternalServerError(error_handler)

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            detail = exc.detail if isinstance(exc.detail, dict) else {"error": "Error", "message": str(exc.detail)}
            exc_value = str(exc)
            alert = detail.get("alert", False)
            
            if exc.status_code == 400:
                detail["status"] = exc.status_code
                detail["code"] = exc.status_code
                await error_handler.handle_error(exc, "400: http_exception_handler", exc_value, request, alert)
            elif exc.status_code == 401:
                if 'autho' in detail.get("error", "").lower():
                    detail["status"] = 401
                    detail["code"] = 401
                else:
                    detail["status"] = 402
                    detail["code"] = 402
            elif exc.status_code == 403:
                detail["status"] = 403
                detail["code"] = 403
            elif exc.status_code == 404:
                detail["status"] = exc.status_code
                detail["code"] = exc.status_code
                await error_handler.handle_error(exc, "404: http_exception_handler", exc_value, request, alert)
            else:
                detail["status"] = exc.status_code
                detail["code"] = exc.status_code
                await error_handler.handle_error(exc, "500: http_exception_handler", exc_value, request, alert)
                
            return ErrorResponse.create_error_response(
                request=request,
                status_code=exc.status_code,
                error=detail.get("error", "Error"),
                message=detail.get("message", str(exc)),
                additional_info=detail
            )

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            exc_value = str(exc)
            await error_handler.handle_error(exc, "422: validation_exception_handler", exc_value, request, True)

            validation_errors = exc.errors()
            messages = " ".join([f"{'.'.join(map(str, error['loc'][1:]))}: {error['msg']}" for error in validation_errors])

            return ErrorResponse.create_error_response(
                request=request,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error="Request Validation Error",
                message=messages
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            if isinstance(exc, LocalProtocolError):
                return None
                
            try:
                return await internal_error_handler.handle_known_error(request, exc)
            except Exception as unknown_exc:
                return await internal_error_handler.handle_unknown_error(request, unknown_exc)

    def create_apps(self, cors_origins: List[str], middlewares: List = None, lifespan: Callable = None):
        # Main app에만 lifespan 함수를 적용합니다.
        main_app = FastAPI(lifespan=lifespan)
        
        # CORS 설정
        main_app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 각 버전별 앱 생성 및 마운트
        for version in self.versions:
            if not version.enabled:
                continue
                
            # 서브 앱은 별도의 lifespan을 지정하지 않습니다.
            version_app = FastAPI(
                title=version.title,
                version=version.version,
                description=version.description,
                servers=version.servers
            )
            version_app.state = main_app.state
            
            # 미들웨어 추가
            if middlewares:
                for middleware in middlewares:
                    version_app.add_middleware(middleware)
            
            # 라우터 추가
            version_app.include_router(version.router)
            
            # 예외 핸들러 추가
            self._add_exception_handlers(version_app, version.error_handler)
            
            # 메인 앱에 마운트
            main_app.mount(version.prefix, version_app)
            
        return main_app
