import time
import json

from typing import List
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

try:
    from app.utils.logging import logger
except:
    import logging
    logger = logging.getLogger(__name__)


def set_webdriver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # 한글 폰트 설정
    options.add_argument("--font-render-hinting=none")
    options.add_argument("--lang=ko_KR")

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
    
    logger.info("웹드라이버 설정 완료")
    
    return driver


def wait_for_element(driver:WebDriver, by:By, value:str, timeout:int=5, retries:int=5):
    current_url = driver.current_url  # 현재 URL 저장
    
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
            return element
        
        except Exception as e:
            if attempt == retries - 1:
                raise e
            logger.info(f"요소를 찾지 못해 페이지 재접속 시도 ({attempt + 1}/{retries})")
            driver.get(current_url)  # 현재 URL로 다시 접속
            time.sleep(5)  # 페이지 로드를 위한 대기 시간