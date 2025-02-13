from typing import Optional
from fastapi import APIRouter, HTTPException, Request

from src.db.mongo import connect_to_mongo
from app.schemas.v1.db_schemas import CompaniesResponse, BizNoList, CompanyRegistration, CompanyResponse, CompanyInfo, CompanyNewsResponse, CompanyReviewResponse


from app.utils.logging import logger

router = APIRouter()

@router.post("/db/search_companies_by_biz_no", response_model=CompaniesResponse)
async def search_companies_by_biz_no_api(data: BizNoList):
    """
    사업자 번호 리스트로 회사 정보를 조회하는 API
    
    Returns:
        각 사업자번호에 대해 회사명, 홈페이지, 상태(존재여부) 정보를 포함하는 목록
    """
    try:
        collection = connect_to_mongo("culture_db", "company")
        if collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        # 필요한 필드만 조회
        projection = {
            "biz_no": 1,
            "company_name": 1,
            "homepage": 1
        }

        # MongoDB에서 데이터 조회
        found_companies = list(collection.find(
            {"biz_no": {"$in": data.biz_no_list}},
            projection
        ))

        # 조회된 회사들의 사업자번호 집합
        found_biz_nos = {doc["biz_no"] for doc in found_companies}

        # 결과 생성
        result = []
        for biz_no in data.biz_no_list:
            if biz_no in found_biz_nos:
                # 존재하는 회사 정보 찾기
                company_doc = next(doc for doc in found_companies if doc["biz_no"] == biz_no)
                company_info = CompanyInfo(
                    biz_no=biz_no,
                    company_name=company_doc.get("company_name", ""),
                    homepage=company_doc.get("homepage"),
                    status="active"  # 데이터가 존재하는 경우
                )
            else:
                # 존재하지 않는 회사
                company_info = CompanyInfo(
                    biz_no=biz_no,
                    company_name="",
                    homepage=None,
                    status="inactive"  # 데이터가 존재하지 않는 경우
                )
            result.append(company_info)

        return CompaniesResponse(
            status="success",
            data=result
        )

    except Exception as e:
        logger.error(f"사업자 번호로 회사 검색 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사업자 번호로 회사 검색 중 오류 발생: {str(e)}"
        )
    

@router.post("/db/register_company", response_model=CompanyResponse)
async def register_company_api(request: Request, data: CompanyRegistration):
    """
    새로운 회사를 등록하고 크롤링을 수행하는 API
    
    Args:
        data: 사업자번호, 회사명, 홈페이지 URL을 포함하는 데이터
    
    Returns:
        등록된 회사 정보와 상태
    """
    from app.router.v1.endpoint.crawler import (
        get_company_info_api,
        get_company_homepage_api,
        get_company_review_api
    )

    try:
        # 1. get_company_info_api 호출
        info_response = get_company_info_api(data.company_name)
        if info_response["status"] != "success":
            raise HTTPException(status_code=500, detail="회사 정보 수집 실패")

        # 2. get_company_homepage_api 호출
        homepage_response = get_company_homepage_api(
            request=request,
            company_name=data.company_name,
            start_url=data.homepage
        )
        if homepage_response["status"] != "success":
            raise HTTPException(status_code=500, detail="홈페이지 크롤링 실패")

        # 3. get_company_review_api 호출
        review_response = get_company_review_api(
            company_name=data.company_name,
            company_url=data.homepage,
            company_bizno=data.biz_no
        )
        if review_response["status"] != "success":
            raise HTTPException(status_code=500, detail="리뷰 크롤링 실패")

        # 4. company 컬렉션에서 최종 데이터 조회
        collection = connect_to_mongo("culture_db", "company")
        if collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        company_data = collection.find_one({"company_name": data.company_name})
        
        if company_data is None:
            return CompanyResponse(
                biz_no=data.biz_no,
                company_name=data.company_name,
                homepage=data.homepage,
                status="inactive"
            )

        # 등록 성공 응답
        return CompanyResponse(
            biz_no=company_data.get("biz_no", data.biz_no),
            company_name=company_data.get("company_name", data.company_name),
            homepage=company_data.get("homepage", data.homepage),
            status="active"
        )

    except Exception as e:
        logger.error(f"회사 등록 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"회사 등록 중 오류 발생: {str(e)}"
        )
    

@router.get("/db/get_company_news", response_model=CompanyNewsResponse)
async def get_company_news(biz_no: str, company_name: Optional[str] = None):
    """
    사업자 번호로 기업을 조회하고, 해당 기업의 뉴스 데이터를 반환하는 API
    """
    company_collection = connect_to_mongo("culture_db", "company")
    news_collection = connect_to_mongo("culture_db", "company_news")

    # 1. 사업자 번호를 기반으로 기업 조회
    query = {"biz_no": biz_no}
    if company_name:
        query["company_name"] = company_name
    
    company_data = company_collection.find_one(query)
    if not company_data:
        raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")
    
    # 2. company_news 컬렉션에서 해당 기업의 뉴스 조회
    news_data = news_collection.find_one({"company": company_data["company_name"]})
    
    return {
        "company": company_data["company_name"],
        "biz_no": company_data["biz_no"],
        "collected_date": news_data.get("collected_date", ""),
        "updated_date": news_data.get("updated_date", ""),
        "news": news_data.get("news_data", []) if news_data else []
    }


@router.get("/db/get_company_reviews", response_model=CompanyReviewResponse)
async def get_company_reviews(biz_no: str, company_name: Optional[str] = None):
    """
    사업자 번호로 기업을 조회하고, 해당 기업의 리뷰 데이터를 반환하는 API

    Args:
        biz_no (str): 사업자 번호
        company_name (Optional[str]): 회사명 (선택사항)

    Returns:
        CompanyReviewResponse: 회사 리뷰 정보를 포함하는 응답
        
    Raises:
        HTTPException: MongoDB 연결 실패 또는 데이터 조회 실패시 발생
    """
    try:
        # MongoDB 컬렉션 연결
        company_collection = connect_to_mongo("culture_db", "company")
        review_collection = connect_to_mongo("culture_db", "company_review")
        
        if company_collection is None or review_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        # 1. 사업자 번호를 기반으로 기업 조회
        query = {"biz_no": biz_no}
        if company_name:
            query["company_name"] = company_name
        
        company_data = company_collection.find_one(query)
        if not company_data:
            raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")
        
        # 2. company_review 컬렉션에서 해당 기업의 리뷰 조회
        review_data = review_collection.find_one({"company": company_data["company_name"]})
        
        if not review_data:
            return {
                "company": company_data["company_name"],
                "biz_no": company_data["biz_no"],
                "collected_date": "",
                "updated_date": "",
                "review_data": []
            }

        # 3. 응답 데이터 구성
        return {
            "company": company_data["company_name"],
            "biz_no": company_data["biz_no"],
            "collected_date": review_data.get("collected_date", ""),
            "updated_date": review_data.get("updated_date", ""),
            "review_data": review_data.get("review_data", [])
        }

    except Exception as e:
        logger.error(f"회사 리뷰 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"회사 리뷰 조회 중 오류 발생: {str(e)}"
        )