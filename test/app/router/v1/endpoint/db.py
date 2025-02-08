from fastapi import APIRouter

from src.db.mongo import connect_to_mongo
from src.crud.company import search_company, update_company, delete_company, get_all_companies
from src.crud.page import add_new_page, search_page, update_page_content, delete_page   

router = APIRouter()

@router.get("/db/search_company")
def search_company_api(company_name: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    document = search_company(collection, company_name)
    if document:
        return {"status": True, "data": document}
    else:
        return {"status": False, "message": "해당 회사의 데이터가 없습니다."}
    

@router.put("/db/update_company")
def update_company_api(company_name: str, root_url: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    result = update_company(collection, company_name, root_url)
    return result


@router.delete("/db/delete_company")
def delete_company_api(company_name: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    result = delete_company(collection, company_name)
    return result


@router.get("/db/get_all_companies")
def get_all_companies_api():
    """
    모든 회사 데이터를 조회하는 API.
    """

    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    result = get_all_companies(collection)
    return result


@router.post("/db/add_new_page")
def add_new_page_api(root_name: str, url: str, text: str):
    """
    특정 회사가 DB에 존재할 경우 신규 페이지를 등록하는 API.

    :param root_name: 회사명
    :param url: 추가할 페이지 URL
    :param text: 추가할 페이지 내용
    """
    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    return add_new_page(collection, root_name, url, text)


@router.get("/db/search_page")
def search_page_api(root_name: str, target_url: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    result = search_page(collection, root_name, target_url)
    return result


@router.put("/db/update_page")
def update_page_api(root_name: str, target_url: str, new_url: str = None, new_text: str = None):
    """
    특정 회사의 특정 페이지 내용을 업데이트하는 API.

    :param root_name: 회사명
    :param target_url: 기존 URL
    :param new_url: 변경할 새로운 URL (선택)
    :param new_text: 변경할 새로운 텍스트 (선택)
    """

    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    result = update_page_content(collection, root_name, target_url, new_url, new_text)
    return result


@router.delete("/db/delete_page")
def delete_page_api(root_name: str, target_url: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"status": False, "message": "MongoDB 연결 실패"}

    result = delete_page(collection, root_name, target_url)
    return result   