import os
import time
import json

from typing import List
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from src.crawler.utils.selenium_utils import set_webdriver

from app.utils.logging import logger


def search_google(driver, company_name:str, url:str):
    driver.get("https://www.google.com")
    driver.find_element(By.XPATH, '//*[@id="APjFqb"]').send_keys(f"잡플래닛 {company_name} {url}")
    driver.find_element(By.XPATH, '//*[@id="APjFqb"]').send_keys(Keys.ENTER)
    time.sleep(1)

    container = driver.find_element(By.XPATH, '//*[@id="rso"]')
    items = container.find_elements(By.TAG_NAME, 'div')

    urls = []
    for item in items:
        try:
            target_url = item.find_element(By.TAG_NAME, 'a').get_attribute("href")
            urls.append(target_url)
        except:
            continue
    
    return urls


def login(driver):
    driver.get("https://www.jobplanet.co.kr/users/sign_in?_nav=gb")
    time.sleep(2)

    driver.find_element(By.XPATH, '//*[@id="user_email"]').send_keys("admin@gravylab.co.kr")
    driver.find_element(By.XPATH, '//*[@id="user_password"]').send_keys("glab0110!!")
    driver.find_element(By.XPATH, '//*[@id="signInSignInCon"]/div[2]/div/section[2]/fieldset/button').click()
    time.sleep(0.5)


def compare_url(driver, company_url:str, urls:List[str]):
    logger.info(f"{len(urls)}개에서 target 찾는 중")
    for idx, url in enumerate(urls):
        driver.get(url)
        time.sleep(1.2)

        logger.info(f"{idx+1}번째 페이지 {url} 확인 중")

        try:
            curr_url = driver.find_element(By.XPATH, '//*[@id="CompaniesInfo"]/div[2]/div/div[2]/div/a').get_attribute("href")
            if curr_url == company_url:
                return idx
        except:
            continue
        
    return -1


def collect_reviews(driver:WebDriver, company_name:str, start_url:str, date_filter:str="2024.12"):
    driver.get(start_url)
    time.sleep(1)

    page_number = 1
    total_review_data = []
    while True:
        curr_url = driver.current_url
        if page_number > 1:
            curr_url = "/".join(curr_url.split("/")[:-1])
            curr_url = f"{curr_url}/{company_name}?page={page_number}"
            driver.get(curr_url)
        logger.info(f"page : {page_number}, url : {driver.current_url}")


        review_container = driver.find_element(By.XPATH, '//*[@id="ReviewContainer"]')
        driver.execute_script("arguments[0].scrollIntoView();", review_container)
        time.sleep(1)

        reviews_list = review_container.find_element(By.ID, "viewReviewsList")
        reviews = reviews_list.find_elements(By.TAG_NAME, 'section')        

        if len(reviews) == 0:
            break

        for review in reviews:
            curr_review_data = {}
            review_header = review.find_element(By.CLASS_NAME, "items-center")
            header_items = review_header.find_elements(By.TAG_NAME, "span")
            for idx, header_item in enumerate(header_items):
                if idx == 0:
                    curr_review_data["position"] = header_item.text
                elif idx == 2:
                    curr_review_data["employ_status"] = header_item.text
                elif idx == 4:
                    curr_review_data["working_area"] = header_item.text
                elif idx == 6:
                    curr_review_data["review_date"] = "".join(header_item.text.split(" ")[0:2])

            review_date = curr_review_data["review_date"]
            if review_date < date_filter:
                return total_review_data

            review_content = review.find_element(By.CLASS_NAME, 'items-stretch')
            rate = review_content.find_element(By.ID, "ReviewCardSide").find_element(By.TAG_NAME, "span").text
            curr_review_data["rate"] = rate
            
            content_container = review_content.find_element(By.CLASS_NAME, "w-full")
            title = content_container.find_element(By.TAG_NAME, "h2").text
            curr_review_data["title"] = title

            divs = content_container.find_elements(By.CLASS_NAME, "whitespace-pre-wrap")
            for idx, div in enumerate(divs):
                content = " ".join(div.text.split("\n")[1:])
                
                if idx == 0:
                    curr_review_data["positive"] = content
                elif idx == 1:
                    curr_review_data["negative"] = content
                elif idx == 2:
                    curr_review_data["expectation"] = content

            total_review_data.append(curr_review_data)

        logger.info(f"page: {page_number}, total : {len(total_review_data)}\n sample : {curr_review_data}")
        page_number += 1

    return total_review_data
        

def crawl_jobplanet(company_name:str, company_url:str, date_filter:str="2024.12"):
    driver = set_webdriver()
    driver.get("https://www.jobplanet.co.kr/users/sign_in?_nav=gb")
    urls = search_google(driver, company_name, company_url)
    
    login(driver)
    time.sleep(0.7)

    idx = compare_url(driver, company_url, urls[:3])
    if idx == -1:
        logger.warning("검색 결과가 없습니다.")
        if "https://www.jobplanet.co.kr/companies" in urls[0]:
            target_url = urls[0]
            jobplanet_id = target_url.split("/")[-1]
            logger.info(f"{target_url}로 설정하고 리뷰를 수집합니다.")
        
        else:
            logger.warning("https://www.jobplanet.co.kr/companies 로 시작하는 후보가 없습니다. 리뷰 크롤링을 종료합니다.")
            return []
        
    else:
        target_url = urls[idx]
        jobplanet_id = target_url.split("/")[-3]
        logger.info(f"타겟을 찾았습니다. URL : {target_url}, ID : {jobplanet_id}")

    logger.info(f"리뷰 수집 시작, 기업명 : {company_name}, 기업 URL : {company_url}, 기업 ID : {jobplanet_id}, 날짜 필터 : {date_filter}")
    review_data = collect_reviews(driver, company_name, target_url, date_filter)
    logger.info(f"리뷰 수집 완료")

    os.makedirs(f"./data/jobplanet", exist_ok=True)

    data = {
        "company": company_name,
        "root_url": company_url,
        "jobplanet_id": jobplanet_id,
        "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
        "review_data": review_data
    }
    with open(f"./data/jobplanet/{company_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    driver.quit()

    return data

if __name__ == "__main__":
    crawl_jobplanet("남양유업", "https://company.namyangi.com/", "2024.12")