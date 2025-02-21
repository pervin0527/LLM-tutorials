from fastapi import APIRouter, Request
import httpx
from app.utils.logging import logger
from app.schemas.v1.db_schemas import (
    CompanyName, UpdateCompany, DeleteCompany, 
    SearchPage, AddNewPage, UpdatePage, DeletePage
)

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


@router.get("/db/search_company")
async def search_company_api(request: Request, company: CompanyName):
    return await forward_request(request, "/db_worker/search_company", {"company_name": company.company_name})


@router.put("/db/update_company")
async def update_company_api(request: Request, company: UpdateCompany):
    return await forward_request(request, "/db_worker/update_company", company.dict(), method="put")


@router.delete("/db/delete_company")
async def delete_company_api(request: Request, company: DeleteCompany):
    return await forward_request(request, "/db_worker/delete_company", {"company_name": company.company_name}, method="delete")


@router.get("/db/get_all_companies")
async def get_all_companies_api(request: Request):
    return await forward_request(request, "/db_worker/get_all_companies", {})


@router.get("/db/search_page")
async def search_page_api(request: Request, page: SearchPage):
    return await forward_request(request, "/db_worker/search_page", page.dict())


@router.post("/db/add_new_page")
async def add_new_page_api(request: Request, page: AddNewPage):
    return await forward_request(request, "/db_worker/add_new_page", page.dict(), method="post")


@router.put("/db/update_page")
async def update_page_api(request: Request, page: UpdatePage):
    return await forward_request(request, "/db_worker/update_page", page.dict(), method="put")


@router.delete("/db/delete_page")
async def delete_page_api(request: Request, page: DeletePage):
    return await forward_request(request, "/db_worker/delete_page", page.dict(), method="delete")


@router.delete("/db/delete_all_company_homepage")
async def delete_all_company_homepage_api(request: Request):
    return await forward_request(request, "/db_worker/delete_all_company_homepage", {}, method="delete")


@router.delete("/db/delete_all_reviews")
async def delete_all_reviews_api(request: Request):
    return await forward_request(request, "/db_worker/delete_all_reviews", {}, method="delete")