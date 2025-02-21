from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CompanyName(BaseModel):
    company_name: str


class UpdateCompany(BaseModel):
    company_name: str
    company_url: str


class DeleteCompany(BaseModel):
    company_name: str


class SearchPage(BaseModel):
    company_name: str
    target_url: str


class AddNewPage(BaseModel):
    company_name: str
    url: str
    text: str


class UpdatePage(BaseModel):
    company_name: str
    target_url: str
    new_url: Optional[str] = None
    new_text: Optional[str] = None


class DeletePage(BaseModel):
    company_name: str
    target_url: str


class BizNoList(BaseModel):
    biz_no_list: List[str]


class CompanyInfo(BaseModel):
    company_id: Optional[str] = None
    biz_no: Optional[str] = None
    company_name: Optional[str] = None
    company_url: Optional[str] = None
    eda_status: Optional[str] = None


class CompaniesResponse(BaseModel):
    data: List[CompanyInfo]    


class CompanyRegisterRequest(BaseModel):
    company_name: str = Field(..., example="코리아교육그룹")
    biz_no: str = Field(..., example="214-87-88737")
    homepage_url: Optional[str] = Field(None, example=None)
    max_pages: Optional[int] = Field(5, example=5)
    num_articles: Optional[int] = Field(1, example=1)
    date_filter: Optional[str] = Field("2024.12", example="2024.12")


class CompanyResponse(BaseModel):
    company_id: str
    company_name: str
    biz_no: str
    homepage: Optional[str]
    eda_status: str


class NewsItem(BaseModel):
    title: str
    url: str
    page_text: str


class CompanyNewsResponse(BaseModel):
    company_id: str
    company_name: str
    biz_no: str
    collected_date: Optional[str] = None
    updated_date: Optional[str] = None
    news: List[NewsItem]


class CompanyReview(BaseModel):
    """개별 리뷰 데이터 모델"""
    position: str = Field(
        description="직무 포지션",
        example="개발"
    )
    employ_status: str = Field(
        description="재직 상태",
        example="현직원"
    )
    working_area: str = Field(
        description="근무 지역",
        example="서울"
    )
    review_date: str = Field(
        description="리뷰 작성일",
        example="2024.12"
    )
    rate: str = Field(
        description="평점",
        example="4.0"
    )
    title: str = Field(
        description="리뷰 제목",
        example="워라밸은 좋지만 일적으로 배울 것은 없음"
    )
    positive: str = Field(
        description="장점",
        example="일 없으면 30분 일찍 퇴근, 근무 중 20분 쉬는 시간이 있음"
    )
    negative: str = Field(
        description="단점",
        example="특정 부서 막무가내식 업무 요청이 잦음"
    )
    expectation: str = Field(
        description="바라는 점",
        example="업무에 집중할 수 있게 해줬음 좋겠습니다"
    )


class CompanyReviewResponse(BaseModel):
    """회사 리뷰 응답 모델"""
    company_id: str = Field(
        description="회사 ID",
        example="666666666666666666666666"
    )
    company_name: str = Field(
        description="회사명",
        example="코리아교육그룹"
    )
    biz_no: str = Field(
        description="사업자 번호",
        example="214-87-88737"
    )
    collected_date: str = Field(
        description="데이터 수집일",
        example="25.02.13-02:58:31"
    )
    updated_date: str = Field(
        description="데이터 갱신일",
        example="25.02.13-02:58:31"
    )
    review_data: List[CompanyReview] = Field(
        description="리뷰 데이터 목록",
        default=[]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "666666666666666666666666",
                "company_name": "코리아교육그룹",
                "biz_no": "214-87-88737",
                "collected_date": "25.02.13-02:58:31",
                "updated_date": "25.02.13-02:58:31",
                "review_data": [
                    {
                        "position": "개발",
                        "employ_status": "현직원",
                        "working_area": "서울",
                        "review_date": "2024.12",
                        "rate": "4.0",
                        "title": "워라밸은 좋지만 일적으로 배울 것은 없음",
                        "positive": "일 없으면 30분 일찍 퇴근, 근무 중 20분 쉬는 시간이 있음",
                        "negative": "특정 부서 막무가내식 업무 요청이 잦음",
                        "expectation": "업무에 집중할 수 있게 해줬음 좋겠습니다"
                    }
                ]
            }
        }


class PageData(BaseModel):
    url: str
    text: str


class HomepageData(BaseModel):
    company_id: str
    collected_date: str
    company_name: str
    pages: List[PageData]
    updated_date: Optional[str]


class ReviewDataItem(BaseModel):
    position: Optional[str]
    employ_status: Optional[str]
    working_area: Optional[str]
    review_date: Optional[str]
    rate: Optional[str]
    title: Optional[str]
    positive: Optional[str]
    negative: Optional[str]
    expectation: Optional[str]


class ReviewData(BaseModel):
    company_id: str
    company_name: str
    collected_date: str
    platform: str
    jobplanet_id: Optional[int]
    review_data: List[ReviewDataItem]
    updated_date: Optional[str] = None


class NewsDataItem(BaseModel):
    title: str
    url: str
    page_text: Optional[str]


class NewsData(BaseModel):
    company_id: str
    company_name: str
    collected_date: str
    news_data: List[NewsDataItem]
    updated_date: Optional[str] = None


class WelfareItem(BaseModel):
    source: str
    data: Optional[Dict[str, Any]] = None  # ✅ 기존 welfare_data -> data로 변경


class WelfareData(BaseModel):
    company_id: str
    company_name: Optional[str]  # ✅ 일부 데이터에서 company_name이 없을 가능성 고려
    collected_date: str
    welfare_data: List[WelfareItem]  # ✅ 리스트로 감싸는 것은 유지
    updated_date: Optional[str] = None


class CompanyTotalData(BaseModel):
    company_id: str
    company_name: str
    company_url: Optional[str] = None  # 필수 필드에서 선택적 필드로 변경
    biz_no: str
    homepage_data: Optional[HomepageData]
    review_data: Optional[ReviewData]
    # news_data: Optional[NewsData]
    welfare_data: Optional[WelfareData]


class CompanyVisionAnalysisRequest(BaseModel):
    biz_no: str
    query: Optional[str] = None
    documents: Optional[List[str]] = []


# 비전 분석 요청에 대한 응답 모델
class CompanyVisionAnalysisResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태 (accepted)")
    message: str = Field(..., description="응답 메시지")
    id: Optional[str] = Field(None, description="생성된 분석 문서의 고유 ID")


# 개별 비전 항목 분석 결과 모델
class VisionItemAnalysis(BaseModel):
    code: str = Field(..., description="비전 항목 코드")
    score: float = Field(..., ge=1.0, le=5.0, description="평가 점수 (1.0-5.0)")
    summary: str = Field(..., description="평가 요약")


# 비전 분석 결과 조회 응답 모델
class VisionAnalysisResult(BaseModel):
    id: str = Field(..., description="문서 ID")
    company_id: str = Field(..., description="회사 ID")
    company_name: str = Field(..., description="회사명")
    biz_no: str = Field(..., description="사업자등록번호")
    date: datetime = Field(..., description="분석 일시")
    status: str = Field(..., description="분석 상태 (processing/completed/failed)")
    response: Optional[List[VisionItemAnalysis]] = Field(None, description="분석 결과")


# ID로 비전 분석 결과 조회 응답 모델
class VisionAnalysisByIdResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태")
    message: Optional[str] = Field(None, description="오류 메시지")
    data: Optional[List[VisionItemAnalysis]] = Field(None, description="분석 결과 데이터")


# 사업자번호로 비전 분석 결과 조회 응답 모델
class VisionAnalysisByBizNoResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태")
    message: Optional[str] = Field(None, description="오류 메시지")
    data: Optional[List[VisionAnalysisResult]] = Field(None, description="분석 결과 데이터 목록")


# Vision 분석 결과 참조 모델
class VisionResponseReference(BaseModel):
    response_id: str = Field(..., description="Vision 분석 결과의 ID")
    response: List[Dict[str, Any]] = Field(..., description="Vision 분석 결과 데이터")


# Workstyle 분석 요청 모델
class CompanyWorkstyleAnalysisRequest(BaseModel):
    biz_no: str
    query: Optional[str] = None
    documents: Optional[List[str]] = []


# Workstyle 분석 요청에 대한 응답 모델
class CompanyWorkstyleAnalysisResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태 (accepted)")
    message: str = Field(..., description="응답 메시지")
    id: Optional[str] = Field(None, description="생성된 분석 문서의 고유 ID")


# Workstyle 분석 결과 모델
class WorkstyleAnalysisResult(BaseModel):
    id: str = Field(..., description="문서 ID")
    company_id: str = Field(..., description="회사 ID")
    company_name: str = Field(..., description="회사명")
    biz_no: str = Field(..., description="사업자등록번호")
    date: datetime = Field(..., description="분석 일시")
    status: str = Field(..., description="분석 상태 (processing/completed/failed)")
    vision_response: VisionResponseReference = Field(..., description="참조된 Vision 분석 결과")
    response: Optional[Dict[str, Any]] = Field(None, description="Workstyle 분석 결과")


# ID로 Workstyle 분석 결과 조회 응답 모델
class WorkstyleAnalysisByIdResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태")
    message: Optional[str] = Field(None, description="오류 메시지")
    data: List[Dict[str, Any]] = Field(..., description="분석 결과 데이터 리스트")



# 사업자번호로 Workstyle 분석 결과 조회 응답 모델
class WorkstyleAnalysisByBizNoResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태")
    message: Optional[str] = Field(None, description="오류 메시지")
    data: List[Dict[str, Any]] = Field(..., description="분석 결과 데이터 리스트")


class CompanyTurnoverAnalysisRequest(BaseModel):
    biz_no: str
    query: Optional[str] = None
    documents: Optional[List[str]] = []


class CompanyTurnoverAnalysisResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태 (accepted)")
    message: str = Field(..., description="응답 메시지")
    id: Optional[str] = Field(None, description="생성된 분석 문서의 고유 ID")


class TurnoverAnalysisResult(BaseModel):
    id: str = Field(..., description="문서 ID")
    company_id: str = Field(..., description="회사 ID")
    company_name: str = Field(..., description="회사명")
    biz_no: str = Field(..., description="사업자등록번호")
    date: datetime = Field(..., description="분석 일시")
    status: str = Field(..., description="분석 상태 (processing/completed/failed)")
    response: Optional[Dict[str, Any]] = Field(None, description="Turnover 분석 결과")


class TurnoverAnalysisByIdResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태")
    message: Optional[str] = Field(None, description="오류 메시지")
    data: List[Dict[str, Any]] = Field(..., description="분석 결과 데이터 리스트")


class TurnoverAnalysisByBizNoResponse(BaseModel):
    status: str = Field(..., description="요청 처리 상태")
    message: Optional[str] = Field(None, description="오류 메시지")
    data: List[Dict[str, Any]] = Field(..., description="분석 결과 데이터 리스트")