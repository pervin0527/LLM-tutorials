import os
import re
import time

from datetime import datetime
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.jobplanet_utils import jobplanet_login
from src.crawler.utils.data_utils import save_json, transform_data
from src.crawler.utils.selenium_utils import set_webdriver, wait_for_element

from app.utils.logging import logger

SAVE_PATH = "./data/company_welfare"
INFO_URLS = [
    "https://www.jobplanet.co.kr/companies",
    # "https://www.saramin.co.kr/zf_user/company-info/",
    # "https://www.jobkorea.co.kr/company/"
]

JOBPLANET_URL = "https://www.jobplanet.co.kr/companies"
WANTED_URL = "https://www.wanted.co.kr/company"


def extract_company_id(url: str) -> Optional[str]:
    """
    URL에서 /companies/ 뒤에 나오는 숫자(기업 ID)를 추출합니다.
    예) 'https://www.jobplanet.co.kr/companies/93880/premium_reviews/카카오' → '93880'
    """
    pattern = r'/companies/(\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def google_search_jobplanet_ids(driver:WebDriver, 
                             query:str,
                             company_name:str, 
                             company_bizno:Optional[str] = None, 
                             company_url:Optional[str] = None
):
    logger.info(f"구글 검색 시작: {company_name} {company_bizno} {company_url}")

    sub_driver = set_webdriver()
    try:    
        driver.get(query)
        time.sleep(0.5)

        container = driver.find_element(By.XPATH, '//*[@id="rso"]')
        items = []
        for class_name in ["hlcw0c", "MjjYud"]:
            items.extend(container.find_elements(By.CLASS_NAME, class_name))

        jobplanet_ids = set()
        for idx, item in enumerate(items):
            try:
                searched_url = item.find_element(By.TAG_NAME, 'a').get_attribute("href")
                sub_driver.get(searched_url)

                header = sub_driver.find_element(By.ID, "CompaniesHeader")
                companies_info = header.find_element(By.ID, "CompaniesInfo")
                jobplanet_company_name = companies_info.find_element(By.ID, "companyName").text
                jobplanet_company_url = companies_info.find_element(By.XPATH, '//*[@id="CompaniesInfo"]/div[2]/div/div[2]/div/a').get_attribute("href")

                logger.info(f"idx : {idx}, searched_url : {searched_url}")
                logger.info(f"jobplanet_company_name : {jobplanet_company_name}, jobplanet_company_url : {jobplanet_company_url}")

                jobplanet_company_id = extract_company_id(searched_url)
                logger.info(f"jobplanet_company_id : {jobplanet_company_id}")

                if any(url in searched_url for url in INFO_URLS) and company_url in jobplanet_company_url and company_name in jobplanet_company_name and jobplanet_company_id is not None:
                    jobplanet_ids.add(jobplanet_company_id)
                
            except:
                continue

        return list(jobplanet_ids)

    except Exception as e:
        logger.warning(f"구글 검색 실패: {e}")
        return []


def get_jobplanet_welfare(driver:WebDriver, curr_url:str, company_url:str):
    try:
        jobplanet_login(driver)
        time.sleep(1)
        
        logger.info(f"[잡플래닛] {curr_url} 로드 중...")
        driver.get(curr_url)

        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')        
        body_wrap = driver.find_element(By.CLASS_NAME, "body_wrap")
        cmp_hd = wait_for_element(driver, By.XPATH, '/html/body/div[1]/div[3]')    
        logger.info(f"[잡플래닛] {curr_url} 로드 완료")

        new_top_bnr = cmp_hd.find_element(By.CLASS_NAME, "new_top_bnr")
        top_bnr_container = new_top_bnr.find_element(By.CLASS_NAME, "top_bnr_container")
        top_bhr_box = top_bnr_container.find_element(By.CLASS_NAME, "top_bhr_box")

        company_info_box = top_bhr_box.find_element(By.CLASS_NAME, "company_info_box")
        about_company = company_info_box.find_element(By.CLASS_NAME, "about_company")
        target_url = about_company.find_element(By.CLASS_NAME, "info").find_element(By.TAG_NAME, "a").get_attribute("href")

        if company_url in target_url:
            contents_wrap = body_wrap.find_element(By.ID, "contents_wrap")
            contents = contents_wrap.find_element(By.ID, "contents")
            main_contents = contents.find_element(By.ID, "mainContents")

            welfare_container = main_contents.find_element(By.ID, "welfareReviewsContainer")
            welfare_tab = welfare_container.find_element(By.ID, "welfareReviewTab")

            try:
                welfare_item_list = welfare_tab.find_element(By.ID, "welfare-item-list")
                welfare_provision = welfare_item_list.find_element(By.CLASS_NAME, "welfare-provision")
                section = welfare_provision.find_element(By.CLASS_NAME, "welfare-provision__section")

                welfare_provision_list = section.find_element(By.CLASS_NAME, "welfare-provision__list")
                items = welfare_provision_list.find_elements(By.CLASS_NAME, "welfare-provision__item")

                logger.info(f"[잡플래닛] {len(items)}개의 복지 정보 찾음")
                total_data = []
                for item in items:
                    title = item.find_element(By.CLASS_NAME, "welfare-bullet__tit").text
                    welfare_items = item.find_elements(By.CLASS_NAME, "welfare-bullet__item")

                    curr_data = []
                    for welfare_item in welfare_items:
                        curr_data.append(welfare_item.text)
                    
                    total_data.append({title: curr_data})

                logger.info(f"[잡플래닛] 복지 정보 수집 완료")
                return total_data

            except Exception as e:
                logger.error(f"[잡플래닛] 복지 정보를 찾지 못함 : {e}")

    except Exception as e:
        logger.error(f"[잡플래닛] 복지 수집 중 오류 발생: {e}")
        return []


def get_wanted_insights(driver:WebDriver, query:str, company_name:str, company_bizno:str):
    try:
        pass

        
    except Exception as e:
        logger.warning(f"원티드 인사이트 수집 실패: {e}")
        return []


def get_company_welfare(company_name: str, company_bizno: Optional[str] = None, company_url: Optional[str] = None):
    os.makedirs(SAVE_PATH, exist_ok=True)
    driver = set_webdriver()

    # get_wanted_insights(
    #     driver, 
    #     query=f"https://www.google.com/search?q=원티드+{company_name}+{company_bizno}", 
    #     company_name=company_name, 
    #     company_bizno=company_bizno
    # )

    data = None  # 결과 데이터를 저장할 변수
    try:    
        jobplanet_ids = google_search_jobplanet_ids(
            driver, 
            query=f"https://www.google.com/search?q=잡플래닛+{company_name}+기업+복지", 
            company_name=company_name, 
            company_bizno=company_bizno, 
            company_url=company_url
        )
        logger.info(f"후보 수 : {len(jobplanet_ids)}")

        for idx, jobplanet_id in enumerate(jobplanet_ids):
            curr_url = f"https://www.jobplanet.co.kr/companies/{jobplanet_id}/benefits"
            logger.info(f"[{idx+1}/{len(jobplanet_ids)}] curr_url : {curr_url}")

            welfare_data = get_jobplanet_welfare(driver, curr_url, company_url)
            if welfare_data:  # 데이터가 수집된 경우에만
                data = {
                    'source': 'jobplanet',
                    'welfare_data': welfare_data
                }
                break  # 성공적으로 데이터를 얻었으면 반복 중단

    except Exception as e:
        logger.error(f"구글 검색 실패: {e}")
        return []
    
    finally:
        driver.quit()  # 모든 작업이 끝난 후에 드라이버 종료

    data = {
        "company": company_name,
        "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
        "welfare_data": data
    }
    save_json(data, f"{SAVE_PATH}/{company_name}.json")

    return data