import asyncio
import traceback

from datetime import datetime
from bson.objectid import ObjectId
from typing import Optional, List, Dict, Any
from fastapi.encoders import jsonable_encoder
from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter, HTTPException, Request, Query, Body, BackgroundTasks

from src.db.mongo import connect_to_mongo, async_mongo_client
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
from src.crawler.utils.data_utils import format_business_number
from src.culture.vision.analysis import company_vision_analysis
from src.culture.workstyle.analysis import company_workstyle_analysis
from src.culture.turnover.analysis import company_turnover_analysis
from src.db.mongo import (
    save_to_mongo, 
    connect_to_mongo, 
    get_or_create_company, 
    convert_objectid_to_str,
    get_company 
)

from app.utils.task_manager import TaskManager
from app.utils.logging import logger

from app.router.v1.endpoint.crawler_worker import (
    get_company_info_api,
    get_company_homepage_api,
    get_company_review_api,
    get_company_news_api,
    get_company_welfare_api
)

router = APIRouter()

# TaskManager 인스턴스 생성
task_manager = TaskManager()

@router.get("/backoffice_worker/company/search", response_model=List[CompanyInfo])
async def search_companies_by_biz_no_api(
    biz_no_list: List[str] = Query(..., description="사업자번호 목록")
):
    try:
        collection = connect_to_mongo("culture_db", "company")
        if collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        ## 입력된 사업자번호를 MongoDB 저장 형식인 XXX-XX-XXXXX로 변환
        formatted_biz_nos = []
        for biz_no in biz_no_list:
            biz_no = biz_no.strip().replace("-", "")
            formatted_biz_nos.append(f"{biz_no[:3]}-{biz_no[3:5]}-{biz_no[5:]}")

        logger.info(f"Formatted business numbers for query: {formatted_biz_nos}")

        # MongoDB에서 회사 정보 조회
        projection = {
            "biz_no": 1,
            "company_name": 1,
            "homepage": 1,
            "eda_status": 1
        }
        
        found_companies = {}
        cursor = collection.find({"biz_no": {"$in": formatted_biz_nos}}, projection)
        for doc in cursor:
            found_companies[doc["biz_no"]] = doc
            # logger.info(f"Found company: {doc['biz_no']} - {doc.get('company_name', 'No name')}")

        # 조회된 데이터만 반환
        result = [
            CompanyInfo(
                company_id=str(doc["_id"]),
                biz_no=doc["biz_no"],
                company_name=doc.get("company_name", ""),
                company_url=doc.get("homepage", ""),
                eda_status=doc.get("eda_status", "")
            )
            for doc in found_companies.values()
        ]

        logger.info(f"Total companies found: {len(result)}")
        return result

    except Exception as e:
        logger.error(f"사업자 번호로 회사 검색 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사업자 번호로 회사 검색 중 오류 발생: {str(e)}"
        )

async def process_company_registration(company_id: str, company_data: CompanyRegisterRequest, request: Request):
    """실제 크롤링 작업을 수행하는 함수"""
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    company_collection = connect_to_mongo("culture_db", "company")
    
    try:
        # 크롤링 상태를 "crawling"으로 업데이트
        await asyncio.to_thread(
            company_collection.update_one,
            {"_id": ObjectId(company_id)},
            {"$set": {"eda_status": "crawling", "updated_at": datetime.utcnow()}}
        )

        ## 1. 회사 정보 자동 보완
        try:
            print("\n\n")
            logger.info("[company_info]")
            if company_data.homepage_url == "string":
                company_data.homepage_url = None

            info_response = await get_company_info_api(
                company_data.company_name,
                company_data.biz_no,
                company_data.homepage_url
            )
            
            if info_response["status"] == "success":
                collected_info = info_response["data"]
                update_fields = {
                    "company_name": collected_info.get("company_name", company_data.company_name),
                    "biz_no": collected_info.get("biz_no", company_data.biz_no),
                    "homepage": collected_info.get("homepage", company_data.homepage_url),
                    "eda_status": "crawling",
                    "alias_name": collected_info.get("alias_name"),
                    "business_type": collected_info.get("business_type"),
                    "phone_number": collected_info.get("phone_number"),
                    "fax_number": collected_info.get("fax_number"),
                    "enterprise_scale": collected_info.get("enterprise_scale"),
                    "business_entity": collected_info.get("business_entity"),
                    "ir_homepage": collected_info.get("ir_homepage"),
                    "ceo_name": collected_info.get("ceo_name"),
                    "corp_no": collected_info.get("corp_no"),
                    "postal_code": collected_info.get("postal_code"),
                    "address": collected_info.get("address"),
                    "updated_at": datetime.utcnow(),
                    "collected_date": datetime.utcnow()
                }
                await asyncio.to_thread(
                    company_collection.update_one,
                    {"_id": ObjectId(company_id)},
                    {"$set": update_fields}
                )
            else:
                raise Exception("기업정보 크롤링 실패")

        except Exception as e:
            await error_handler.handle_error(
                e,
                api_source="company_info_crawling",
                detail_message=f"{company_data.company_name} 기업정보 크롤링 중 오류 발생",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise

        # 비동기로 크롤링 작업 실행
        print("\n\n")
        logger.info("[company_homepage]")
        homepage_result = await get_company_homepage_api(
            request=request,
            company_name=collected_info.get("company_name", company_data.company_name),
            max_pages=company_data.max_pages
        )
        
        print("\n\n")
        logger.info("[company_review]")
        review_result = await get_company_review_api(
            company_name=collected_info.get("company_name", company_data.company_name),
            company_url=collected_info.get("homepage", company_data.homepage_url),
            company_bizno=collected_info.get("biz_no", company_data.biz_no),
            date_filter=company_data.date_filter
        )
        
        print("\n\n")
        logger.info("[company_welfare]")
        welfare_result = await get_company_welfare_api(
            company_name=collected_info.get("company_name", company_data.company_name),
            company_url=collected_info.get("homepage", company_data.homepage_url),
            company_bizno=collected_info.get("biz_no", company_data.biz_no)
        )

        # print("\n\n")
        # logger.info(f"[company_news]")
        # news_result = await get_company_news_api(
        #     request=request,
        #     company_name=collected_info.get("company_name", company_data.company_name),
        #     num_articles=company_data.num_articles
        # )


        results = [homepage_result, review_result, welfare_result]
        success = all(isinstance(r, dict) and r.get("status") == "success" for r in results)
        
        # 최종 상태 업데이트
        await asyncio.to_thread(
            company_collection.update_one,
            {"_id": ObjectId(company_id)},
            {"$set": {
                "eda_status": "completed" if success else "partially_completed",
                "updated_at": datetime.utcnow(),
                "crawling_results": {
                    "homepage": homepage_result,
                    "review": review_result,
                    "welfare": welfare_result,
                    # "news": news_result
                }
            }}
        )

        return {
            "status": "success" if success else "partial_success",
            "company_id": company_id,
            "data": {
                "homepage": homepage_result,
                "review": review_result,
                "welfare": welfare_result,
                # "news": news_result
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사 비전 분석 중 오류 발생: {str(e)}")
        await error_handler.handle_error(
            e,
            api_source="vision_analysis",
            detail_message=f"회사 비전 분석 API 호출 중 오류 발생",
            request=request,
            alert=True,
            error_url=request_url
        )
        raise HTTPException(status_code=500, detail=f"회사 비전 분석 중 오류 발생: {str(e)}")

async def process_background_crawling(task_id: str, company_id: str, company_data: CompanyRegisterRequest, request: Request):
    """백그라운드에서 실행될 크롤링 작업"""
    company_collection = connect_to_mongo("culture_db", "company")
    
    try:
        # blocking DB 업데이트도 to_thread로 오프로드
        await asyncio.to_thread(
            company_collection.update_one,
            {"_id": ObjectId(company_id)},
            {"$set": {"eda_status": "crawling", "updated_at": datetime.utcnow()}}
        )

        # 크롤링 작업 실행
        result = await process_company_registration(company_id, company_data, request)

        # 크롤링 결과에 따라 상태 업데이트
        if result and result.get("status") == "success":
            crawling_data = result.get("data", {})
            all_responses = [
                crawling_data.get("homepage", {}),
                crawling_data.get("review", {}),
                crawling_data.get("welfare", {})
            ]
            all_have_status = all(
                isinstance(response, dict) and "status" in response
                for response in all_responses
            )
            
            if all_have_status:
                all_success = all(
                    response.get("status") == "success"
                    for response in all_responses
                )
                update_data = {
                    "eda_status": "completed" if all_success else "not_available",
                    "crawling_result": crawling_data,
                    "updated_at": datetime.utcnow()
                }
                failed_items = [
                    item_name
                    for item_name, response in [
                        ("homepage", crawling_data.get("homepage", {})),
                        ("review", crawling_data.get("review", {})),
                        ("welfare", crawling_data.get("welfare", {}))
                    ]
                    if response.get("status") != "success"
                ]
                if failed_items:
                    update_data["failed_items"] = failed_items
                    update_data["error_message"] = f"Failed to crawl: {', '.join(failed_items)}"
            else:
                update_data = {
                    "eda_status": "crawling",
                    "updated_at": datetime.utcnow()
                }
        else:
            update_data = {
                "eda_status": "failed_execution",
                "error_message": str(result.get("error", "Unknown error")),
                "updated_at": datetime.utcnow()
            }

        await asyncio.to_thread(
            company_collection.update_one,
            {"_id": ObjectId(company_id)},
            {"$set": update_data}
        )

        logger.info(f"Company {company_id} crawling status: {update_data['eda_status']}")
        if update_data['eda_status'] not in ["completed", "crawling"]:
            logger.warning(f"Crawling issues for company {company_id}: {update_data.get('error_message', 'No error message')}")
        return result

    except Exception as e:
        logger.error(f"백그라운드 크롤링 작업 중 오류 발생: {str(e)}")
        await asyncio.to_thread(
            company_collection.update_one,
            {"_id": ObjectId(company_id)},
            {"$set": {
                "eda_status": "failed_execution",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )
        raise

@router.post("/backoffice_worker/company/register", response_model=CompanyResponse)
async def register_company_api(
    request: Request,
    company_data: CompanyRegisterRequest = Body(...)
):
    try:
        company_collection = connect_to_mongo("culture_db", "company")
        if company_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        # blocking insert도 to_thread로 오프로드
        initial_company_doc = {
            "company_name": company_data.company_name,
            "biz_no": format_business_number(company_data.biz_no),
            "homepage": company_data.homepage_url,
            "eda_status": "pending",
            "updated_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        result = await asyncio.to_thread(company_collection.insert_one, initial_company_doc)
        company_id = str(result.inserted_id)

        task_id = await task_manager.create_task(company_data.company_name)
        task_manager.tasks[task_id].update({
            "company_id": company_id,
            "biz_no": company_data.biz_no
        })

        # 백그라운드 작업 등록: await 대신 asyncio.create_task로 실행하여 바로 응답 반환
        asyncio.create_task(
            task_manager.add_task_to_queue(
                task_id=task_id,
                crawling_function=process_background_crawling,  # 함수 직접 전달
                company_id=company_id,
                company_data=company_data,
                request=request
            )
        )
        
        return {
            "company_id": company_id,
            "company_name": company_data.company_name,
            "biz_no": format_business_number(company_data.biz_no),
            "homepage": company_data.homepage_url,
            "eda_status": "pending"
        }
        
    except Exception as e:
        error_handler = request.app.state.error_handler
        await error_handler.handle_error(
            error=e,
            api_source="company_register",
            detail_message=f"{company_data.company_name} 등록 요청 처리 중 오류 발생.",
            request=request,
            alert=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"회사 등록 요청 처리 중 오류 발생: {repr(e)}"
        )


@router.get("/backoffice_worker/company/news", response_model=CompanyNewsResponse)
async def get_company_news(biz_no: str, company_name: Optional[str] = None):
    company_collection = connect_to_mongo("culture_db", "company")
    news_collection = connect_to_mongo("culture_db", "company_news")

    formatted_biz_no = format_business_number(biz_no)
    query = {"biz_no": formatted_biz_no}
    if company_name:
        query["company_name"] = company_name
    
    company_data = company_collection.find_one(query)
    if not company_data:
        raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")
    logger.info(f"company_id: {company_data['_id']}, company_name: {company_data['company_name']}, biz_no: {company_data['biz_no']}")
    
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


@router.get("/backoffice_worker/company/reviews", response_model=CompanyReviewResponse)
async def get_company_reviews(
    biz_no: str = Query(..., description="사업자 번호 (필수)"),
    company_name: Optional[str] = Query(None, description="회사명 (선택)")
):
    try:
        company_collection = connect_to_mongo("culture_db", "company")
        review_collection = connect_to_mongo("culture_db", "company_review")
        
        if company_collection is None or review_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB 연결 실패")

        formatted_biz_no = format_business_number(biz_no)
        query = {"biz_no": formatted_biz_no}
        if company_name:
            query["company_name"] = company_name
        
        company_data = company_collection.find_one(query)
        if not company_data:
            raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")
        
        company_id = str(company_data["_id"])
        logger.info(f"company_id: {company_id}, company_name: {company_data['company_name']}, biz_no: {company_data['biz_no']}")
        
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
    

@router.get("/backoffice_worker/company/dataset", response_model=CompanyTotalData)
async def get_company_total_data(biz_no: str, company_name: Optional[str] = None):
    try:
        formatted_biz_no = format_business_number(biz_no)
        company_collection = connect_to_mongo("culture_db", "company")
        company_homepage_collection = connect_to_mongo("culture_db", "company_homepage")
        company_review_collection = connect_to_mongo("culture_db", "company_review")
        # company_news_collection = connect_to_mongo("culture_db", "company_news")
        company_welfare_collection = connect_to_mongo("culture_db", "company_welfare")

        query = {"biz_no": formatted_biz_no}
        if company_name:
            query["company_name"] = company_name
        
        company_data = company_collection.find_one(query)
        if not company_data:
            raise HTTPException(status_code=404, detail="해당 사업자 번호의 기업을 찾을 수 없음")

        company_id = str(company_data["_id"])
        logger.info(f"company_id: {company_id}, company_name: {company_data['company_name']}, biz_no: {company_data['biz_no']}")

        company_homepage_data = convert_objectid_to_str(company_homepage_collection.find_one({"company_id": company_id}))
        company_review_data = convert_objectid_to_str(company_review_collection.find_one({"company_id": company_id}))
        # company_news_data = convert_objectid_to_str(company_news_collection.find_one({"company_id": company_id}))
        company_welfare_data = convert_objectid_to_str(company_welfare_collection.find_one({"company_id": company_id}))

        # 반환 데이터가 CompanyTotalData 모델과 일치하는지 확인
        return jsonable_encoder({
            "company_id": company_id,
            "company_name": company_data["company_name"],
            "company_url": company_data.get("homepage"),
            "biz_no": company_data["biz_no"],
            "homepage_data": company_homepage_data,
            "review_data": company_review_data,
            # "news_data": company_news_data,
            "welfare_data": company_welfare_data
        })

    except Exception as e:
        logger.error(f"회사 전체 데이터 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 전체 데이터 조회 중 오류 발생: {str(e)}")
    

# 백그라운드에서 실행할 분석 작업 함수
async def background_company_vision_analysis(
        request: Request,
        company_data: CompanyVisionAnalysisRequest,
        company_info: dict,
        inserted_id,
        collection):
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    
    try:
        # vector_store 접근 (비동기 처리 아님)
        vector_store = request.app.state.vector_store
        query = company_data.query if company_data.query else f"{company_info['company_name']}이 추구하는 비전, 미션 그리고 핵심가치는?"
        logger.info(f"[company_vision_analysis] RAG query: {query}")
        
        if not vector_store:
            error_msg = "vector_store 접근 실패"
            await error_handler.handle_error(
                Exception(error_msg),
                api_source="vision_analysis",
                detail_message=f"{company_info['company_name']} vector_store 접근 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise Exception(error_msg)
        
        try:
            # 만약 similarity_search_with_relevance_scores가 blocking 함수라면 run_in_threadpool 사용
            relevance_docs = await run_in_threadpool(vector_store.similarity_search_with_relevance_scores, query)
            logger.info(f"[company_vision_analysis] relevance_docs: {len(relevance_docs)}")
        except Exception as e:
            await error_handler.handle_error(
                api_source="vision_analysis",
                detail_message=f"{company_info['company_name']} 유사 문서 검색 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise
        
        # (document, score) 튜플에서 문서만 추출
        rag_docs = [doc[0] for doc in relevance_docs]
        user_docs = company_data.documents if company_data.documents else []
        total_docs = rag_docs + user_docs

        try:
            # company_vision_analysis가 비동기 함수라면 단순히 await 호출
            output = await company_vision_analysis(total_docs)
            logger.info(f"[company_vision_analysis] 분석 결과: {output}")
        except Exception as e:
            await error_handler.handle_error(
                api_source="vision_analysis",
                detail_message=f"{company_info['company_name']} 비전 분석 실행 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise
        
        # 분석 결과를 업데이트 (상태를 "completed"로 변경)
        await collection.update_one(
            {"_id": inserted_id},
            {"$set": {
                "request": output["request"],
                "response": output["response"],
                "status": "completed"
            }}
        )
        
    except Exception as e:
        logger.error(f"[company_vision_analysis] 오류 발생: {str(e)}")
        # 오류 발생 시 상태 업데이트
        await collection.update_one(
            {"_id": inserted_id},
            {"$set": {
                "status": "failed",
                "error": str(e)
            }}
        )
        await error_handler.handle_error(
            api_source="vision_analysis",
            detail_message=f"{company_info['company_name']} 비전 분석 전체 프로세스 실패",
            request=request,
            alert=True,
            error_url=request_url
        )

@router.post("/backoffice_worker/company/analysis/vision", response_model=CompanyVisionAnalysisResponse)
async def analyze_company_vision_api(background_tasks: BackgroundTasks, request: Request, company_data: CompanyVisionAnalysisRequest):
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    
    try:
        formatted_biz_no = format_business_number(company_data.biz_no)
        company_collection = async_mongo_client("culture_db", "company")
        
        company_info = await company_collection.find_one({"biz_no": formatted_biz_no})
        if not company_info:
            error_msg = "회사를 찾을 수 없음"
            await error_handler.handle_error(
                Exception(error_msg),
                api_source="vision_analysis",
                detail_message=f"사업자번호 {formatted_biz_no}에 해당하는 회사를 찾을 수 없음",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise HTTPException(status_code=404, detail=error_msg)
        
        company_id = str(company_info["_id"])
        logger.info(f"[vision_analysis] company_id: {company_id}, company_name: {company_info['company_name']}, biz_no: {company_info['biz_no']}")
                
        # 초기 상태를 "processing"으로 하여 company_vision 컬렉션에 저장
        vision_data = {
            "company_id": company_id,
            "company_name": company_info['company_name'],
            "biz_no": company_info['biz_no'],
            "date": datetime.utcnow(),
            "status": "processing"
        }
        
        collection = async_mongo_client("culture_db", "company_vision")
        insert_result = await collection.insert_one(vision_data)
        inserted_id = insert_result.inserted_id
        
        # BackgroundTasks에 등록하면 응답 후 백그라운드 작업 실행됨
        background_tasks.add_task(background_company_vision_analysis, request, company_data, company_info, inserted_id, collection)
        
        # 즉시 요청 접수 응답과 _id 반환
        return {
            "status": "accepted",
            "message": "회사 비전 분석 요청이 접수되었습니다. 분석 결과는 후속 업데이트를 확인해주세요.",
            "id": str(inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사 비전 분석 중 오류 발생: {str(e)}")
        await error_handler.handle_error(
            e,
            api_source="vision_analysis",
            detail_message=f"회사 비전 분석 API 호출 중 오류 발생",
            request=request,
            alert=True,
            error_url=request_url
        )
        raise HTTPException(status_code=500, detail=f"회사 비전 분석 중 오류 발생: {str(e)}")
    

@router.get("/backoffice_worker/company/analysis/vision/id/{id}", response_model=VisionAnalysisByIdResponse)
async def get_company_vision_analysis(id: str):
    collection = connect_to_mongo("culture_db", "company_vision")
    try:
        result = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        logger.error(f"ObjectId 변환 오류: {e}")
        return {"status": "failed", "message": "유효하지 않은 _id 형식입니다."}

    if not result:
        return {"status": "failed", "message": "해당 id의 데이터가 존재하지 않습니다.", "data": []}

    return {"status": "success", "message": "비전 분석 결과 조회 성공", "data": result.get('response')}


@router.get("/backoffice_worker/company/analysis/vision/biz_no/{biz_no}", response_model=VisionAnalysisByBizNoResponse)
async def get_company_vision_analysis_by_biz_no(biz_no: str):

    ## company_vision 컬렉션에서 사업자번호로 데이터 조회
    collection = connect_to_mongo("culture_db", "company_vision")
    formatted_biz_no = format_business_number(biz_no)
    results = list(collection.find({"biz_no": formatted_biz_no}))
    
    if not results:
        return {
            "status": "failed", 
            "message": "해당 사업자 번호의 데이터가 존재하지 않습니다.",
            "data": []
        }
    
    # MongoDB ObjectId 필드를 문자열로 변환
    for doc in results:
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
        if "company_id" in doc:
            doc["company_id"] = str(doc["company_id"])
    
    return {"status": "success", "message": "비전 분석 결과 조회 성공", "data": results}


async def background_company_workstyle_analysis(
        request: Request, 
        company_data: CompanyWorkstyleAnalysisRequest, 
        company_info: dict, 
        inserted_id, 
        collection,
        vision_response: List[Dict[str, Any]]
    ):
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    
    try:
        # vector_store 접근 (비동기 처리 아님)
        vector_store = request.app.state.vector_store
        query = company_data.query if company_data.query else f"{company_info['company_name']}의 업무 방식 또는 업무 스타일은?"
        logger.info(f"[company_workstyle_analysis] RAG query: {query}")
        
        if not vector_store:
            error_msg = "vector_store 접근 실패"
            await error_handler.handle_error(
                api_source="workstyle_analysis",
                detail_message=f"{company_info['company_name']} vector_store 접근 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise Exception(error_msg)
        
        try:
            # 만약 similarity_search_with_relevance_scores가 blocking 함수라면 run_in_threadpool 사용
            relevance_docs = await run_in_threadpool(vector_store.similarity_search_with_relevance_scores, query)
            logger.info(f"[company_workstyle_analysis] relevance_docs: {len(relevance_docs)}")
        except Exception as e:
            await error_handler.handle_error(
                api_source="workstyle_analysis",
                detail_message=f"{company_info['company_name']} 유사 문서 검색 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise
        
        # (document, score) 튜플에서 문서만 추출
        rag_docs = [doc[0] for doc in relevance_docs]
        user_docs = company_data.documents if company_data.documents else []
        total_docs = rag_docs + user_docs

        try:
            # company_workstyle_analysis가 vision_response도 필요하므로 추가
            output = await company_workstyle_analysis(total_docs, vision_response)  # ✅ 수정된 부분
            logger.info(f"[company_workstyle_analysis] 분석 결과: {output}")

        except Exception as e:
            await error_handler.handle_error(
                api_source="workstyle_analysis",
                detail_message=f"{company_info['company_name']} 워크스타일 분석 실행 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise
        
        # 분석 결과를 업데이트 (상태를 "completed"로 변경)
        await collection.update_one(
            {"_id": inserted_id},
            {"$set": {
                "request": output["request"],
                "response": output["response"],
                "status": "completed"
            }}
        )
        
    except Exception as e:
        logger.error(f"[company_workstyle_analysis] 오류 발생: {str(e)}")
        # 오류 발생 시 상태 업데이트
        await collection.update_one(
            {"id": inserted_id},
            {"$set": {
                "status": "failed",
                "error": str(e)
            }}
        )
        await error_handler.handle_error(
            api_source="workstyle_analysis",
            detail_message=f"{company_info['company_name']} 워크스타일 분석 전체 프로세스 실패",
            request=request,
            alert=True,
            error_url=request_url
        )


@router.post("/backoffice_worker/company/analysis/workstyle", response_model=CompanyWorkstyleAnalysisResponse)
async def analyze_company_workstyle_api(background_tasks: BackgroundTasks, request: Request, company_data: CompanyWorkstyleAnalysisRequest):
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    
    try:
        formatted_biz_no = format_business_number(company_data.biz_no)
        company_collection = async_mongo_client("culture_db", "company")
        
        ## biz_no로 회사 정보 조회
        company_info = await company_collection.find_one({"biz_no": formatted_biz_no})
        if not company_info:
            error_msg = "회사를 찾을 수 없음"
            await error_handler.handle_error(
                Exception(error_msg),
                api_source="workstyle_analysis",
                detail_message=f"사업자번호 {formatted_biz_no}에 해당하는 회사를 찾을 수 없음",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise HTTPException(status_code=404, detail=error_msg)
        
        ## company_id 추출
        company_id = str(company_info["_id"])
        logger.info(f"[workstyle_analysis] company_id: {company_id}, company_name: {company_info['company_name']}, biz_no: {company_info['biz_no']}")
                
        # 초기 상태를 "processing"으로 하여 company_workstyle 컬렉션에 저장
        workstyle_data = {
            "company_id": company_id,
            "company_name": company_info['company_name'],
            "biz_no": company_info['biz_no'],
            "date": datetime.utcnow(),
            "status": "processing"
        }

        ## 최신 회사 비전 데이터 조회 (await 추가)
        collection = async_mongo_client("culture_db", "company_vision")
        latest_vision_data = await collection.find_one({"company_id": company_id}, sort=[("date", -1)])  # ← await 추가

        if not latest_vision_data:
            raise HTTPException(status_code=404, detail="해당 회사의 비전 데이터가 존재하지 않습니다.")

        vision_response = latest_vision_data["response"]
        response_id = latest_vision_data["_id"]
        workstyle_data["vision_response"] = {
            "response_id": response_id,
            "response": vision_response
        }
        logger.info(f"[workstyle_analysis] vision_response: {response_id}, {vision_response}")
        
        collection = async_mongo_client("culture_db", "company_workstyle")
        insert_result = await collection.insert_one(workstyle_data)
        inserted_id = insert_result.inserted_id
        
        # BackgroundTasks에 등록하면 응답 후 백그라운드 작업 실행됨
        background_tasks.add_task(background_company_workstyle_analysis, request, company_data, company_info, inserted_id, collection, vision_response)
        
        # 즉시 요청 접수 응답과 id 반환
        return {
            "status": "accepted",
            "message": "회사 워크스타일 분석 요청이 접수되었습니다. 분석 결과는 후속 업데이트를 확인해주세요.",
            "id": str(inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사 워크스타일 분석 중 오류 발생: {str(e)}")
        await error_handler.handle_error(
            e,
            api_source="workstyle_analysis",
            detail_message=f"회사 워크스타일 분석 API 호출 중 오류 발생",
            request=request,
            alert=True,
            error_url=request_url
        )
        raise HTTPException(status_code=500, detail=f"회사 워크스타일 분석 중 오류 발생: {str(e)}")


@router.get("/backoffice_worker/company/analysis/workstyle/id/{id}", response_model=WorkstyleAnalysisByIdResponse)
async def get_company_workstyle_analysis(id: str):
    collection = connect_to_mongo("culture_db", "company_workstyle")

    try:
        object_id = ObjectId(id)

    except Exception as e:
        logger.error(f"ObjectId 변환 오류: {e}")
        raise HTTPException(status_code=400, detail="유효하지 않은 _id 형식입니다.")

    result = collection.find_one({"_id": object_id})
    if not result:
        return {"status": "failed", "message": "해당 id의 데이터가 존재하지 않습니다.", "data": []}

    result["_id"] = str(result["_id"])
    if "vision_response" in result and isinstance(result["vision_response"], dict):
        if "response_id" in result["vision_response"]:
            result["vision_response"]["response_id"] = str(result["vision_response"]["response_id"])

    response_data = result.get("response", [])
    return {"status": "success", "message": "워크스타일 분석 결과 조회 성공", "data": response_data}


@router.get("/backoffice_worker/company/analysis/workstyle/biz_no/{biz_no}", response_model=WorkstyleAnalysisByBizNoResponse)
async def get_company_workstyle_analysis_by_biz_no(biz_no: str):
    collection = connect_to_mongo("culture_db", "company_workstyle")
    formatted_biz_no = format_business_number(biz_no)
    
    try:
        results = list(collection.find({"biz_no": formatted_biz_no}))

        if not results:
            return {
                "status": "failed", 
                "message": "해당 사업자 번호의 데이터가 존재하지 않습니다.",
                "data": []
            }
        
        converted_results = convert_objectid_to_str(results)
        return {"status": "success", "message": "워크스타일 분석 결과 조회 성공", "data": converted_results}
    
    except Exception as e:
        logger.error(f"MongoDB 조회 오류: {e}")
        return {"status": "failed", "message": f"데이터 조회 중 오류가 발생했습니다. {str(e)}"}
    


# 백그라운드에서 실행할 분석 작업 함수
async def background_company_turnover_analysis(
        request: Request,
        company_data: CompanyTurnoverAnalysisRequest,
        company_info: dict,
        inserted_id,
        welfare_collection,
        review_collection,
        turnover_collection
    ):
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    
    try:
        ## 복지 정보 조회
        company_id = str(company_info["_id"])
        welfare_data = await welfare_collection.find_one({"company_id": company_id})
        if not welfare_data:
            error_msg = "회사 복지 정보를 찾을 수 없음"
            await error_handler.handle_error(
                Exception(error_msg),
                api_source="turnover_analysis",
                detail_message=f"{company_info['company_name']} 복지 정보를 찾을 수 없음",
                request=request,
                alert=True,
                error_url=request_url
            )

        logger.info(f"[company_turnover_analysis] welfare_data: {welfare_data}")

        ## 리뷰 정보 조회
        review_data = await review_collection.find_one({"company_id": company_id})
        if not review_data:
            error_msg = "회사 리뷰 정보를 찾을 수 없음"
            await error_handler.handle_error(
                Exception(error_msg),
                api_source="turnover_analysis",
                detail_message=f"{company_info['company_name']} 리뷰 정보를 찾을 수 없음",
                request=request,
                alert=True,
                error_url=request_url
            )

        logger.info(f"[company_turnover_analysis] review_data: {review_data}")

        try:
            output = await company_turnover_analysis(welfare_data, review_data)
            logger.info(f"[company_turnover_analysis] 분석 결과: {output}")
        except Exception as e:
            await error_handler.handle_error(
                api_source="vision_analysis",
                detail_message=f"{company_info['company_name']} 비전 분석 실행 실패",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise
        
        # 분석 결과를 업데이트 (상태를 "completed"로 변경)
        await turnover_collection.update_one(
            {"_id": inserted_id},
            {"$set": {
                "request": output["request"],
                "response": output["response"],
                "status": "completed"
            }}
        )
        
    except Exception as e:
        logger.error(f"[company_turnover_analysis] 오류 발생: {str(e)}")
        # 오류 발생 시 상태 업데이트
        await turnover_collection.update_one(
            {"_id": inserted_id},
            {"$set": {
                "status": "failed",
                "error": str(e)
            }}
        )
        await error_handler.handle_error(
            api_source="vision_analysis",
            detail_message=f"{company_info['company_name']} 비전 분석 전체 프로세스 실패",
            request=request,
            alert=True,
            error_url=request_url
        )
    

@router.post("/backoffice_worker/company/analysis/turnover", response_model=CompanyTurnoverAnalysisResponse)
async def analyze_company_turnover_api(background_tasks: BackgroundTasks, request: Request, company_data: CompanyTurnoverAnalysisRequest):
    error_handler = request.app.state.error_handler
    request_url = str(request.url)
    
    try:
        formatted_biz_no = format_business_number(company_data.biz_no)
        company_collection = async_mongo_client("culture_db", "company")

        ## biz_no로 회사 정보 조회
        company_info = await company_collection.find_one({"biz_no": formatted_biz_no})
        if not company_info:
            error_msg = "회사를 찾을 수 없음"
            await error_handler.handle_error(
                Exception(error_msg),
                api_source="vision_analysis",
                detail_message=f"사업자번호 {formatted_biz_no}에 해당하는 회사를 찾을 수 없음",
                request=request,
                alert=True,
                error_url=request_url
            )
            raise HTTPException(status_code=404, detail=error_msg)
        
        ## company_id 추출
        company_id = str(company_info["_id"])
        logger.info(f"[turnover_analysis] company_id: {company_id}, company_name: {company_info['company_name']}, biz_no: {company_info['biz_no']}")

        welfare_collection = async_mongo_client("culture_db", "company_welfare")
        review_collection = async_mongo_client("culture_db", "company_review")

        turnover_data = {
            "company_id": company_id,
            "company_name": company_info['company_name'],
            "biz_no": company_info['biz_no'],
            "date": datetime.utcnow(),
            "status": "processing"
        }

        collection = async_mongo_client("culture_db", "company_turnover")
        insert_result = await collection.insert_one(turnover_data)
        inserted_id = insert_result.inserted_id
        
        # BackgroundTasks에 등록하면 응답 후 백그라운드 작업 실행됨
        background_tasks.add_task(
            background_company_turnover_analysis, 
            request, 
            company_data, 
            company_info, 
            inserted_id, 
            welfare_collection, 
            review_collection,
            collection
        )
        
        # 즉시 요청 접수 응답과 _id 반환
        return {
            "status": "accepted",
            "message": "회사 재직 요인 분석 요청이 접수되었습니다. 분석 결과는 후속 업데이트를 확인해주세요.",
            "id": str(inserted_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사 재직 만족도 분석 중 오류 발생: {str(e)}")
        await error_handler.handle_error(
            e,
            api_source="turnover_analysis",
            detail_message=f"회사 재직 만족도 분석 API 호출 중 오류 발생",
            request=request,
            alert=True,
            error_url=request_url
        )
        raise HTTPException(status_code=500, detail=f"회사 재직 만족도 분석 중 오류 발생: {str(e)}")
    

@router.get("/backoffice_worker/company/analysis/turnover/id/{id}", response_model=TurnoverAnalysisByIdResponse)
async def get_company_turnover_analysis(id: str):
    collection = connect_to_mongo("culture_db", "company_turnover")
    try:
        result = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        logger.error(f"ObjectId 변환 오류: {e}")
        return {"status": "failed", "message": "유효하지 않은 _id 형식입니다.", "data": []}

    if not result:
        return {"status": "failed", "message": "turnover 데이터가 존재하지 않습니다.", "data": []}

    return {"status": "success", "message": "turnover 데이터 조회 성공", "data": result.get('response')}


@router.get("/backoffice_worker/company/analysis/turnover/biz_no/{biz_no}", response_model=TurnoverAnalysisByBizNoResponse)
async def get_company_turnover_analysis_by_biz_no(biz_no: str):
    # company_turnover 컬렉션에서 사업자번호로 데이터 조회
    collection = connect_to_mongo("culture_db", "company_turnover")
    formatted_biz_no = format_business_number(biz_no)
    
    try:
        results = list(collection.find({"biz_no": formatted_biz_no}))

        if not results:
            return {
                "status": "failed", 
                "message": "해당 사업자 번호의 데이터가 존재하지 않습니다.",
                "data": []
            }
        
        converted_results = convert_objectid_to_str(results)
        return {"status": "success", "message": "turnover 데이터 조회 성공", "data": converted_results}
    
    except Exception as e:
        logger.error(f"MongoDB 조회 오류: {e}")
        return {"status": "failed", "message": f"turnover 데이터 조회 중 오류가 발생했습니다. {str(e)}", "data": []}