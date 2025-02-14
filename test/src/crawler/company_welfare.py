import os
import time

from typing import Optional
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver

from src.crawler.utils.data_utils import save_json
from src.crawler.utils.selenium_utils import set_webdriver

from src.crawler.utils.jobplanet_utils import get_jobplanet_welfare, google_search_jobplanet_ids
from src.crawler.utils.wanted_utils import wanted_login, wanted_search_company, get_wanted_welfare
from app.utils.logging import logger

SAVE_PATH = "./data/company_welfare"
TARGET_URLS = [
    "https://www.jobplanet.co.kr/companies",
    # "https://www.saramin.co.kr/zf_user/company-info/",
    # "https://www.jobkorea.co.kr/company/"
]



def get_company_welfare(company_name: str, company_url: str, company_bizno: str):
    os.makedirs(SAVE_PATH, exist_ok=True)
    driver = set_webdriver()

    data = []
    try:
        wanted_data = get_wanted_welfare(driver, company_name, company_url, company_bizno)
        if wanted_data:
            data.append({'source': 'wanted', 'data': wanted_data})

    except Exception as e:
        logger.error(f"원티드 복지 수집 실패: {e}")

    try:    
        jobplanet_data = get_jobplanet_welfare(driver, company_name, company_url, company_bizno, TARGET_URLS)
        if jobplanet_data:
            data.append({'source': 'jobplanet', 'data': jobplanet_data})

    except Exception as e:
        logger.error(f"잡플래닛 복지 수집 실패: {e}")
    
    finally:
        driver.quit()

    data = {
        "company": company_name,
        "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
        "welfare_data": data
    }
    save_json(data, f"{SAVE_PATH}/{company_name}.json")

    return data