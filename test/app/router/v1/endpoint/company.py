from fastapi import APIRouter

from src.db.mongo import connect_to_mongo
from src.crud.company import search_company, update_company, delete_company, get_all_companies

router = APIRouter()

@router.get("/company/search_company")
def search_company_api(company_name: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"success": False, "message": "MongoDB 연결 실패"}

    document = search_company(collection, company_name)
    if document:
        return {"success": True, "data": document}
    else:
        return {"success": False, "message": "해당 회사의 데이터가 없습니다."}
    

@router.put("/company/update_company")
def update_company_api(company_name: str, root_url: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"success": False, "message": "MongoDB 연결 실패"}

    result = update_company(collection, company_name, root_url)
    return result


@router.delete("/company/delete_company")
def delete_company_api(company_name: str):
    collection = connect_to_mongo()
    if collection is None:
        return {"success": False, "message": "MongoDB 연결 실패"}

    result = delete_company(collection, company_name)
    return result


@router.get("/company/get_all_companies")
def get_all_companies_api():
    """
    모든 회사 데이터를 조회하는 API.
    """

    collection = connect_to_mongo()
    if collection is None:
        return {"success": False, "message": "MongoDB 연결 실패"}

    result = get_all_companies(collection)
    return result
