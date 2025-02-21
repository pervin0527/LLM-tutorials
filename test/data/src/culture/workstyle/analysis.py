import asyncio

from datetime import datetime
from typing import List, Dict, Any
from langchain.docstore.document import Document

from app.utils.logging import logger
from src.llm.utils import process_string_to_json
from src.llm.commercial_models import chatgpt_response

from src.culture.workstyle.prompts import (
    WORKSTYLE_TITLES, 
    WORKSTYLE_CONTEXTS, 
    WORKSTYLE_INITIAL_MESSAGES, 
    get_workstyle_messages
)

async def company_workstyle_analysis(documents: List[Document], vision_response: List[Dict[str, Any]]):
    """회사의 업무 스타일을 분석하여 키워드를 추출하고 30개 항목에 대해 병렬 평가하는 함수"""
    try:
        request = {}
        formatted_results = []  # formatted_results 초기화

        ## 문서들을 리스트로 변환 --> db 저장용
        document_list = []
        for doc in documents:
            if isinstance(doc, Document):
                document_list.append(doc.page_content)
            else:
                document_list.append(doc)
        request["page_content"] = document_list
        
        ## 각 비전 항목에 대해 병렬로 API 호출
        combined_data = ' '.join(document_list)
        prompts = [WORKSTYLE_INITIAL_MESSAGES]
        response_list = []
        for i, (ko_title, en_title) in enumerate(WORKSTYLE_TITLES.items()):
            contexts = WORKSTYLE_CONTEXTS.get(ko_title, "")
            messages = WORKSTYLE_INITIAL_MESSAGES + get_workstyle_messages(i+1, en_title, contexts, combined_data, vision_response)
            prompts.append(get_workstyle_messages(i+1, f"{ko_title}({en_title})", contexts, combined_data, vision_response))
            response_list.append(chatgpt_response(prompt=messages))

        ## 동시에 모든 요청을 실행
        all_responses = await asyncio.gather(*response_list)

        ## 응답 후처리도 병렬 처리
        process_tasks = [process_string_to_json(response) for response in all_responses]
        results = await asyncio.gather(*process_tasks)
        
        # 응답을 [{'en_title' : "ko_title", "score" : float, "summary" : str}] 형식으로 변환
        for i, result in enumerate(results):
            ko_title, en_title = list(WORKSTYLE_TITLES.items())[i]
            for keyword, data in result.items():
                formatted_results.append({
                    "code" : en_title,
                    "score": data['score'],
                    "summary": data['summary']
                })
        
        request["prompts"] = prompts
        return {"request": request, "response": formatted_results}

    except Exception as e:
        logger.error(f"키워드 추출 중 오류 발생: {str(e)}")
        return {"error": str(e)}