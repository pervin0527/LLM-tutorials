import os
import re
import time
import json

from datetime import datetime
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.data_utils import save_json
from src.crawler.utils.selenium_utils import set_webdriver
from src.crawler.utils.jobplanet_utils import jobplanet_login

from app.utils.logging import logger

SAVE_PATH = "./data/company_review"

def google_search_jobplanet(driver, company_name:str, url:str, bizno:str):
    logger.info(f"구글 검색 시작: {company_name} {bizno} {url}")
    try:    
        driver.get(f"https://www.google.com/search?q=잡플래닛+{company_name}+{bizno}+{url}")
        time.sleep(0.5)

        container = driver.find_element(By.XPATH, '//*[@id="rso"]')
        items = container.find_elements(By.TAG_NAME, 'div')
        logger.info(f"구글 검색 성공: {len(items)}개 후보")

        urls = []
        for item in items:
            try:
                target_url = item.find_element(By.TAG_NAME, 'a').get_attribute("href")
                urls.append(target_url)
            except:
                continue

    except Exception as e:
        logger.warning(f"구글 검색 실패: {e}")
        return []
    
    return urls


def compare_url(driver, company_url:str, urls:List[str]):
    logger.info(f"{len(urls)}개에서 target 찾는 중")
    for idx, url in enumerate(urls):
        driver.get(url)
        time.sleep(1.2)

        try:
            curr_url = driver.find_element(By.XPATH, '//*[@id="CompaniesInfo"]/div[2]/div/div[2]/div/a').get_attribute("href")
            if curr_url == company_url:
                logger.info(f"{idx+1}번째 페이지 {url} 확인 완료")
                return idx
        except:
            continue
        
    return -1


def collect_reviews(driver: WebDriver, company_name: str, start_url: str, company_bizno: str, date_filter: str = "2024.12"):
    """
    기업 리뷰를 수집하는 함수
    
    Args:
        driver (WebDriver): Selenium WebDriver 인스턴스
        company_name (str): 기업명
        start_url (str): 시작 URL
        date_filter (str): 수집 중단 기준 날짜 (YYYY.MM 형식)
        
    Returns:
        list: 수집된 리뷰 데이터 리스트
    """
    driver.get(start_url)
    time.sleep(1)

    page_number = 1
    total_review_data = []
    
    while True:
        try:
            # URL 설정
            curr_url = driver.current_url
            if page_number > 1:
                curr_url = "/".join(curr_url.split("/")[:-1])
                curr_url = f"{curr_url}/{company_name}?page={page_number}"
                driver.get(curr_url)
            logger.info(f"page : {page_number}, url : {driver.current_url}")

            # 리뷰 컨테이너 찾기
            review_container = driver.find_element(By.XPATH, '//*[@id="ReviewContainer"]')
            driver.execute_script("arguments[0].scrollIntoView();", review_container)
            time.sleep(1)

            reviews_list = review_container.find_element(By.ID, "viewReviewsList")
            reviews = reviews_list.find_elements(By.TAG_NAME, 'section')        

            if len(reviews) == 0:
                logger.warning(f"리뷰가 없습니다. 크롤링 종료")
                break

            for review in reviews:
                try:
                    curr_review_data = {}
                    
                    # 리뷰 헤더 정보 추출
                    review_header = review.find_element(By.CLASS_NAME, "items-center")
                    header_items = review_header.find_elements(By.TAG_NAME, "span")
                    
                    # 헤더 아이템 처리
                    curr_review_data["position"] = header_items[0].text if len(header_items) > 0 else "정보 없음"
                    curr_review_data["employ_status"] = header_items[2].text if len(header_items) > 2 else "정보 없음"
                    curr_review_data["working_area"] = header_items[4].text if len(header_items) > 4 else "정보 없음"
                    
                    # 리뷰 날짜 처리
                    if len(header_items) > 6:
                        try:
                            date_text = header_items[6].text
                            curr_review_data["review_date"] = "".join(date_text.split(" ")[0:2])
                        except Exception:
                            curr_review_data["review_date"] = "날짜 없음"
                    else:
                        curr_review_data["review_date"] = "날짜 없음"

                    # 날짜 필터 체크 - 날짜가 없는 경우는 계속 수집
                    if curr_review_data["review_date"] != "날짜 없음":
                        try:
                            if curr_review_data["review_date"] < date_filter:
                                return total_review_data
                        except Exception as e:
                            logger.warning(f"날짜 비교 중 오류 발생: {e}")

                    # 리뷰 컨텐츠 추출
                    review_content = review.find_element(By.CLASS_NAME, 'items-stretch')
                    
                    # 평점 추출
                    try:
                        rate = review_content.find_element(By.ID, "ReviewCardSide").find_element(By.TAG_NAME, "span").text
                        curr_review_data["rate"] = rate
                    except Exception:
                        curr_review_data["rate"] = "평점 없음"
                    
                    # 제목과 내용 추출
                    content_container = review_content.find_element(By.CLASS_NAME, "w-full")
                    try:
                        title = content_container.find_element(By.TAG_NAME, "h2").text
                        curr_review_data["title"] = title
                    except Exception:
                        curr_review_data["title"] = "제목 없음"

                    # 장단점 및 기대사항 추출
                    divs = content_container.find_elements(By.CLASS_NAME, "whitespace-pre-wrap")
                    curr_review_data["positive"] = "내용 없음"
                    curr_review_data["negative"] = "내용 없음"
                    curr_review_data["expectation"] = "내용 없음"
                    
                    for idx, div in enumerate(divs):
                        content = " ".join(div.text.split("\n")[1:])
                        if idx == 0:
                            curr_review_data["positive"] = content
                        elif idx == 1:
                            curr_review_data["negative"] = content
                        elif idx == 2:
                            curr_review_data["expectation"] = content

                    total_review_data.append(curr_review_data)

                except Exception as e:
                    logger.error(f"개별 리뷰 처리 중 오류 발생: {e}")
                    continue

            logger.info(f"page: {page_number}, total : {len(total_review_data)}")
            if curr_review_data:
                logger.info(f"sample : {curr_review_data}")
            page_number += 1

        except Exception as e:
            logger.error(f"페이지 처리 중 오류 발생: {e}")
            break

    return total_review_data
        

def get_company_review(
        company_name:str, 
        company_url:str, 
        company_bizno:str, 
        date_filter:str="2024.12"
    ):
    os.makedirs(SAVE_PATH, exist_ok=True)

    driver = set_webdriver()
    urls = google_search_jobplanet(driver, company_name, company_url, company_bizno)
    
    try:
        jobplanet_login(driver)

    except RuntimeError as e:
        logger.error(f"로그인 실패로 인해 크롤링 중단: {e}")
        driver.quit()
        return {"status": False, "message": "로그인 실패로 인해 크롤링 중단"}

    idx = compare_url(driver, company_url, urls[:10])
    # 기존 코드에서 jobplanet_id 추출 부분을 수정
    if idx == -1:
        logger.warning("검색 결과가 없습니다.")
        if "https://www.jobplanet.co.kr/companies" in urls[0]:
            target_url = urls[0]
            match = re.search(r'/companies/(\d+)', target_url)  # 숫자 ID 추출
            if match:
                jobplanet_id = match.group(1)  # 숫자 부분만 가져옴
            else:
                logger.warning("올바른 ID를 찾지 못했습니다.")
                return []
            
            logger.info(f"{target_url}로 설정하고 리뷰를 수집합니다.")
        
        else:
            logger.warning("잡플래닛과 관련된 후보가 없습니다. 리뷰 크롤링을 종료합니다.")
            return []

    else:
        target_url = urls[idx]
        match = re.search(r'/companies/(\d+)', target_url)  # 숫자 ID 추출
        if match:
            jobplanet_id = match.group(1)  # 숫자 부분만 가져옴
        else:
            logger.warning("올바른 ID를 찾지 못했습니다.")
            return []

    logger.info(f"타겟을 찾았습니다. URL : {target_url}, ID : {jobplanet_id}")

    logger.info(f"리뷰 수집 시작, 기업명 : {company_name}, 기업 URL : {company_url}, 기업 ID : {jobplanet_id}, 날짜 필터 : {date_filter}")
    review_data = collect_reviews(driver, company_name, target_url, company_bizno, date_filter)
    logger.info(f"리뷰 수집 완료")

    data = {
        "company": company_name,
        "platform": "jobplanet",
        "root_url": company_url,
        "jobplanet_id": int(jobplanet_id),
        "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
        "review_data": review_data
    }

    save_json(data, f"{SAVE_PATH}/{company_name}.json")

    driver.quit()

    return data