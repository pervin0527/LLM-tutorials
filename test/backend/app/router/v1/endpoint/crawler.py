import os
import httpx


from typing import Optional
from fastapi import APIRouter, Request
from app.utils.logging import logger

router = APIRouter()

async def forward_request(request: Request, endpoint: str, params: dict):
    """서버2로 요청을 전달하는 헬퍼 함수"""
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            # /api/v1 prefix 추가
            response = await client.get(f"{request.app.state.cfg['data_server']}/api/v1{endpoint}", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"서버2 요청 실패: {e}")
            return {"status": "error", "message": f"서버2 요청 실패: {str(e)}"}

@router.get("/crawler/company_info")
async def get_company_info_api(request: Request, company_name: str):
    logger.info(f"### 서버2로 기업정보 수집 요청 전달")
    return await forward_request(request, "/crawler_worker/company_info", {"company_name": company_name})


@router.get("/crawler/company_homepage")
async def get_company_homepage_api(
    request: Request, 
    company_name: str, 
    start_url: Optional[str] = None, 
    max_pages: int = 100
):
    logger.info(f"### 서버2로 홈페이지 수집 요청 전달")
    params = {
        "company_name": company_name,
        "start_url": start_url,
        "max_pages": max_pages
    }
    return await forward_request(request, "/crawler_worker/company_homepage", params)


@router.get("/crawler/company_review")
async def get_company_review_api(
    request: Request,
    company_name: str,
    company_url: Optional[str] = None,
    company_bizno: Optional[str] = None,
    date_filter: str = "2024.12"
):
    logger.info(f"### 서버2로 리뷰 수집 요청 전달")
    params = {
        "company_name": company_name,
        "company_url": company_url,
        "company_bizno": company_bizno,
        "date_filter": date_filter
    }
    return await forward_request(request, "/crawler_worker/company_review", params)


@router.get("/crawler/company_news")
async def get_company_news_api(request: Request, company_name: str, num_articles: int = 50):
    logger.info(f"### 서버2로 뉴스 수집 요청 전달")
    params = {
        "company_name": company_name,
        "num_articles": num_articles
    }
    return await forward_request(request, "/crawler_worker/company_news", params)


@router.get("/crawler/company_welfare")
async def get_company_welfare_api(request: Request, company_name: str):
    logger.info(f"### 서버2로 복지 수집 요청 전달")
    return await forward_request(request, "/crawler_worker/company_welfare", {"company_name": company_name})
    