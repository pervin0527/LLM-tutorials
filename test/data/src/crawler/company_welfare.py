import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from typing import Optional
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver

from src.crawler.utils.data_utils import save_json
from src.crawler.utils.selenium_utils import set_webdriver

from src.crawler.utils.jobplanet_utils import get_jobplanet_welfare_async
from src.crawler.utils.wanted_utils import get_wanted_welfare_async
from app.utils.logging import logger

SAVE_PATH = "./data/company_welfare"
TARGET_URLS = [
    "https://www.jobplanet.co.kr/companies",
    # "https://www.saramin.co.kr/zf_user/company-info/",
    # "https://www.jobkorea.co.kr/company/"
]

# 전역 ThreadPoolExecutor 생성
executor = ThreadPoolExecutor(max_workers=3)

async def get_company_welfare(company_name: str, company_url: str, company_bizno: str):
    os.makedirs(SAVE_PATH, exist_ok=True)
    driver = set_webdriver()
    total_data = []

    try:
        # 원티드 복지 정보 수집
        wanted_result = await get_wanted_welfare_async(driver, company_name, company_url, company_bizno)
        logger.info(f"Wanted result: {wanted_result}")
        if wanted_result:
            total_data.append({'source': 'wanted', 'data': wanted_result})
        else:
            total_data.append({'source': 'wanted', 'data': []})

        # 잡플래닛 복지 정보 수집
        jobplanet_result = await get_jobplanet_welfare_async(driver, company_name, company_url, company_bizno, TARGET_URLS)
        logger.info(f"Jobplanet result: {jobplanet_result}")
        if jobplanet_result:
            total_data.append({'source': 'jobplanet', 'data': jobplanet_result})
        else:
            total_data.append({'source': 'jobplanet', 'data': []})

        data = {
            "company_name": company_name,
            "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
            "welfare_data": total_data
        }

        save_json(data, f"{SAVE_PATH}/{company_name}.json")
        logger.info(f"기업 복지 수집 결과가 {SAVE_PATH}/{company_name}.json에 저장되었습니다.")

        driver.quit()
        return data

    except Exception as e:
        logger.error(f"복지 정보 수집 중 오류 발생: {e}")