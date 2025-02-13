import os
import time
import json

from typing import List
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from app.utils.logging import logger
from src.crawler.utils.selenium_utils import set_webdriver
from src.crawler.utils.data_utils import save_json, transform_data, normalize_url

SAVE_PATH = "./data/company_info"
BIZ_NO_URL = "https://bizno.net/상호명으로사업자등록번호조회/"


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
    """
    google 검색 결과 중 bizno.net 검색 결과 찾기
    """
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
        logger.warning(f"구글 검색 실패: {e}")
        return None
    
    return None
    

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

        collected_data = {"company": company_name}
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


def get_company_info(company_name:str):
    os.makedirs(SAVE_PATH, exist_ok=True)
    driver = set_webdriver()

    try:
        driver.get(BIZ_NO_URL)
        # bizno_send_query(driver, company_name)
        # post = bizno_get_post(driver)
        # company, post_url = post

        post_url = google_search_bizno(driver, company_name)
        driver.get(post_url)
        time.sleep(0.5)

        data = bizno_get_detail(driver)
        data["homepage"] = normalize_url(data["homepage"])
        driver.quit()        

        logger.info(f"bizno.net에서 기업 데이터 수집 완료 : {data}")
        save_json(data, f"{SAVE_PATH}/{company_name}.json")
        logger.info(f"기업 정보 데이터가 {SAVE_PATH}/{company_name}.json에 저장되었습니다.")
        return data
    
    except Exception as e:
        logger.error(f"기업 데이터 수집 중 오류 발생 : {e}")
        return None