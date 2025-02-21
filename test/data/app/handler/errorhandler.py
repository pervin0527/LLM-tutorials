import os
import json
import httpx
import traceback

from typing import Dict
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse

from app.utils.logging import logger
from src.utils.config_utils import load_config

# ENVIRONMENT = os.getenv("PYTHON_PROFILES_ACTIVE", "dev")
# slack_token = os.getenv('SLACK_TOKEN')
# slack_channel = os.getenv('SLACK_CHANNEL')
# slack_project = os.getenv('SLACK_PROJECT')

cfg = load_config("app/configs/config.yaml")
environment = cfg['environment']
slack_token = cfg['slack_token']
slack_channel = f"{cfg['slack_channel']}_{environment}"
slack_project = f"{cfg['slack_project']}-{environment}"

class SlackNotifier:
    def __init__(self, token: str, channel: str, project: str):
        self.token = token
        self.channel = channel
        self.project = project
        self.base_url = "https://slack.com/api"
        self.post_send_url = "/chat.postMessage"

    async def send_message(self, message: str):
        url = self.base_url + self.post_send_url
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        body = {
            "channel": self.channel,
            "text": message
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=json.dumps(body))
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class ErrorHandler(metaclass=SingletonMeta):
    def __init__(self):
        self.slack_notifier = SlackNotifier(slack_token, slack_channel, slack_project)

    async def log_error(self, error_type: str, message: str, trace: str, detail_message: str = None):
        log_msg = f"{error_type}: {message}\n{trace}"
        # if detail_message:
        #     log_msg += f"\nDetail: {detail_message}"
        logger.error(log_msg)


    async def send_slack_notification(self, error_type: str, message: str, detail_message: str, request: Request = None, error_url: str = None):
        timestamp = datetime.utcnow().isoformat()
        path = request.url.path if request else "N/A"
        method = request.method if request else "N/A"
        request_id = request.headers.get("X-Request-ID", "N/A") if request else "N/A"

        error_message = str(message)
        short_error_message = error_message[:200] + "..." if len(error_message) > 200 else error_message
        slack_message = (
            "==========================================\n"
            f"[culture-data-{environment}]\n"
            f"timestamp : {timestamp}\n"
            f"path : {method} {path}\n"
            f"requestId : {request_id}\n"
            f"url : {error_url}\n"
            f"message : {short_error_message}\n"
            # f"detail_message : {detail_message}\n"
            "=========================================="
        )

        await self.slack_notifier.send_message(slack_message)

    def classify_error(self, error):
        return type(error).__name__

    async def handle_error(self, error, api_source: str, detail_message: str = None, request: Request = None, alert: bool = False, error_url: str = None):
        error_type = self.classify_error(error)
        message = str(error)
        trace = traceback.format_exc()

        # Extract function name from traceback
        tb = traceback.extract_tb(error.__traceback__)
        function_name = tb[-1].name if tb else "Unknown"

        # Log, save to DB, and notify Slack asynchronously
        await self.log_error(error_type, message, trace, detail_message)
        
        if alert:
            await self.send_slack_notification(error_type, message, detail_message, request, error_url)

class ErrorResponse:
    """에러 응답 생성 클래스"""
    @staticmethod
    def create_error_response(
        request: Request,
        status_code: int,
        error: str,
        message: str,
        additional_info: Dict = None
    ) -> JSONResponse:
        response_content = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status": status_code,
            "code": status_code,
            "error": error,
            "message": message
        }
        
        if additional_info:
            response_content.update(additional_info)
            
        return JSONResponse(
            status_code=status_code,
            content=response_content
        )

class InternalServerError:
    """500 에러 처리 전용 클래스"""
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler

    async def handle_known_error(self, request: Request, exc: Exception) -> JSONResponse:
        """알려진 내부 서버 에러 처리"""
        exc_message = str(exc)
        await self.error_handler.handle_error(
            exc, 
            "500: known_internal_error", 
            exc_message, 
            request, 
            True
        )
        
        return ErrorResponse.create_error_response(
            request=request,
            status_code=500,
            error="An internal server error occurred.",
            message="알수없는 에러가 발생했습니다. 자세한 사항은 errorlog 참고"
        )

    async def handle_unknown_error(self, request: Request, exc: Exception) -> JSONResponse:
        """예상치 못한 내부 서버 에러 처리"""
        exc_message = str(exc)
        await self.error_handler.handle_error(
            exc, 
            "500: unknown_internal_error", 
            exc_message, 
            request, 
            False
        )
        
        return ErrorResponse.create_error_response(
            request=request,
            status_code=500,
            error="An internal server error occurred.",
            message="알수없는 에러가 발생했습니다. 자세한 사항은 채널톡으로 문의주세요."
        )