import time
import json

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

from app.utils.logging import logger

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


def save_tree(tree, filename="crawl_result.json"):
    """크롤링 결과를 JSON 파일로 저장"""

    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(tree, json_file, ensure_ascii=False, indent=4)
        
    print(f"크롤링 결과가 {filename} 파일로 저장되었습니다.")


def transform_data(web_tree, company_name):   
    def extract_pages(data):
        pages = []
        stack = [data]  # 루트 데이터부터 탐색 시작
        
        while stack:
            current = stack.pop()
            pages.append({"url": current["url"], "text": current.get("text", "")})
            stack.extend(current.get("children", []))  # 자식 요소들을 스택에 추가
        
        return pages
    
    current_time = datetime.today().strftime("%y.%m.%d-%H:%M:%S")
    formatted_data = {
        "company": company_name,
        "collected_date": current_time,
        "updated_date": None,
        "root_url": web_tree["url"],
        "pages": extract_pages(web_tree)
    }
    
    return formatted_data