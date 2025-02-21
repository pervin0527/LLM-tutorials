import os
import re
import time
import json
import asyncio

from datetime import datetime
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.data_utils import save_json
from src.crawler.utils.selenium_utils import set_webdriver
from src.crawler.utils.jobplanet_utils import (
    jobplanet_login, 
    get_jobplanet_review_async,
    compare_url,
    google_search_jobplanet
)

from app.utils.logging import logger

SAVE_PATH = "./data/company_review"

async def get_company_review(company_name: str, company_url: str, company_bizno: str, date_filter: str = None):
    os.makedirs(SAVE_PATH, exist_ok=True)
    driver = set_webdriver()

    logger.info(f"company_name : {company_name}, company_url : {company_url}, company_bizno : {company_bizno}, date_filter : {date_filter}")

    try:
        # 비동기로 잡플래닛 리뷰 수집
        id, data = await get_jobplanet_review_async(driver, company_name, company_url, company_bizno, date_filter)
        data = {
            "company_name": company_name,
            "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
            "platform": "jobplanet",
            "jobplanet_id": id,
            "review_data": data
        }

        save_json(data, f"{SAVE_PATH}/{company_name}.json")
        logger.info(f"기업 리뷰 수집 결과가 {SAVE_PATH}/{company_name}.json에 저장되었습니다.")

        driver.quit()
        return data
    
    except Exception as e:
        logger.error(f"기업 리뷰 수집 중 오류 발생: {e}")
        return None

