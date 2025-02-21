import os
import json
import openai
import asyncio
import anthropic

from typing import Dict, List, Any

from app.utils.logging import logger
from src.utils.config_utils import load_config

from fastapi import HTTPException, status

cfg = load_config("app/configs/config.yaml")

openai_client = openai.AsyncOpenAI(api_key=cfg['openai_api_key'])
claude_client = anthropic.Anthropic(api_key=cfg['anthropic_api_key'])

def completion_run(messages):
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    usage_data = json.dumps(completion.to_dict(), indent=4)
    return usage_data

async def chatgpt_response(
    prompt: List[Dict[str, Any]],
    model: str = 'gpt-4o',
    retry_count: int = 1,
) -> str:

    # model = 'gpt-4o-mini'
    temperature = 0.001

    for attempt in range(retry_count):
        try:
            logger.info(f'{model} 모델로 응답 요청 중...')

            # OpenAI API 호출
            response = await openai_client.chat.completions.create(
                model=model,
                messages=prompt,
                temperature=temperature,
                seed=456
            )

            result = response.choices[0].message.content
            return result  # 성공적인 응답 반환

        except openai.RateLimitError as e:
            logger.warning(f"요청 한도 초과: {e}")
            await asyncio.sleep(2 ** (attempt + 2))  # 지수적 백오프
            continue

        except openai.InternalServerError as e:
            logger.error(f"서버 내부 오류: {e}")
            break

        except Exception as e:
            # 일반적인 예외 처리
            logger.error(f"예기치 않은 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "예기치 않은 오류", 
                    "message": "요청을 처리하는 중 예기치 않은 오류가 발생했습니다.",
                    "alert": True
                }
            )

    # 모든 재시도가 실패했을 경우
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "서비스 이용 불가", 
            "message": "서비스가 일시적으로 이용 불가능합니다. 잠시 후 다시 시도해 주세요.",
            "alert": True
        }
    )


async def anthropic_response(
    prompt: List[Dict[str, Any]],
    model: str = 'claude-3-5-sonnet-20240620',
    temperature: float = 0.001,
    max_tokens: int = 4096,
    top_p: float = 0.999,
    top_k: int = 250,
    retry_count: int = 1,
) -> str:
    for attempt in range(retry_count):
        try:
            logger.info(f'{model} 모델로 응답 요청 중...')
            
            # 메시지 변환 (OpenAI 형식 -> Anthropic 형식)
            formatted_messages = []
            for msg in prompt:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            response = claude_client.messages.create(
                model=model,
                system=system_content,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
            )

            return response.content[0].text

        except anthropic.RateLimitError as e:
            logger.warning(f"요청 한도 초과: {e}")
            await asyncio.sleep(2 ** (attempt + 2))  # 지수적 백오프
            continue

        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            logger.warning(f"API 연결 또는 타임아웃 오류: {e}")
            await asyncio.sleep(2 ** (attempt + 2))
            continue

        except anthropic.BadRequestError as e:
            if "credit" in str(e).lower():
                logger.error("크레딧 부족 오류")
            else:
                logger.error(f"잘못된 요청 오류: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "잘못된 요청",
                    "message": str(e),
                    "alert": True
                }
            )

        except (anthropic.APIError, anthropic.UnprocessableEntityError) as e:
            logger.error(f"API 오류: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "API 오류",
                    "message": str(e),
                    "alert": True
                }
            )

        except Exception as e:
            logger.error(f"예기치 않은 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "예기치 않은 오류",
                    "message": "요청을 처리하는 중 예기치 않은 오류가 발생했습니다.",
                    "alert": True
                }
            )

    # 모든 재시도가 실패했을 경우
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "서비스 이용 불가",
            "message": "서비스가 일시적으로 이용 불가능합니다. 잠시 후 다시 시도해 주세요.",
            "alert": True
        }
    )
