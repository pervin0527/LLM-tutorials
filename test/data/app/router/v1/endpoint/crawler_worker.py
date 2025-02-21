import os
from typing import Optional
from fastapi import APIRouter, Request

from src.crawler.company_info import get_company_info
from src.crawler.company_homepage import get_company_homepage
from src.crawler.company_news import get_company_news
from src.crawler.company_review import get_company_review
from src.crawler.company_welfare import get_company_welfare

from src.rag.data.dataset import convert_to_documents
from src.crawler.utils.data_utils import format_business_number, clean_company_name
from src.db.mongo import (
    save_to_mongo, 
    connect_to_mongo, 
    get_or_create_company, 
    convert_objectid_to_str,
    get_company 
)

from app.utils.logging import logger

router = APIRouter()

@router.get("/crawler_worker/company_info")
async def get_company_info_api(company_name: str, company_biz_no: str = None, company_url: str = None):
    """
    기업 정보를 수집하는 API
    """
    logger.info(f"company_name : {company_name}, company_biz_no : {company_biz_no}, company_url : {company_url}")

    try:
        # get_company_info는 비동기 함수이므로 await 사용
        data = await get_company_info(company_name, company_biz_no, company_url)

        return {"status": "success", "data": data}

    except Exception as e:
        logger.error(f"기업 정보 수집 중 오류 발생: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/crawler_worker/company_homepage")
async def get_company_homepage_api(request: Request, company_name: str, start_url: Optional[str] = None, max_pages: int = 100):
    try:      
        company_id = get_or_create_company(company_name)
        if company_id is None:
            return {"status": "error", "message": "Company ID Not Found"}

        data = await get_company_homepage(company_name, start_url, max_pages)
        
        data["company_id"] = company_id
        # company_data = get_company(company_id)
        # data['company_url'] = company_data.get("homepage")
        # data['company_bizno'] = company_data.get("biz_no")

        # MongoDB 저장
        collection = connect_to_mongo("culture_db", "company_homepage")
        save_to_mongo(collection, data)

        # 벡터 DB 저장
        vector_store = getattr(request.app.state, "vector_store", None)
        
        if vector_store is None:
            logger.warning("⚠[company_homepage] Vector DB is not initialized, MongoDB data saved.")
            return {"status": "partial_success", "message": "Vector DB is not initialized, MongoDB data saved.", "company_id": company_id}

        # 벡터 스토어 존재 여부 확인
        if not hasattr(vector_store, "vector_db") or not vector_store.vector_db:
            logger.warning("⚠ Vector DB is not initialized, cannot add documents.")
            return {"status": "partial_success", "message": "Vector DB is not initialized, MongoDB data saved.", "company_id": company_id}

        logger.info(f"✅[company_homepage] Vector DB is initialized: {vector_store.vector_db}")

        # 기존 문서 가져오기
        existing_documents = vector_store.get_company_documents(company_name) or []
        new_documents = [doc for doc in convert_to_documents(data) if not any(d['url'] == doc.metadata['url'] for d in existing_documents)]
        
        logger.info(f"📝 Number of new documents to add: {len(new_documents)}")
        if not new_documents:
            logger.info("✅[company_homepage] No new documents to add. All documents are duplicates.")
        else:
            
            # 문서 추가 시도
            try:
                vector_store.vector_db.add_documents(new_documents)
                logger.info(f"✅[company_homepage] {len(new_documents)} new documents added to Vector DB")

            except Exception as e:
                logger.warning(f"⚠[company_homepage] Vector DB save failed: {e}")
                return {"status": "partial_success", "message": f"Data Saved to MongoDB, Not Added to Vector DB(Error: {e})", "company_id": company_id}

        return {"status": "success", "message": "Data Saved to MongoDB, Added to Vector DB", "company_id": company_id, "data": data}

    except Exception as e:
        logger.error(f"❌[company_homepage] Crawling Failed: {e}")
        return {"status": "error", "message": f"{str(e)}"}


@router.get("/crawler_worker/company_review")
async def get_company_review_api(
    company_name: str, 
    company_url: Optional[str] = None, 
    company_bizno: Optional[str] = None, 
    date_filter: str = "2024.12"
):
    try:
        company_id = get_or_create_company(company_name)
        logger.info(f"[company_review] company_id : {company_id}")

        company_data = get_company(company_id)
        if company_data is None:
            return {"status": "error", "message": "Company Not Found"}

        company_url = company_data.get("homepage")
        company_bizno = company_data.get("biz_no")
        
        # 리뷰 수집 비동기 함수 호출
        data = await get_company_review(company_name, company_url, company_bizno, date_filter)

        data["company_id"] = company_id
        collection = connect_to_mongo("culture_db", "company_review")
        save_to_mongo(collection, data)

        return {"status": "success", "message": "Crawling Success", "company_id": company_id, "data": data}

    except Exception as e:
        logger.error(f"❌[company_review] Crawling Failed: {e}")
        return {"status": "error", "message": f"{str(e)}"}


@router.get("/crawler_worker/company_welfare")
async def get_company_welfare_api(company_name: str, company_url: str = None, company_bizno: str = None):
    try:
        company_id = get_or_create_company(company_name)
        company_data = get_company(company_id)
        if company_data is None:
            return {"status": "error", "message": "Company Not Found"}

        # get_company_welfare 호출
        data = await get_company_welfare(company_name, company_url or company_data.get("homepage"), company_bizno or company_data.get("biz_no"))
        
        # MongoDB에 저장
        data["company_id"] = company_id
        collection = connect_to_mongo("culture_db", "company_welfare")
        save_to_mongo(collection, data)

        return {"status": "success", "message": "Crawling Success", "data": data}

    except Exception as e:
        logger.error(f"❌[company_welfare] Crawling Failed: {e}")
        return {"status": "error", "message": f"{str(e)}"}
    


@router.get("/crawler_worker/company_news")
async def get_company_news_api(request: Request, company_name: str, num_articles: int = 50):
    try:
        company_id = get_or_create_company(company_name)
        company_data = get_company(company_id)
        if company_data is None:
            return {"status": "error", "message": "Company Not Found"}

        data = await get_company_news(company_name, num_articles, request.app.state.cfg['openai_api_key'])
        ## [25.02.20] 데이터가 없는 경우 에러로 취급하지 않음
        # if not data or 'news_data' not in data or not data['news_data']:
        #     return {"status": "error", "message": "Data is Empty"}

        data["company_id"] = company_id
        # data['company_url'] = company_data.get("homepage")
        # data['company_bizno'] = company_data.get("biz_no")

        collection = connect_to_mongo("culture_db", "company_news")
        save_to_mongo(collection, data)

        return {"status": "success", "message": "Crawling Success", "company_id": company_id, "data": data}

    except Exception as e:
        logger.error(f"❌[company_news] Crawling Failed: {e}")
        return {"status": "error", "message": f"{str(e)}"}