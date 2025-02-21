import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging import logger

class ExecutionTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        execution_time = time.time() - start_time
        logger.info(f"API 요청 처리 시간: {request.url.path} - {execution_time:.5f}초")
        return response