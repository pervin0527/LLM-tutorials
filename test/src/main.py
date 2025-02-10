import time
import logging

from typing import Optional

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

def set_webdriver(start_url):
    logger.info(f"웹드라이버 설정 시작: {start_url}")
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # 추가적인 헤더 설정
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 더 현실적인 user-agent 설정
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
    options.add_argument(f'user-agent={user_agent}')
    
    # 추가 헤더 설정
    options.add_argument('accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    options.add_argument('accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 웹드라이버 감지 방지를 위한 JavaScript 실행
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    # 페이지 로딩 대기 시간 증가
    driver.get(start_url)
    time.sleep(1)
    
    logger.info("웹드라이버 설정 완료")
    return driver


def login_jobplanet(driver):
    driver.find_element(By.XPATH, '//*[@id="user_email"]').send_keys("admin@gravylab.co.kr")
    driver.find_element(By.XPATH, '//*[@id="user_password"]').send_keys("glab0110!!")
    driver.find_element(By.XPATH, '//*[@id="signInSignInCon"]/div[2]/div/section[2]/fieldset/button').click()
    time.sleep(0.5)


def set_company_name(driver, company_name):
    driver.find_element(By.XPATH, '//*[@id="search_bar_search_query"]').send_keys(company_name)
    driver.find_element(By.XPATH, '//*[@id="search_bar_search_query"]').send_keys(Keys.ENTER)
    container = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[1]/div/div/div[1]/div[2]/ul')
    items = container.find_elements(By.TAG_NAME, "a")
    print(len(items))

    target_item = items[0]
    driver.get(target_item.get_attribute("href"))
    time.sleep(1)
    

def collect_reviews(driver):
    review_container = driver.find_element(By.XPATH, '//*[@id="ReviewContainer"]')
    
    # 스크롤을 review_container로 이동
    driver.execute_script("arguments[0].scrollIntoView();", review_container)
    time.sleep(1)  # 스크롤 후 잠시 대기
    
    review_header = review_container.find_element(By.ID, "viewReviewsTitle")
    num_reviews = int(review_header.find_element(By.TAG_NAME, "span").text)
    print(num_reviews)



def crawl_jobplanet(company_name:str, url:Optional[str]=None):
    driver = set_webdriver("https://www.jobplanet.co.kr/users/sign_in?_nav=gb")
    login_jobplanet(driver)

    if url is None:
        set_company_name(driver, company_name)
    else:
        driver.get(url)

    collect_reviews(driver)

    time.sleep(30)
    driver.quit()


def main():
    company_name = "현대자동차"
    crawl_jobplanet(company_name)

if __name__ == "__main__":
    main()