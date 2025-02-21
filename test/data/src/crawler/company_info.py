import os
import time
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from datetime import datetime
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from app.utils.logging import logger
from src.crawler.utils.selenium_utils import set_webdriver
from src.crawler.utils.data_utils import save_json, normalize_url, format_business_number

SAVE_PATH = "./data/company_info"
BIZ_NO_URL = "https://bizno.net/상호명으로사업자등록번호조회/"

# 전역 ThreadPoolExecutor 생성
executor = ThreadPoolExecutor(max_workers=3)

def bizno_send_query(driver:WebDriver, company_name:str):
    """
    bizno.net에 검색어 입력
    """
    logger.info(f"bizno.net에 검색어 입력 : {company_name}")
    try:
        home = driver.find_element(By.ID, "home")
        container = home.find_element(By.CLASS_NAME, "container")
        search_form = container.find_element(By.CLASS_NAME, "serach-form-area").find_element(By.CLASS_NAME, "form-wrap")

        form_cols = search_form.find_elements(By.CLASS_NAME, "form-cols")
        target_col = form_cols[1]
        input_box = target_col.find_element(By.ID, "query")
        input_box.send_keys(company_name)
        input_box.send_keys(Keys.ENTER)

        time.sleep(0.5)
        logger.info(f"검색 완료")

    except Exception as e:
        logger.error(f"검색 실패 : {e}")
    

def bizno_get_post(driver:WebDriver):
    """
    검색 결과 리스트 중 하나를 선택.
    """
    logger.info(f"검색 결과 탐색 시작")
    try:
        post_area = driver.find_element(By.CLASS_NAME, "post-area")
        container = post_area.find_element(By.CLASS_NAME, "container")
        post_list = container.find_element(By.CLASS_NAME, "post-list")
        post_items = post_list.find_elements(By.CLASS_NAME, "single-post")
        logger.info(f"검색 결과 수 : {len(post_items)}")

        candidates = []
        for idx, post_item in enumerate(post_items):
            details = post_item.find_element(By.CLASS_NAME, "details")
            title_div = details.find_element(By.CLASS_NAME, "titles")
            a = title_div.find_element(By.TAG_NAME, "a")
            url = a.get_attribute("href")
            title = a.find_element(By.TAG_NAME, "h4").text
            candidates.append((title, url))

        logger.info(f"탐색 완료. : {candidates[0][0]}, {candidates[0][1]}")
        return candidates[0]

    except Exception as e:
        logger.error(f"탐색 중 에러 : {e}")
        return None
    

def google_search_bizno(driver:WebDriver, company_name:str):
    logger.info(f"google 검색 시작 : {company_name}")
    try:    
        driver.get(f"https://www.google.com/search?q={company_name}+사업자등록번호")
        time.sleep(0.5)

        container = driver.find_element(By.XPATH, '//*[@id="rso"]')
        items = container.find_elements(By.TAG_NAME, 'div')
        logger.info(f"구글 검색 성공: {len(items)}개 후보")

        for item in items:
            try:
                target_url = item.find_element(By.TAG_NAME, 'a').get_attribute("href")
                if "https://bizno.net/article/" in target_url:
                    return target_url
            except:
                continue

    except Exception as e:
        logger.warning(f"❌ 구글 검색 실패: {e}")
        return None

    logger.warning(f"❌ 사업자등록번호 관련 링크를 찾지 못했습니다. company_name: {company_name}")
    return None  # 적절한 URL을 찾지 못하면 `None` 반환

    

def bizno_get_detail(driver: WebDriver):
    """
    post 페이지 데이터 수집
    """
    logger.info(f"데이터 수집 시작")

    try:
        post_area = driver.find_element(By.CLASS_NAME, "post-area")
        container = post_area.find_element(By.CLASS_NAME, "container")
        post_list = container.find_element(By.CLASS_NAME, "post-list")
        target_post = post_list.find_elements(By.CLASS_NAME, "single-post")[0]
        details = target_post.find_element(By.CLASS_NAME, "details")

        company_name = details.find_element(By.CLASS_NAME, "titles").text
        
        table = details.find_element(By.CLASS_NAME, "table_guide01")
        trs = table.find_elements(By.TAG_NAME, "tr")

        # 수집할 데이터와 키워드 매핑
        data_mapping = {
            "국세청업종분류": "industry",
            "업태": "business_type",
            "전화번호": "phone_number",
            "팩스번호": "fax_number",
            "기업규모": "enterprise_scale",
            "법인구분": "business_entity",
            "본사/지사": "office_type",
            "홈페이지": "homepage",
            "IR홈페이지": "ir_homepage",
            "대표자명": "ceo_name",
            "사업자등록번호": "biz_no",
            "법인등록번호": "corp_no",
            "우편번호": "postal_code",
            "회사주소": "address"
        }

        collected_data = {"alias_name": company_name}
        for tr in trs:
            try:
                th_elements = tr.find_elements(By.TAG_NAME, "th")
                if not th_elements:  # th가 없으면 다음 tr로 넘어감
                    continue

                th = tr.find_element(By.TAG_NAME, "th").text.strip()
                td = tr.find_element(By.TAG_NAME, "td")
                
                if th in data_mapping:
                    if th == "국세청업종분류":
                        # 산업분류 정보 추출
                        industry_info = {}
                        p_tags = td.find_elements(By.TAG_NAME, "p")
                        
                        for p in p_tags:
                            if "대분류" in p.text:
                                industry_info["main_category"] = p.text.split(":", 1)[-1].strip()
                            elif "중분류" in p.text:
                                industry_info["middle_category"] = p.text.split(":", 1)[-1].strip()
                            elif "소분류" in p.text:
                                industry_info["sub_category"] = p.text.split(":", 1)[-1].strip()
                            elif "세분류" in p.text:
                                industry_info["detailed_category"] = p.text.split(":", 1)[-1].strip()
                        collected_data["industry"] = industry_info
                        
                    elif th == "회사주소":
                        # 주소 정보 추출
                        addresses = td.text.split("\n")
                        address_data = {
                            "road": addresses[0].strip() if len(addresses) > 0 else "",
                            "jibun": addresses[2].strip() if len(addresses) > 2 else ""
                        }
                        collected_data["address"] = address_data
                        
                    else:
                        # 일반적인 데이터 추출
                        collected_data[data_mapping[th]] = td.text.strip()
            
            except Exception as e:
                logger.error(f"Row 처리 중 에러 발생: {th} - {str(e)}")
                continue

        return collected_data

    except Exception as e:
        logger.error(f"데이터 수집 중 에러 : {e}")
        return None

# 기존 동기 함수들은 유지하고 비동기 래퍼 함수 추가
async def bizno_send_query_async(driver: WebDriver, company_name: str):
    return await asyncio.get_event_loop().run_in_executor(
        executor, bizno_send_query, driver, company_name
    )

async def google_search_bizno_async(driver: WebDriver, company_name: str):
    return await asyncio.get_event_loop().run_in_executor(
        executor, google_search_bizno, driver, company_name
    )

async def bizno_get_detail_async(driver: WebDriver):
    return await asyncio.get_event_loop().run_in_executor(
        executor, bizno_get_detail, driver
    )

async def get_company_info(company_name: str, company_biz_no: Optional[str] = None, company_url: Optional[str] = None):
    """
    기업 정보를 비동기적으로 수집하는 함수
    """
    os.makedirs(SAVE_PATH, exist_ok=True)
    driver = set_webdriver()

    try:
        driver.get(BIZ_NO_URL)

        # 구글 검색을 통해 post_url 가져오기
        post_url = await google_search_bizno_async(driver, company_name)

        if not post_url:
            logger.error(f"❌ 구글 검색에서 사업자등록번호 페이지를 찾을 수 없습니다. company_name: {company_name}")
            driver.quit()
            return {
                "status": "failed",
                "message": "사업자등록번호 페이지를 찾을 수 없습니다."
            }

        driver.get(post_url)
        time.sleep(0.5)

        data = await bizno_get_detail_async(driver)
        if not data:
            logger.error(f"❌ 기업 데이터 수집 실패: {company_name}")
            driver.quit()
            return {
                "status": "failed",
                "message": "기업 데이터 수집 실패"
            }

        data["company_name"] = company_name
        data["eda_status"] = "not_available"

        if company_biz_no:
            logger.info(f"biz_no 제공됨 : {company_biz_no}")
            data["biz_no"] = format_business_number(company_biz_no)
        else:
            company_biz_no = format_business_number(data["biz_no"])
            data["biz_no"] = company_biz_no

        if company_url:
            logger.info(f"homepage 제공됨 : {company_url}")
            data["homepage"] = company_url

        driver.quit()

        logger.info(f"✅ bizno.net에서 기업 데이터 수집 완료 : {data}")
        save_json(data, f"{SAVE_PATH}/{company_name}.json")
        logger.info(f"✅ 기업 정보 데이터가 {SAVE_PATH}/{company_name}.json에 저장되었습니다.")
        
        return data

    except Exception as e:
        logger.error(f"❌ 기업 데이터 수집 중 오류 발생 : {e}")
        driver.quit()
        return None
