import json
import asyncio

from bson import ObjectId

from datetime import datetime
from typing import List, Dict, Any
from langchain.docstore.document import Document

from app.utils.logging import logger
from src.llm.utils import process_string_to_json
from src.llm.commercial_models import chatgpt_response

from src.culture.turnover.prompts import (
    TURNOVER_TITLES, 
    TURNOVER_CONTEXTS, 
    TURNOVER_INITIAL_MESSAGES, 
    get_turnover_messages
)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


def get_data_context(title: str, data: list) -> str:
    """
    주어진 데이터를 JSON 문자열로 변환하여 프롬프트에 반영할 텍스트를 생성합니다.
    CustomJSONEncoder를 사용하여 ObjectId와 같은 직렬화 불가한 객체를 문자열로 변환합니다.
    """
    data_str = json.dumps(data, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
    context = f"아래의 데이터는 평가에 참고할 {title} 자료입니다:\n\n{data_str}\n\n"
    return context


async def company_turnover_analysis(welfare_data, review_data):
    """회사의 재직 만족도를 분석하여 9개 항목에 대해 병렬 평가하는 함수"""
    try:
        request = {}
        formatted_results = []  # formatted_results 초기화

        welfare_context = get_data_context("복지", welfare_data)
        review_context = get_data_context("리뷰", review_data)
        combined_data = f"{welfare_context}\n\n{review_context}"
        logger.info(f"[company_turnover_analysis] combined_data: {combined_data}")

        prompts = [TURNOVER_INITIAL_MESSAGES]
        response_list = []
        for i, (ko_title, en_title) in enumerate(TURNOVER_TITLES.items()):
            contexts = TURNOVER_CONTEXTS.get(ko_title, "")
            messages = TURNOVER_INITIAL_MESSAGES + get_turnover_messages(i+1, en_title, contexts, combined_data)
            prompts.append(get_turnover_messages(i+1, f"{ko_title}({en_title})", contexts, combined_data))
            response_list.append(chatgpt_response(prompt=messages))

        ## 동시에 모든 요청을 실행
        all_responses = await asyncio.gather(*response_list)

        ## 응답 후처리도 병렬 처리
        process_tasks = [process_string_to_json(response) for response in all_responses]
        results = await asyncio.gather(*process_tasks)
        
        # 응답을 [{'en_title' : "ko_title", "score" : float, "summary" : str}] 형식으로 변환
        for i, result in enumerate(results):
            ko_title, en_title = list(TURNOVER_TITLES.items())[i]
            for keyword, data in result.items():
                formatted_results.append({
                    "code" : en_title,
                    "score": data['score'],
                    "summary": data['summary']
                })
        
        request["prompts"] = prompts
        return {"request": request, "response": formatted_results}

    except Exception as e:
        logger.error(f"회사 재직 만족도 분석 중 오류 발생: {str(e)}")
        return {"error": str(e)}