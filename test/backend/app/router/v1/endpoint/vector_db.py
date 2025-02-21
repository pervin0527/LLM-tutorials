import logging
from fastapi import APIRouter, HTTPException, Request, Query, Body
import httpx
from app.utils.logging import logger

logger = logging.getLogger(__name__)

router = APIRouter()

async def forward_request(request: Request, endpoint: str, params: dict, method: str = "get"):
    """서버2로 요청을 전달하는 헬퍼 함수"""
    base_url = f"{request.app.state.cfg['data_server']}/api/v1{endpoint}"
    
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            if method.lower() in ["get", "delete"]:
                # GET과 DELETE 요청은 쿼리 파라미터로 전송
                response = await client.request(
                    method=method,
                    url=base_url,
                    params=params
                )
            else:
                # POST와 PUT 요청은 JSON body로 전송
                response = await client.request(
                    method=method,
                    url=base_url,
                    json=params
                )
            return response.json()
        except Exception as e:
            logger.error(f"서버2 요청 실패: {e}")
            return {"status": "error", "message": f"서버2 요청 실패: {str(e)}"}


@router.get("/vector_db/search_company")
async def search_company_api(request: Request, company_name: str):
    """
    주어진 회사명이 벡터 데이터베이스에 존재하는지 확인하고, 몇 개의 문서가 있는지 반환하는 API.
    """
    return await forward_request(request, "/vector_db_worker/search_company", {"company_name": company_name})


@router.delete("/vector_db/delete_company")
async def delete_company_api(request: Request, company_name: str):
    """
    주어진 회사명에 해당하는 모든 문서를 벡터 데이터베이스에서 삭제하는 API.
    """
    return await forward_request(request, "/vector_db_worker/delete_company", {"company_name": company_name}, method="delete")


@router.get("/vector_db/get_company_documents")
async def get_company_documents_api(request: Request, company_name: str):
    """
    주어진 회사명을 가진 모든 문서를 벡터 데이터베이스에서 검색하여 반환하는 API.
    """
    return await forward_request(request, "/vector_db_worker/get_company_documents", {"company_name": company_name})


@router.get("/vector_db/search_document")
async def search_document_api(request: Request, company_name: str, url: str):
    """
    주어진 회사명과 URL에 해당하는 문서를 검색하여 반환하는 API.
    """
    return await forward_request(request, "/vector_db_worker/search_document", {"company_name": company_name, "url": url})


@router.put("/vector_db/update_document")
async def update_document_api(request: Request, company_name: str, url: str, new_url: str = Query(None), new_text: str = Query(None)):
    """
    주어진 회사명과 URL에 해당하는 문서를 업데이트하는 API.
    """
    params = {
        "company_name": company_name,
        "url": url,
        "new_url": new_url,
        "new_text": new_text
    }
    return await forward_request(request, "/vector_db_worker/update_document", params, method="put")


@router.delete("/vector_db/delete_document")
async def delete_document_api(request: Request, company_name: str, url: str):
    """
    주어진 회사명과 URL에 해당하는 문서를 벡터 데이터베이스에서 삭제하는 API.
    """
    params = {
        "company_name": company_name,
        "url": url
    }
    return await forward_request(request, "/vector_db_worker/delete_document", params, method="delete")


@router.get("/vector_db/similarity_search_with_score")
async def similarity_search_with_score_api(request: Request, query: str):
    """
    주어진 쿼리와 회사명에 따라 유사도 점수를 기반으로 문서를 검색하는 API.
    """
    return await forward_request(request, "/vector_db_worker/similarity_search_with_score", {"query": query})


@router.get("/vector_db/similarity_search_with_relevance_scores")
async def similarity_search_with_relevance_scores_api(request: Request, query: str):
    """
    주어진 쿼리와 회사명에 따라 관련성 점수를 기반으로 문서를 검색하는 API.
    """
    return await forward_request(request, "/vector_db_worker/similarity_search_with_relevance_scores", {"query": query})