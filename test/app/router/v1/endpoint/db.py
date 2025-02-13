from fastapi import APIRouter, Request, HTTPException

from src.db.mongo import connect_to_mongo

from src.crud.page import add_new_page, search_page, update_page_content, delete_page   
from src.crud.company import search_company, update_company, delete_company, get_all_companies

from app.utils.logging import logger
from app.schemas.v1.db_schemas import (
    CompanyName,
    UpdateCompany, 
    DeleteCompany, 
    SearchPage, 
    AddNewPage, 
    UpdatePage, 
    DeletePage, 
)

router = APIRouter()

@router.get("/db/search_company")
def search_company_api(company: CompanyName):
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        document = search_company(collection, company.company_name)
        if document:
                return {"status": "success", "data": document}
        else:   
            return {"status": "error", "message": "해당 회사의 데이터가 없습니다."}
    
    except Exception as e:
        logger.error(f"회사 검색 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"회사 검색 중 오류 발생: {str(e)}"}


@router.put("/db/update_company")
def update_company_api(company: UpdateCompany):
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        result = update_company(collection, company.company_name, company.root_url)
        return result
    
    except Exception as e:
        logger.error(f"회사 업데이트 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"회사 업데이트 중 오류 발생: {str(e)}"}


@router.delete("/db/delete_company")
def delete_company_api(request: Request, company: DeleteCompany):
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}
    
        vector_store = request.app.state.vector_store
        result = delete_company(collection, company.company_name, vector_store)
        return result
    
    except Exception as e:
        logger.error(f"회사 삭제 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"회사 삭제 중 오류 발생: {str(e)}"}


@router.get("/db/get_all_companies")
def get_all_companies_api():
    """
    모든 회사 데이터를 조회하는 API.
    """
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        result = get_all_companies(collection)
        return result
    
    except Exception as e:
        logger.error(f"모든 회사 조회 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"모든 회사 조회 중 오류 발생: {str(e)}"}


@router.get("/db/search_page")
def search_page_api(page: SearchPage):
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        result = search_page(collection, page.company_name, page.target_url)
        return result
    
    except Exception as e:
        logger.error(f"페이지 검색 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"페이지 검색 중 오류 발생: {str(e)}"}


@router.post("/db/add_new_page")
def add_new_page_api(request: Request, page: AddNewPage):
    """
    특정 회사가 DB에 존재할 경우 신규 페이지를 등록하는 API.

    :param company_name: 회사명
    :param url: 추가할 페이지 URL
    :param text: 추가할 페이지 내용
    """

    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        vector_store = request.app.state.vector_store

        return add_new_page(collection, page.company_name, page.url, page.text, vector_store)
    
    except Exception as e:
        logger.error(f"페이지 추가 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"페이지 추가 중 오류 발생: {str(e)}"}


@router.put("/db/update_page")
def update_page_api(request: Request, page: UpdatePage):
    """
    특정 회사의 특정 페이지 내용을 업데이트하는 API.

    :param company_name: 회사명
    :param target_url: 기존 URL
    :param new_url: 변경할 새로운 URL (선택)
    :param new_text: 변경할 새로운 텍스트 (선택)
    """

    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        vector_store = request.app.state.vector_store
        result = update_page_content(collection, vector_store, page.company_name, page.target_url, page.new_url, page.new_text)
        return result
    
    except Exception as e:
        logger.error(f"페이지 업데이트 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"페이지 업데이트 중 오류 발생: {str(e)}"}


@router.delete("/db/delete_page")
def delete_page_api(request: Request, page: DeletePage):
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}
    
        vector_store = request.app.state.vector_store
        result = delete_page(collection, vector_store, page.company_name, page.target_url)
        return result
    
    except Exception as e:
        logger.error(f"페이지 삭제 중 오류 발생: {str(e)}")
        return {"status": "error", "message": f"페이지 삭제 중 오류 발생: {str(e)}"}


@router.delete("/db/delete_all_company_homepage")
def delete_all_company_homepage_api(request: Request):
    """
    company_homepage 컬렉션의 모든 데이터를 삭제하고 벡터 DB의 모든 문서를 제거하는 API.
    """
    try:
        collection = connect_to_mongo("culture_db", "company_homepage")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        # MongoDB의 모든 문서 삭제
        result = collection.delete_many({})
        logger.info(f"✅ {result.deleted_count}개의 문서가 삭제되었습니다.")

        # 벡터 DB의 모든 문서 삭제
        vector_store = request.app.state.vector_store
        if vector_store is None:
            logger.error("❌ 벡터 스토어가 초기화되지 않았습니다.")
            return {"status": "error", "message": "벡터 스토어 초기화 실패"}

        vector_store.clear_all_documents()  # 모든 문서를 제거하는 메서드 호출
        logger.info("✅ 벡터 DB의 모든 문서가 삭제되었습니다.")

        return {"status": True, "message": f"{result.deleted_count}개의 문서가 삭제되었습니다. 벡터 DB의 모든 문서도 삭제되었습니다."}
    
    except Exception as e:
        logger.error(f"❌ 문서 삭제 실패: {e}")
        return {"status": "error", "message": f"문서 삭제 실패: {e}"}


@router.delete("/db/delete_all_reviews")
def delete_all_reviews_api():
    """
    company_review 컬렉션의 모든 데이터를 삭제하는 API.
    """
    try:
        collection = connect_to_mongo("culture_db", "company_review")
        if collection is None:
            return {"status": "error", "message": "MongoDB 연결 실패"}

        result = collection.delete_many({})
        logger.info(f"✅ {result.deleted_count}개의 문서가 삭제되었습니다.")
        return {"status": "success", "message": f"{result.deleted_count}개의 문서가 삭제되었습니다."}
    
    except Exception as e:
        logger.error(f"❌ 문서 삭제 실패: {e}")
        return {"status": "error", "message": f"문서 삭제 실패: {e}"}