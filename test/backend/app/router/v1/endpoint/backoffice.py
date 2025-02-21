import httpx

from typing import Optional, List
from fastapi import APIRouter, Request, Query, Path

from app.schemas.v1.db_schemas import (
    CompanyInfo, 
    CompanyNewsResponse, 
    CompanyReviewResponse, 
    NewsItem,
    CompanyTotalData,
    CompanyResponse,
    CompanyRegisterRequest,
    
    CompanyVisionAnalysisRequest,
    CompanyVisionAnalysisResponse,
    VisionAnalysisByIdResponse,
    VisionAnalysisByBizNoResponse,

    CompanyWorkstyleAnalysisRequest,
    CompanyWorkstyleAnalysisResponse,
    WorkstyleAnalysisByIdResponse,
    WorkstyleAnalysisByBizNoResponse,

    CompanyTurnoverAnalysisRequest,
    CompanyTurnoverAnalysisResponse,
    TurnoverAnalysisByIdResponse,
    TurnoverAnalysisByBizNoResponse,
)
from app.utils.logging import logger

router = APIRouter()

async def forward_request(request: Request, endpoint: str, params: dict, method: str = "get"):
    """서버2로 요청을 전달하는 헬퍼 함수"""
    base_url = f"{request.app.state.cfg['data_server']}/api/v1{endpoint}"
    logger.info(f"base_url: {base_url}")
    
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


@router.get("/backoffice/company/search", response_model=List[CompanyInfo])
async def companies_biz_nums_api(
    request: Request, 
    biz_no_list: List[str] = Query(..., description="사업자번호 목록")
):
    """사업자 번호 리스트로 회사 정보를 조회하는 API"""
    logger.info("### 서버2로 회사 검색 요청 전달")

    # 입력된 사업자 번호 전처리 (하이픈 제거, 공백 제거)
    biz_nos = [biz_no.strip().replace("-", "") for biz_no in biz_no_list]
    formatted_biz_nos = [f"{biz_no[:3]}-{biz_no[3:5]}-{biz_no[5:]}" for biz_no in biz_nos]

    params = {"biz_no_list": formatted_biz_nos}
    
    try:
        response = await forward_request(request, "/backoffice_worker/company/search", params, method="get")
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and "data" in response:
            return response["data"]
        return []
        
    except Exception as e:
        logger.error(f"회사 검색 중 오류 발생: {str(e)}")
        return []


@router.post("/backoffice/company/register", response_model=CompanyResponse)
async def company_register_api(
    request: Request,
    company_data: CompanyRegisterRequest
):
    logger.info("### 서버2로 회사 등록 요청 전달")
    
    # company_data를 딕셔너리로 변환
    params = company_data.model_dump()

    # HTTP 메서드를 "post"로 forward
    return await forward_request(request, "/backoffice_worker/company/register", params, method="post")


@router.get("/backoffice/company/news/{biz_no}", response_model=CompanyNewsResponse)
async def company_news(
    request: Request, 
    biz_no: str = Path(..., description="사업자번호 (필수)"),  # 변경: Query -> Path
    company_name: Optional[str] = Query(None, description="회사명 (선택)")
):
    """사업자 번호로 기업의 뉴스 데이터를 조회하는 API"""
    logger.info("### 서버2로 뉴스 조회 요청 전달")
    params = {"biz_no": biz_no}
    if company_name:
        params["company_name"] = company_name

    return await forward_request(request, "/backoffice_worker/company/news", params)


@router.get("/backoffice/company/reviews/{biz_no}", response_model=CompanyReviewResponse)
async def company_reviews(
    request: Request,
    biz_no: str = Path(..., description="사업자번호 (필수)"),  # 변경: Query -> Path
    company_name: Optional[str] = Query(None, description="회사명 (선택)")
):
    """사업자 번호로 기업의 리뷰 데이터를 조회하는 API"""
    logger.info("### 서버2로 리뷰 조회 요청 전달")
    params = {"biz_no": biz_no}
    if company_name:
        params["company_name"] = company_name

    return await forward_request(request, "/backoffice_worker/company/reviews", params)


@router.get("/backoffice/company/dataset/{biz_no}", response_model=CompanyTotalData)
async def company_total_data(
    request: Request, 
    biz_no: str = Path(..., description="사업자번호 (필수)"),  # 변경: Query -> Path
    company_name: Optional[str] = Query(None, description="회사명 (선택)")
):
    """사업자 번호로 기업의 전체 데이터를 조회하는 API"""
    logger.info("### 서버2로 전체 데이터 조회 요청 전달")
    params = {"biz_no": biz_no}
    if company_name:
        params["company_name"] = company_name
    
    return await forward_request(request, "/backoffice_worker/company/dataset", params)


@router.post("/backoffice/company/analysis/vision")
async def company_vision_analysis(request: Request, company_data: CompanyVisionAnalysisRequest):
    """
    기업 비전 분석.
    - 사업자 번호로 기업 분석
    - 비전 항목 분석 후 반환.(항목별로 score, summary 반환)
    """
    logger.info("### 서버2로 회사 분석 요청 전달")
    params = company_data.model_dump()

    return await forward_request(request, "/backoffice_worker/company/analysis/vision", params, method="post")


@router.get("/backoffice/company/analysis/vision/id/{id}", response_model=VisionAnalysisByIdResponse)
async def company_vision_analysis_by_id(
    request: Request, 
    id: str = Path(..., description="company_vision 컬렉션의 _id")
):
    """
    company_vision 컬렉션에서 _id를 통해 vision 결과 분석을 반환 받음.
    """
    logger.info("### 서버2로 비전 분석 요청 전달")
    params = {"id": id}
    return await forward_request(request, f"/backoffice_worker/company/analysis/vision/id/{id}", params, method="get")


@router.get("/backoffice/company/analysis/vision/biz_no/{biz_no}", response_model=VisionAnalysisByBizNoResponse)
async def company_vision_analysis_by_biz_no(
    request: Request, 
    biz_no: str = Path(..., description="사업자번호 (필수)")
):
    """
    company_vision 컬렉션에서 biz_no를 통해 vision 결과 분석을 반환 받음.
    """
    logger.info("### 서버2로 비전 분석 요청 전달")
    params = {"biz_no": biz_no}
    return await forward_request(request, f"/backoffice_worker/company/analysis/vision/biz_no/{biz_no}", params, method="get")


@router.post("/backoffice/company/analysis/workstyle", response_model=CompanyWorkstyleAnalysisResponse)
async def company_workstyle_analysis(request: Request, company_data: CompanyWorkstyleAnalysisRequest):
    """
    기업 업무 스타일 분석.
    - 사업자 번호로 기업 분석
    - 워크스타일 항목 분석 후 반환.(항목별로 score, summary 반환)
    """
    logger.info("### 서버2로 회사 분석 요청 전달")
    params = company_data.model_dump()

    return await forward_request(request, "/backoffice_worker/company/analysis/workstyle", params, method="post")


@router.get("/backoffice/company/analysis/workstyle/id/{id}", response_model=WorkstyleAnalysisByIdResponse)
async def company_workstyle_analysis_by_id(
    request: Request, 
    id: str = Path(..., description="company_workstyle 컬렉션의 _id")
):
    """
    company_workstyle 컬렉션에서 _id를 통해 workstyle 결과 분석을 반환 받음.
    """
    logger.info("### 서버2로 비전 분석 요청 전달")
    params = {"id": id}
    return await forward_request(request, f"/backoffice_worker/company/analysis/workstyle/id/{id}", params, method="get")


@router.get("/backoffice/company/analysis/workstyle/biz_no/{biz_no}", response_model=WorkstyleAnalysisByBizNoResponse)
async def company_workstyle_analysis_by_biz_no(
    request: Request, 
    biz_no: str = Path(..., description="사업자번호 (필수)")
):
    """
    company_workstyle 컬렉션에서 biz_no를 통해 workstyle 결과 분석을 반환 받음.
    """
    logger.info("### 서버2로 비전 분석 요청 전달")
    params = {"biz_no": biz_no}
    return await forward_request(request, f"/backoffice_worker/company/analysis/workstyle/biz_no/{biz_no}", params, method="get")


@router.post("/backoffice/company/analysis/turnover", response_model=CompanyTurnoverAnalysisResponse)
async def company_turnover_analysis(request: Request, company_data: CompanyTurnoverAnalysisRequest):
    """
    기업 재직예측요인 분석.
    - 사업자 번호로 기업 분석
    - 재직예측요인 분석 후 반환.(항목별로 score, summary 반환)
    """
    logger.info("### 서버2로 회사 분석 요청 전달")
    params = company_data.model_dump()

    return await forward_request(request, "/backoffice_worker/company/analysis/turnover", params, method="post")


@router.get("/backoffice/company/analysis/turnover/id/{id}", response_model=TurnoverAnalysisByIdResponse)
async def company_turnover_analysis_by_id(
    request: Request, 
    id: str = Path(..., description="company_turnover 컬렉션의 _id")
):
    """
    company_turnover 컬렉션에서 _id를 통해 turnover 결과 분석을 반환 받음.
    """
    logger.info("### 서버2로 비전 분석 요청 전달")
    params = {"id": id}
    return await forward_request(request, f"/backoffice_worker/company/analysis/turnover/id/{id}", params, method="get")


@router.get("/backoffice/company/analysis/turnover/biz_no/{biz_no}", response_model=TurnoverAnalysisByBizNoResponse)
async def company_turnover_analysis_by_biz_no(
    request: Request, 
    biz_no: str = Path(..., description="사업자번호 (필수)")
):
    """
    company_turnover 컬렉션에서 biz_no를 통해 turnover 결과 분석을 반환 받음.
    """
    logger.info("### 서버2로 비전 분석 요청 전달")
    params = {"biz_no": biz_no}
    return await forward_request(request, f"/backoffice_worker/company/analysis/turnover/biz_no/{biz_no}", params, method="get")