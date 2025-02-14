from typing import Optional
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, HTTPException, Request, Query

from src.db.mongo import connect_to_mongo
from app.schemas.v1.db_schemas import (
    CompaniesResponse, 
    BizNoList, 
    CompanyRegistration, 
    CompanyResponse, 
    CompanyInfo, 
    CompanyNewsResponse, 
    CompanyReviewResponse, 
    NewsItem,
    CompanyTotalData
)

from src.db.mongo import convert_objectid_to_str

from app.utils.logging import logger


router = APIRouter()

@router.post("/search_companies_by_biz_no", response_model=CompaniesResponse)
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
                    company_id=company_doc["_id"],
                    biz_no=biz_no,
                    company_name=company_doc.get("company_name", ""),
                    homepage=company_doc.get("homepage"),
                    status="success"  # 데이터가 존재하는 경우
                )
            else:
                # 존재하지 않는 회사
                company_info = CompanyInfo(
                    company_id=None,
                    biz_no=biz_no,
                    company_name="",
                    homepage=None,
                    status="error"  # 데이터가 존재하지 않는 경우
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
    

@router.post("/register_company", response_model=CompanyResponse)
async def register_company_api(
    request: Request,
    biz_no: str = Query(..., description="사업자등록번호 (필수)"),
    company_name: Optional[str] = Query(None, description="회사명 (선택)"),
    homepage: Optional[str] = Query(None, description="홈페이지 URL (선택)")
):
    """
    새로운 회사를 등록하고 크롤링을 수행하는 API
    
    Args:
        biz_no: 사업자등록번호 (필수)
        company_name: 회사명 (선택)
        homepage: 홈페이지 URL (선택)
    
    Returns:
        등록된 회사 정보와 상태
    """
    from app.router.v1.endpoint.crawler import (
        get_company_info_api,
        get_company_homepage_api,
        get_company_review_api,
        get_company_news_api,
        get_company_welfare_api
    )

    try:
        # 1. 회사 정보 자동 보완 (회사명이 없을 경우 biz_no로 검색)
        if not company_name:
            info_response = get_company_info_api(biz_no)
            if info_response["status"] != "success":
                raise HTTPException(status_code=500, detail="회사 정보 조회 실패")
            company_name = info_response.get("company_name")

        if not company_name:
            raise HTTPException(status_code=400, detail="회사명을 찾을 수 없습니다.")

        # 2. 홈페이지 정보 자동 보완 (홈페이지 주소가 없을 경우 크롤링)
        if not homepage:
            homepage_response = get_company_homepage_api(request=request, company_name=company_name)
            if homepage_response["status"] == "success":
                homepage = homepage_response.get("homepage", None)

        # 3. 리뷰 크롤링 수행
        review_response = get_company_review_api(company_name=company_name, company_url=homepage, company_bizno=biz_no, date_filter="2024.12")
        if review_response["status"] != "success":
            raise HTTPException(status_code=500, detail="리뷰 크롤링 실패")

        # 4. 뉴스 크롤링 수행
        news_response = get_company_news_api(company_name=company_name, num_articles=50)
        if news_response["status"] != "success":
            raise HTTPException(status_code=500, detail="뉴스 크롤링 실패")

        # 5. 복지 크롤링 수행
        welfare_response = get_company_welfare_api(company_name=company_name)
        if welfare_response["status"] != "success":
            raise HTTPException(status_code=500, detail="복지 크롤링 실패")

        # 6. 회사 정보 데이터베이스 조회
        collection = connect_to_mongo("culture_db", "company")
        if collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        company_data = collection.find_one({"biz_no": biz_no})

        if company_data is None:
            return CompanyResponse(
                company_id=biz_no,
                company_name=company_name,
                biz_no=biz_no,
                homepage=homepage,
                status="error"
            )

        return CompanyResponse(
            company_id=company_data['_id'],
            company_name=company_data.get("company_name", company_name),
            biz_no=company_data.get("biz_no", biz_no),
            homepage=company_data.get("homepage", homepage),
            status="success"
        )

    except Exception as e:
        logger.error(f"회사 등록 중 오류 발생: {repr(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"회사 등록 중 오류 발생: {repr(e)}"
        )
    

@router.get("/get_company_news", response_model=CompanyNewsResponse)
async def get_company_news(biz_no: str, company_name: Optional[str] = None):
    """
    사업자 번호로 기업을 조회하고, 해당 기업의 뉴스 데이터를 반환하는 API
    """
    company_collection = connect_to_mongo("culture_db", "company")
    news_collection = connect_to_mongo("culture_db", "company_news")

    # company_news에서 특정 회사의 모든 데이터 확인
    # for doc in news_collection.find({"company": "코리아교육그룹"}):
    #     print(doc)

    # 1. 사업자 번호를 기반으로 기업 조회
    query = {"biz_no": biz_no}
    if company_name:
        query["company_name"] = company_name
    
    company_data = company_collection.find_one(query)
    if not company_data:
        raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")
    logger.info(f"company_id: {company_data['_id']}, company_name: {company_data['company_name']}, biz_no: {company_data['biz_no']}")
    
    # news_data = news_collection.find_one({"company_id": company_data["_id"]})
    news_data = news_collection.find_one({"company_id": str(company_data["_id"])})

    if not news_data:
        raise HTTPException(status_code=404, detail="해당 기업의 기사를 찾을 수 없음")
    
    response_data = CompanyNewsResponse(
        company_id=str(company_data["_id"]),
        company_name=company_data["company_name"],
        biz_no=company_data["biz_no"],
        collected_date=news_data.get("collected_date", ""),
        updated_date=news_data.get("updated_date", ""),
        news=[
            NewsItem(
                title=item["title"],
                url=item["url"],
                page_text=item.get("page_text", "")
            )
            for item in news_data.get("news_data", [])
        ]
    )

    return response_data


@router.get("/get_company_reviews", response_model=CompanyReviewResponse)
async def get_company_reviews(
    biz_no: str = Query(..., description="사업자 번호 (필수)"),
    company_name: Optional[str] = Query(None, description="회사명 (선택)")
):
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
        
        company_id = str(company_data["_id"])
        logger.info(f"company_id: {company_id}, company_name: {company_data['company_name']}, biz_no: {company_data['biz_no']}")
        
        # 2. company_review 컬렉션에서 해당 기업의 리뷰 조회
        review_data = review_collection.find_one({"company_id": company_id})
        if not review_data:
            raise HTTPException(status_code=404, detail="해당 기업의 리뷰를 찾을 수 없음")

        return {
            "company_id": company_id,
            "company_name": company_data["company_name"],
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
    

@router.post("/get_company_total_data", response_model=CompanyTotalData)
async def get_company_total_data(biz_no: str, company_name: Optional[str] = None):
    try:
        company_collection = connect_to_mongo("culture_db", "company")
        company_page_collection = connect_to_mongo("culture_db", "company_page")
        company_review_collection = connect_to_mongo("culture_db", "company_review")
        company_news_collection = connect_to_mongo("culture_db", "company_news")
        company_welfare_collection = connect_to_mongo("culture_db", "company_welfare")

        query = {"biz_no": biz_no}
        if company_name:
            query["company_name"] = company_name
        
        company_data = company_collection.find_one(query)
        if not company_data:
            raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")

        company_id = str(company_data["_id"])  # ✅ ObjectId -> 문자열 변환

        # MongoDB 조회 결과를 변환하여 `_id` 필드를 문자열로 처리
        company_page_data = convert_objectid_to_str(company_page_collection.find_one({"company_id": company_id}))
        company_review_data = convert_objectid_to_str(company_review_collection.find_one({"company_id": company_id}))
        company_news_data = convert_objectid_to_str(company_news_collection.find_one({"company_id": company_id}))
        company_welfare_data = convert_objectid_to_str(company_welfare_collection.find_one({"company_id": company_id}))

        return jsonable_encoder({
            "company_id": company_id,  # ✅ 문자열 변환된 company_id
            "company_name": company_data["company_name"],
            "biz_no": company_data["biz_no"],
            "page_data": company_page_data,
            "review_data": company_review_data,
            "news_data": company_news_data,
            "welfare_data": company_welfare_data
        })

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"회사 전체 데이터 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 전체 데이터 조회 중 오류 발생: {str(e)}")