from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CompanyName(BaseModel):
    company_name: str


class UpdateCompany(BaseModel):
    company_name: str
    root_url: str


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
    biz_no: str
    company_name: str
    homepage: Optional[str] = None
    status: str  # "active" 또는 "inactive"


class CompaniesResponse(BaseModel):
    status: str
    data: List[CompanyInfo]    


class CompanyRegistration(BaseModel):
    biz_no: str
    company_name: Optional[str] = None
    homepage: Optional[str] = None


class CompanyResponse(BaseModel):
    company_id: str
    company_name: str
    biz_no: str
    homepage: Optional[str]
    status: str


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
    _id: str
    company: str
    collected_date: str
    company_id: str
    jobplanet_id: Optional[int]
    platform: str
    review_data: List[ReviewDataItem]
    root_url: Optional[str]
    updated_date: str


class NewsDataItem(BaseModel):
    title: str
    url: str
    page_text: Optional[str]


class NewsData(BaseModel):
    _id: str
    company: str
    collected_date: str
    company_id: str
    news_data: List[NewsDataItem]
    updated_date: str


class WelfareItem(BaseModel):
    source: str
    welfare_data: Dict[str, Any]  # 다양한 형태의 데이터를 허용


class WelfareData(BaseModel):
    _id: str
    company: str
    collected_date: str
    company_id: str
    welfare_data: List[WelfareItem]
    updated_date: str


class CompanyTotalData(BaseModel):
    company_id: str
    company_name: str
    biz_no: str
    page_data: Optional[Dict[str, Any]]  # Null 가능
    review_data: Optional[ReviewData]
    news_data: Optional[NewsData]
    welfare_data: Optional[WelfareData]
