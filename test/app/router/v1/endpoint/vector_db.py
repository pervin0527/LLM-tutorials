import logging
from fastapi import APIRouter, HTTPException, Request, Query, Body

from src.db.mongo import connect_to_mongo
from src.crud.company import delete_company
from src.crud.page import update_page_content, delete_page

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/vector_db/search_company")
def search_company_api(request: Request, company_name: str):
    """
    주어진 회사명이 벡터 데이터베이스에 존재하는지 확인하고, 몇 개의 문서가 있는지 반환하는 API.
    """
    try:
        vector_store = request.app.state.vector_store
        count = vector_store.search_company(company_name)
        
        return {"success": True, "count": count}
    
    except Exception as e:
        logger.error(f"회사 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 검색 중 오류 발생: {str(e)}")


@router.delete("/vector_db/delete_company")
def delete_company_api(request: Request, company_name: str):
    """
    주어진 회사명에 해당하는 모든 문서를 벡터 데이터베이스에서 삭제하는 API.
    """
    try:
        vector_store = request.app.state.vector_store
        success = vector_store.delete_company(company_name)

        collection = connect_to_mongo("culture_db", "company_websites")
        if collection is None:
            return {"success": False, "message": "MongoDB 연결 실패"}
        
        delete_company(collection, company_name)
        
        if success:
            return {"success": True, "message": f"'{company_name}' 회사의 문서가 삭제되었습니다."}
        else:
            return {"success": False, "message": f"'{company_name}' 회사의 문서를 찾을 수 없습니다."}
    
    except Exception as e:
        logger.error(f"문서 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류 발생: {str(e)}")


@router.get("/vector_db/get_company_documents")
def get_company_documents_api(request: Request, company_name: str):
    """
    주어진 회사명을 가진 모든 문서를 벡터 데이터베이스에서 검색하여 반환하는 API.
    """
    try:
        logger.info(f"Available state attributes: {dir(request.app.state)}")
        vector_store = request.app.state.vector_store
        logger.info(f"Retrieved vector_store: {vector_store}")
        results = vector_store.get_company_documents(company_name)
        
        if not results:
            return {"success": False, "message": f"'{company_name}' 회사의 문서를 찾을 수 없습니다."}
        
        return {"success": True, "data": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 검색 중 오류 발생: {str(e)}")


@router.get("/vector_db/search_document")
def search_document_api(request: Request, company_name: str, url: str):
    """
    주어진 회사명과 URL에 해당하는 문서를 검색하여 반환하는 API.
    """
    try:
        vector_store = request.app.state.vector_store
        document = vector_store.search_document(company_name, url)
        
        if document:
            return {"success": True, "data": document}
        else:
            return {"success": False, "message": f"'{company_name}' 회사의 URL '{url}'에 해당하는 문서를 찾을 수 없습니다."}
    
    except Exception as e:
        logger.error(f"문서 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 검색 중 오류 발생: {str(e)}")


@router.put("/vector_db/update_document")
def update_document_api(request: Request, company_name: str, url: str, new_url: str = Query(None), new_text: str = Query(None)):
    """
    주어진 회사명과 URL에 해당하는 문서를 업데이트하는 API.
    """
    try:
        collection = connect_to_mongo("culture_db", "company_websites")
        if collection is None:
            return {"success": False, "message": "MongoDB 연결 실패"}
        
        vector_store = request.app.state.vector_store
        update_page_content(collection, vector_store, company_name, url, new_url, new_text)
        
        return {"success": True, "message": "문서 업데이트 성공"}
    
    except Exception as e:
        logger.error(f"문서 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 업데이트 중 오류 발생: {str(e)}")


@router.delete("/vector_db/delete_document")
def delete_document_api(request: Request, company_name: str, url: str):
    """
    주어진 회사명과 URL에 해당하는 문서를 벡터 데이터베이스에서 삭제하는 API.
    """
    try:
        collection = connect_to_mongo("culture_db", "company_websites")
        if collection is None:
            return {"success": False, "message": "MongoDB 연결 실패"}

        vector_store = request.app.state.vector_store
        delete_page(collection, vector_store, company_name, url)
        
        return {"success": True, "message": f"'{company_name}' 회사의 URL '{url}'에 해당하는 문서가 삭제되었습니다."}
    
    except Exception as e:
        logger.error(f"문서 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류 발생: {str(e)}")


@router.get("/vector_db/similarity_search_with_score")
def similarity_search_with_score_api(request: Request, query: str):
    """
    주어진 쿼리와 회사명에 따라 유사도 점수를 기반으로 문서를 검색하는 API.
    """
    try:
        vector_store = request.app.state.vector_store
        results = vector_store.similarity_search_with_score(query)
        
        return {"success": True, "data": results}
    
    except Exception as e:
        logger.error(f"유사도 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"유사도 검색 중 오류 발생: {str(e)}")


@router.get("/vector_db/similarity_search_with_relevance_scores")
def similarity_search_with_relevance_scores_api(request: Request, query: str):
    """
    주어진 쿼리와 회사명에 따라 관련성 점수를 기반으로 문서를 검색하는 API.
    """
    try:
        vector_store = request.app.state.vector_store
        results = vector_store.similarity_search_with_relevance_scores(query)
        
        return {"success": True, "data": results}
    
    except Exception as e:
        logger.error(f"관련성 점수 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관련성 점수 검색 중 오류 발생: {str(e)}")