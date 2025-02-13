from openai import OpenAI
from anthropic import Anthropic

from typing import List
from fastapi import APIRouter, Request

from app.utils.logging import logger

router = APIRouter()

def industry_inference(request: Request, company_name: str) -> str:
    client = OpenAI(api_key=request.app.state.cfg.get("openai_api_key"))

    query = f"{company_name}은(는) 어떤 산업에 속하는 기업인가요?"
    vector_store = request.app.state.vector_store
    if vector_store is None:
        logger.error("❌ 벡터 스토어가 초기화되지 않았습니다.")
        return
    
    ret_results = vector_store.similarity_search_with_score(query, filter=company_name)
    logger.info(f"{ret_results}")

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "당신은 뛰어난 기업 분석가입니다. 주어진 문서들을 보고 해당 기업이 어떤 산업에 속하는지 추론하여 하나의 단어로 출력해주세요."},
            {"role": "user", "content": ret_results}
        ],
        temperature=0.0
    )
        prediction = completion.choices[0].message.content
        logger.info(f"{prediction}")
    except Exception as e:
        logger.error(f"❌ 산업 추론 실패: {e}")
        return

    return prediction