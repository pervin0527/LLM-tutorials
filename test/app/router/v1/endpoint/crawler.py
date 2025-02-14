import os

from typing import Optional
from fastapi import APIRouter, Request

from src.crawler.company_info import get_company_info
from src.crawler.company_hompage import get_company_homepage
from src.crawler.company_news import get_company_news
from src.crawler.company_review import get_company_review
from src.crawler.company_welfare import get_company_welfare

from src.rag.data.dataset import convert_to_documents
from src.db.mongo import (
    save_to_mongo, 
    connect_to_mongo, 
    get_or_create_company, 
    convert_objectid_to_str,
    get_company 
)

from app.utils.logging import logger

router = APIRouter()

@router.post("/crawler/get_company_info")
def get_company_info_api(company_name: str):
    data = get_company_info(company_name)

    if not data:
        return {"status": "error", "message": "data 크롤링 데이터가 비어 있습니다."}

    collection = connect_to_mongo("culture_db", "company")

    # ✅ upsert=True를 사용하여 데이터가 존재하면 업데이트, 없으면 새로 추가
    result = collection.update_one(
        {"company_name": company_name},  # 검색 조건
        {"$set": data},  # 업데이트할 데이터
        upsert=True  # ✅ 존재하지 않으면 새로 추가
    )

    # ✅ 업데이트된 회사의 `_id` 가져오기
    existing_company = collection.find_one({"company_name": company_name})
    company_id = str(existing_company["_id"])

    # ✅ 모든 데이터에서 ObjectId를 문자열로 변환
    data = convert_objectid_to_str(data)

    return {"status": "success", "message": "기업정보 수집 성공", "company_id": company_id, "data": data}


@router.post("/crawler/get_company_homepage")
def get_company_homepage_api(request: Request, company_name: str, start_url: Optional[str] = None, max_pages: int = 100):
    try:
        company_id = get_or_create_company(company_name, start_url)  # ✅ `company` 컬렉션의 `_id`를 참조
        data = get_company_homepage(company_name, start_url, max_pages)

        if data['pages'] is None:
            return {"status": "error", "message": "data 크롤링 데이터가 비어 있습니다."}

        data["company_id"] = company_id  # ✅ `company_id` 추가

        collection = connect_to_mongo("culture_db", "company_homepage")
        save_to_mongo(collection, data)

        documents = convert_to_documents(data)

        # 벡터 데이터베이스에서 기존 문서 확인 및 업데이트
        vector_store = getattr(request.app.state, "vector_store", None)
        if vector_store is None:
            logger.error("벡터 스토어가 초기화되지 않았습니다.")
            return {"status": "error", "message": "벡터 스토어가 초기화되지 않았습니다."}

        # 기존 문서 가져오기, 없으면 빈 리스트 반환
        existing_documents = vector_store.get_company_documents(company_name) or []

        # 새 문서 추가
        new_documents = [doc for doc in documents if not any(d['url'] == doc.metadata['url'] for d in existing_documents)]

        if not new_documents:
            return {"status": "success", "message": "기존 문서와 중복되는 문서가 없어 추가할 문서가 없습니다.", "company_id": company_id}

        if hasattr(vector_store, "vector_db") and vector_store.vector_db:
            vector_store.vector_db.add_documents(new_documents)
            logger.info(f"✅ {len(new_documents)}개의 새 문서 추가 완료")

        return {"status": "success", "message": "크롤링 및 저장 성공", "company_id": company_id, "data": data}

    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        return {"status": "error", "message": f"크롤링 실패: {e}"}


@router.post("/crawler/get_company_review")
def get_company_review_api(
    company_name: str, 
    company_url: Optional[str] = None, 
    company_bizno: Optional[str] = None, 
    date_filter: str = "2024.12"
):
    try:
        company_id = get_or_create_company(company_name)  # ✅ `company` 컬렉션의 `_id`를 참조
        company_data = get_company(company_name)
        company_url = company_data.get("homepage")
        company_bizno = company_data.get("biz_no")

        data = get_company_review(company_name, company_url, company_bizno, date_filter)

        if data['review_data'] is None:
            return {"status": "error", "message": "data 크롤링 데이터가 비어 있습니다."}

        data["company_id"] = company_id  # ✅ `company_id` 추가
        try:
            collection = connect_to_mongo("culture_db", "company_review")
            save_to_mongo(collection, data)
            logger.info(f"잡플래닛 데이터가 MongoDB에 저장되었습니다: {company_name}")
        
        except Exception as e:
            logger.error(f"❌ 저장 실패: {e}")

        return {"status": "success", "message": "잡플래닛 크롤링 성공", "company_id": company_id, "data": data}

    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        return {"status": "error", "message": f"크롤링 실패: {e}"}


@router.post("/crawler/get_company_news")
def get_company_news_api(request: Request, company_name: str, num_articles: int = 50):
    try:
        company_id = get_or_create_company(company_name)
        data = get_company_news(company_name, num_articles, request.app.state.cfg['openai_api_key'])

        if data['news_data'] is None:
            return {"status": "error", "message": "data 크롤링 데이터가 비어 있습니다."}

        data["company_id"] = company_id
        try:
            collection = connect_to_mongo("culture_db", "company_news") 
            save_to_mongo(collection, data)
            logger.info(f"뉴스 데이터가 MongoDB에 저장되었습니다: {company_name}")
        
        except Exception as e:
            logger.error(f"❌ 저장 실패: {e}")

        return {"status": "success", "message": "기업 뉴스 크롤링 성공", "data": data}
    
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        return {"status": "error", "message": f"크롤링 실패: {e}"}
    

@router.post("/crawler/get_company_welfare")
def get_company_welfare_api(company_name: str):
    try:
        company_data = get_company(company_name)
        if company_data is None:
            return {"status": "error", "message": "기업 정보가 없습니다. 기업 정보를 먼저 수집해주세요."}
                
        company_bizno = company_data.get("biz_no", None)
        company_url = company_data.get("homepage", None)
        data = get_company_welfare(company_name, company_url, company_bizno)

        if data['welfare_data'] is None:
            return {"status": "error", "message": "data 크롤링 데이터가 비어 있습니다."}

        company_id = get_or_create_company(company_name)
        data["company_id"] = company_id

        collection = connect_to_mongo("culture_db", "company_welfare")
        save_to_mongo(collection, data)

        return {"status": "success", "message": "기업 복지 크롤링 성공", "data": data}
    
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        return {"status": "error", "message": f"크롤링 실패: {e}"}
    