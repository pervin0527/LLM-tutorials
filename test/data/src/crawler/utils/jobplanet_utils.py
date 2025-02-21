import re
import time
import asyncio

from datetime import datetime
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.data_utils import extract_company_id
from src.crawler.utils.selenium_utils import set_webdriver, wait_for_element

from app.utils.logging import logger

# 전역 ThreadPoolExecutor 생성
executor = ThreadPoolExecutor(max_workers=3)

REVIEW_TARGETS = ["https://www.jobplanet.co.kr/companies"]


def jobplanet_login(driver:WebDriver):
    logger.info("잡플래닛 로그인 시작")
    while True:
        driver.get("https://www.jobplanet.co.kr/users/sign_in?_nav=gb")
        try:
            contents_wrap = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="contents_wrap"]'))
            )
            break  # 성공적으로 찾으면 반복문 탈출

        except:
            logger.warning("contents_wrap을 찾지 못했습니다. 다시 시도합니다.")
            time.sleep(1)  # 잠시 대기 후 다시 시도

    contents = contents_wrap.find_element(By.ID, "contents")
    new_user = contents.find_element(By.ID, "new_user")

    sign_in = new_user.find_element(By.ID, "signInSignInCon")
    login_container = sign_in.find_element(By.CLASS_NAME, 'signInsignIn_wrap')
    sign_wrap = login_container.find_element(By.CLASS_NAME, "sign_wrap")
    email_section = sign_wrap.find_element(By.CLASS_NAME, "section_email")

    user_email = email_section.find_element(By.ID, "user_email")
    user_email.send_keys("admin@gravylab.co.kr")

    user_password = email_section.find_element(By.ID, "user_password")
    user_password.send_keys("glab0110!!")

    sign_in_button = sign_wrap.find_element(By.CLASS_NAME, "btn_sign_up")
    sign_in_button.click()

    logger.info("로그인 완료")
    

def google_search_jobplanet(driver: WebDriver, company_name: str, url: str, bizno: str):
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


def compare_url(driver: WebDriver, company_url: str, urls: List[str]):
    logger.info(f"{len(urls)}개에서 target 찾는 중")
    for idx, url in enumerate(urls):
        logger.info(f"{company_url}, {url} 비교 중")
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


def google_search_jobplanet_ids(driver:WebDriver, target_urls:List[str], company_name:str, company_url:Optional[str] = None, company_bizno:Optional[str] = None):
    logger.info(f"[jobplanet - 구글검색] {company_name} {company_bizno} {company_url}")
    sub_driver = set_webdriver()

    try:    
        driver.get(f"https://www.google.com/search?q=잡플래닛+{company_name}")
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

                logger.info(f"[jobplanet - 구글검색] idx : {idx}, searched_url : {searched_url}")
                jobplanet_company_id = extract_company_id(searched_url)
                logger.info(f"[jobplanet - 구글검색] 회사명 : {jobplanet_company_name}, 회사 id : {jobplanet_company_id}, 회사 링크 : {jobplanet_company_url}")

                if jobplanet_company_id is None:
                    logger.info(f"잡플래닛 id가 없습니다.")
                    continue

                if any(url in searched_url for url in target_urls):
                    logger.info(f"company_name : {company_name}, jobplanet_company_name : {jobplanet_company_name}")
                    logger.info(f"company_url : {company_url}, jobplanet_company_url : {jobplanet_company_url}")

                    if company_url in jobplanet_company_url:
                        logger.info(f"ADDED\n")
                        jobplanet_ids.add(jobplanet_company_id)

                        break

                    else:
                        logger.info(f"NOT ADDED\n")
                
            except:
                continue

        return list(jobplanet_ids)

    except Exception as e:
        logger.warning(f"구글 검색 실패: {e}")
        return []
    
    finally:
        sub_driver.quit()
    

def collect_reviews(driver: WebDriver, company_name: str, jobplanet_id: str, date_filter: str = "2024.12"):
    """
    기업 리뷰를 수집하는 함수
    """ 

    try:
        jobplanet_login(driver)
        time.sleep(3)
        logger.info(f"로그인 후 주소 : {driver.current_url}")

    except RuntimeError as e:
        logger.error(f"로그인 실패로 인해 크롤링 중단: {e}")
        return {"status": "failed", "message": "로그인 실패"}

    encoded_company_name = quote(company_name)
    base_url = f"https://www.jobplanet.co.kr/companies/{jobplanet_id}/reviews/{encoded_company_name}"
    logger.info(f"[company_review] 페이지 로드 중: {base_url}")

    driver.get(base_url)
    time.sleep(5)
    logger.info(f"[company_review] 페이지 로드 완료: {driver.current_url}")
    
    page_number = 1
    total_review_data = []
    while True:
        try:
            current_url = driver.current_url
            if page_number > 1:
                current_url = f"{base_url}?page={page_number}"
                driver.get(current_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ReviewContainer"]')))
                time.sleep(5)

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
                    curr_review_data["positive"] = divs[0].text if len(divs) > 0 else "내용 없음"
                    curr_review_data["negative"] = divs[1].text if len(divs) > 1 else "내용 없음"
                    curr_review_data["expectation"] = divs[2].text if len(divs) > 2 else "내용 없음"

                    total_review_data.append(curr_review_data)

                except Exception as e:
                    logger.error(f"개별 리뷰 처리 중 오류 발생: {e}")
                    continue

            logger.info(f"page: {page_number}, total : {len(total_review_data)}")
            if curr_review_data:
                logger.info(f"sample : {curr_review_data}")
            logger.info(f"{page_number} 페이지 수집 완료")
            page_number += 1
            print("\n")

        except Exception as e:
            logger.error(f"페이지 처리 중 오류 발생: {e}")
            break

    return total_review_data


def get_jobplanet_review(driver: WebDriver, company_name: str, company_url: str, company_bizno: str, date_filter: str = "2024.12"):
    """
    기업의 잡플래닛 리뷰를 수집하는 함수
    """
    try:
        ids = google_search_jobplanet_ids(driver, REVIEW_TARGETS, company_name, company_url, company_bizno)

        if len(ids) == 0:
            logger.warning(f"잡플래닛 회사 검색 결과가 없습니다. company_name : {company_name}, company_url : {company_url}, company_bizno : {company_bizno}")
        
        else:
            for id in ids:
                logger.info(f"[company_review] 타겟 ID : {id}, 시작 URL : https://www.jobplanet.co.kr/companies/{id}/reviews/")
                review_data = collect_reviews(driver, company_name, id, date_filter)

                if len(review_data) == 0:
                    logger.warning(f"리뷰가 없습니다. 크롤링 종료")

                logger.info(f"리뷰 수집 완료")
                break

            return id, review_data

    except Exception as e:
        logger.error(f"[잡플래닛] 리뷰 수집 중 오류 발생: {e}")
        return None
    

async def get_jobplanet_review_async(driver: WebDriver, company_name: str, company_url: str, company_bizno: str, date_filter: str = "2024.12"):
    """
    기업의 잡플래닛 리뷰를 비동기적으로 수집하는 함수
    """
    return await asyncio.get_event_loop().run_in_executor(executor, get_jobplanet_review, driver, company_name, company_url, company_bizno, date_filter)



def get_jobplanet_welfare(driver:WebDriver, company_name:str, company_url:str, company_bizno:str, target_urls:List[str]):
    try:
        jobplanet_ids = google_search_jobplanet_ids(driver, 
                                                    target_urls=target_urls,
                                                    company_name=company_name, 
                                                    company_url=company_url,
                                                    company_bizno=company_bizno)
        
        logger.info(f"후보 수 : {len(jobplanet_ids)}")

        if len(jobplanet_ids) == 0:
            logger.warning(f"잡플래닛 회사 검색 결과가 없습니다. company_name : {company_name}, company_url : {company_url}, company_bizno : {company_bizno}")
            return None

        for idx, jobplanet_id in enumerate(jobplanet_ids):
            curr_url = f"https://www.jobplanet.co.kr/companies/{jobplanet_id}/benefits"
            logger.info(f"[{idx+1}/{len(jobplanet_ids)}] curr_url : {curr_url}")


        jobplanet_login(driver)
        time.sleep(1)
        
        logger.info(f"[잡플래닛] {curr_url} 로드 중...")
        driver.get(curr_url)
        time.sleep(3)

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
                total_data = {}
                for item in items:
                    title = item.find_element(By.CLASS_NAME, "welfare-bullet__tit").text
                    welfare_items = item.find_elements(By.CLASS_NAME, "welfare-bullet__item")

                    curr_data = []
                    for welfare_item in welfare_items:
                        curr_data.append(welfare_item.text)
                    
                    total_data[title] = curr_data

                logger.info(f"[잡플래닛] 복지 정보 수집 완료")
                return total_data

            except Exception as e:
                logger.error(f"[잡플래닛] 복지 정보를 찾지 못함 : {e}")

    except Exception as e:
        logger.error(f"[잡플래닛] 복지 수집 중 오류 발생: {e}")
        return []


async def get_jobplanet_welfare_async(driver, company_name, company_url, company_bizno, target_urls):
    return await asyncio.get_event_loop().run_in_executor(executor, get_jobplanet_welfare, driver, company_name, company_url, company_bizno, target_urls)