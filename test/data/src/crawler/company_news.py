import os
import time
import asyncio

from openai import OpenAI
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.data_utils import save_json
from src.crawler.utils.selenium_utils import set_webdriver
from app.utils.logging import logger

SAVE_PATH = "./data/company_news"
NAVER_SEARCH_URL = "https://search.naver.com/search.naver?ssc=tab.news.all&where=news&sm=tab_jum&query="

async def get_gpt_response(client: OpenAI, article_text: str, company_name: str):
    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"주어진 뉴스 기사가 '{company_name}'라는 회사를 주제로 작성된 기사인지 확인하고 관련이 있으면 True, 없으면 False를 반환하세요. 응답은 오직 True 또는 False만 반환해야 합니다."},
            {"role": "user", "content": f"뉴스 기사: {article_text}"},
        ],
        temperature=0.0
    )
    return completion.choices[0].message.content

async def check_correspondence(sub_driver: WebDriver, article_url: str, company_name: str, client: OpenAI):
    """기사 본문을 가져와서 특정 기업이 언급되었는지 확인"""
    try:
        # 동기 함수이므로 await 제거
        sub_driver.get(article_url)
        await asyncio.sleep(1)
        # WebDriverWait 역시 동기 호출이므로 await 제거
        WebDriverWait(sub_driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        article_text = sub_driver.find_element(By.TAG_NAME, "body").text

        relevant = await get_gpt_response(client, article_text, company_name)
        if relevant == "True":
            return True, article_text
        else:
            return False, None

    except Exception as e:
        logger.error(f"❌ 기사 본문 분석 실패: {article_url} - 오류: {e}")
        return False, None

async def get_news_contents(driver: WebDriver, url: str, num_articles: int, company_name: str, client: OpenAI):
    logger.info(f"네이버 검색 시작: {url}")
    # 동기 함수이므로 await 제거
    driver.get(url)
    
    collected_urls = set()
    collected_ids = set()
    article_urls = []
    last_collected_id = 0

    # 별도의 WebDriver를 생성하여 기사 본문 검증
    sub_driver = set_webdriver()
    try:
        while len(article_urls) < num_articles:
            try:
                wrap = driver.find_element(By.ID, "wrap")
                container = wrap.find_element(By.ID, "container")
                content = container.find_element(By.ID, "content")
                main_pack = content.find_element(By.ID, "main_pack")
                section = main_pack.find_element(By.CLASS_NAME, "sp_nnews")
                list_news = section.find_element(By.CLASS_NAME, "list_news")
                news_items = list_news.find_elements(By.CLASS_NAME, "bx")

                current_ids = []
                for item in news_items:
                    news_id = item.get_attribute("id")
                    if news_id and news_id.startswith("sp_nws"):
                        news_num = int(news_id.replace("sp_nws", ""))
                        current_ids.append(news_num)

                if not current_ids:
                    logger.warning("새로운 뉴스 기사가 발견되지 않음, 중단")
                    break

                max_current_id = max(current_ids)

                for item in news_items:
                    try:
                        news_id = item.get_attribute("id")
                        if not news_id or not news_id.startswith("sp_nws"):
                            continue

                        news_num = int(news_id.replace("sp_nws", ""))
                        if news_num <= last_collected_id or news_num in collected_ids:
                            continue

                        news_area = item.find_element(By.CLASS_NAME, "news_area")
                        news_contents = news_area.find_element(By.CLASS_NAME, "news_contents")
                        news_title = news_contents.find_element(By.CLASS_NAME, "news_tit")

                        article_url = news_title.get_attribute("href")
                        article_title = news_title.text
                        if article_url and article_url not in collected_urls:
                            collected_urls.add(article_url)
                            collected_ids.add(news_num)

                            # 별도의 WebDriver로 기사 본문 확인
                            is_relevant, article_text = await check_correspondence(sub_driver, article_url, company_name, client)

                            if is_relevant:
                                article_urls.append({
                                    "title": article_title,
                                    "url": article_url,
                                    "page_text": article_text
                                })
                                logger.info(f"✅ 기업 관련 기사 추가됨: [{len(article_urls)}/{num_articles}] {article_url}")
                            else:
                                logger.warning(f"❌ 기업 관련 없음: {article_url}")

                        if len(article_urls) >= num_articles:
                            break

                    except Exception as e:
                        logger.warning(f"기사 URL 수집 중 오류 발생: {e}")

                last_collected_id = max_current_id

                if len(article_urls) < num_articles:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                    await asyncio.sleep(1.5)

            except Exception as e:
                logger.error(f"뉴스 기사 수집 중 오류 발생: {e}")
                break

    finally:
        # 동기 quit 호출이므로 await 제거
        sub_driver.quit()

    logger.info(f"총 {len(article_urls)}개의 기업 관련 기사 수집 완료")
    return article_urls

async def get_company_news(company_name: str, num_articles: int, api_key: str):
    os.makedirs(SAVE_PATH, exist_ok=True)
    client = OpenAI(api_key=api_key)
    driver = set_webdriver()
    
    try:
        search_url = f"{NAVER_SEARCH_URL}{company_name}"
        data = await get_news_contents(driver, search_url, num_articles, company_name, client)
        logger.info(f"{company_name} 뉴스 수집 완료. {len(data)}개 수집됨.")

        data = {
            "company_name": company_name,
            "collected_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S"),
            "news_data": data
        }

        save_json(data, f"{SAVE_PATH}/{company_name}.json")
        logger.info(f"기업 뉴스 수집 결과가 {SAVE_PATH}/{company_name}.json에 저장되었습니다.")

        # 동기 quit 호출
        driver.quit()
        return data
        
    except Exception as e:
        logger.error(f"기업 뉴스 수집 중 오류 발생 : {e}")
        return None