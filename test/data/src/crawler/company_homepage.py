import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from collections import deque
from urllib.parse import urljoin, urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.selenium_utils import set_webdriver
from src.crawler.utils.data_utils import save_json, transform_data, clean_text

from app.utils.logging import logger

SAVE_PATH = "./data/company_homepage"
BLOCK_FILE_EXT = {".pdf", ".zip", ".exe", ".rar", ".tar.gz", ".dmg", ".jpg", ".png", ".hwp", ".doc", ".xlsx", ".pptx", ".ppt", ".docx", ".txt", ".pdf"}

# 전역 ThreadPoolExecutor 생성
executor = ThreadPoolExecutor(max_workers=3)

def google_search_homepage(driver:WebDriver, company_name:str):
    logger.info(f"google 검색 시작: {company_name}")
    try:
        driver.get(f"https://www.google.com/search?q={company_name}+기업+홈페이지")
        time.sleep(0.5)

        container = driver.find_element(By.XPATH, '//*[@id="rso"]')
        items = container.find_elements(By.TAG_NAME, 'div')
        
        return items[0].find_element(By.TAG_NAME, 'a').get_attribute("href")

    except Exception as e:
        logger.warning(f"구글 검색 실패: {e}")
        return None 


def initialize_crawler(driver, start_url):
    logger.info(f"크롤러 초기화 시작: {start_url}")
    driver.get(start_url)
    time.sleep(1.5)
    
    # 리다이렉션 후의 실제 URL을 사용
    actual_url = driver.current_url
    visited = set([actual_url])
    tree = {}
    parent_map = {}
    queue = deque([(actual_url, None)])
    logger.info("크롤러 초기화 완료")
    return visited, tree, parent_map, queue


def get_page_content(driver, url):
    logger.info(f"페이지 로드 시작: {driver.current_url}")
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 페이지 이동 후 차단된 파일 유형인지 확인
        current_url = driver.current_url
        if any(urlparse(current_url).path.lower().endswith(ext) for ext in BLOCK_FILE_EXT):
            logger.info(f"차단된 파일 URL 감지됨, 페이지 스킵: {current_url}")
            return ""

        content = driver.find_element(By.TAG_NAME, "body").text.strip()
        logger.info(f"페이지 로드 완료: {driver.current_url}")
        return content
    
    except Exception as e:
        logger.error(f"URL: {url} 페이지 오류: {e}")
        return ""


def process_links(driver, current_url, start_url, visited, max_pages):
    logger.info(f"링크 처리 시작: {driver.current_url}")

    start_domain = urlparse(driver.current_url).netloc 
    links_to_visit = []
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href:
                absolute_url = urljoin(current_url, href)
                parsed_url = urlparse(absolute_url)
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

                if any(clean_url.lower().endswith(ext) for ext in BLOCK_FILE_EXT):
                    logger.info(f"차단된 파일 URL: {clean_url}")
                    continue

                # 도메인이 같고, 아직 방문하지 않은 URL만 추가
                if parsed_url.netloc == start_domain and clean_url not in visited:
                    # 방문 제한에 도달하지 않았을 때만 추가
                    if len(visited) < max_pages:
                        visited.add(clean_url)
                        links_to_visit.append(clean_url)
                        logger.info(f"새로운 링크 발견: {clean_url}")
                    else:
                        logger.info("방문 페이지 제한에 도달하여 새로운 링크 추가 중단")
                        break  # 또는 continue로 처리할 수도 있음
    except Exception as e:
        logger.error(f"링크 처리 오류: {e} (URL: {current_url})")
    
    logger.info(f"링크 처리 완료, 발견된 링크 수: {len(links_to_visit)}")
    return links_to_visit


def clean_tree(node, seen=None):
    """
    재귀적으로 트리를 순회하면서 아래 두 조건을 만족하지 않는 노드를 제거합니다.
      1. 동일 URL의 노드가 여러 번 등장하면, 최초 노드만 남깁니다.
      2. text 값이 빈 문자열("")이면 해당 노드를 제거합니다.
      
    반환 값은 정리된 노드이며, 만약 현재 노드를 제거해야 한다면 None을 반환합니다.
    """
    if seen is None:
        seen = set()
        
    url = node.get("url")
    # 이미 등장한 URL이면 중복이므로 제거
    if url in seen:
        return None
    seen.add(url)
    
    # text 값이 비어있다면 해당 노드 제거 (자식 노드들은 버림)
    if not node.get("text", "").strip():
        return None

    # 자식 노드들에 대해 재귀 처리
    new_children = []
    for child in node.get("children", []):
        cleaned_child = clean_tree(child, seen)
        if cleaned_child is not None:
            new_children.append(cleaned_child)
    node["children"] = new_children
    return node


# 기존 동기 함수들은 유지하고 비동기 래퍼 함수 추가
async def google_search_homepage_async(driver: WebDriver, company_name: str):
    return await asyncio.get_event_loop().run_in_executor(
        executor, google_search_homepage, driver, company_name
    )

async def initialize_crawler_async(driver: WebDriver, start_url: str):
    return await asyncio.get_event_loop().run_in_executor(
        executor, initialize_crawler, driver, start_url
    )

async def get_page_content_async(driver: WebDriver, url: str):
    return await asyncio.get_event_loop().run_in_executor(
        executor, get_page_content, driver, url
    )

async def process_links_async(driver: WebDriver, current_url: str, start_url: str, visited: set, max_pages: int):
    return await asyncio.get_event_loop().run_in_executor(
        executor, process_links, driver, current_url, start_url, visited, max_pages
    )

async def get_company_homepage(company_name: str, start_url: str = None, max_pages: int = 100):
    """
    기업 홈페이지를 비동기적으로 크롤링하는 함수
    """
    try:
        os.makedirs(SAVE_PATH, exist_ok=True)
        
        driver = set_webdriver()
        if start_url:
            logger.info(f"시작 URL 제공: {start_url}")
            visited, tree, parent_map, queue = await initialize_crawler_async(driver, start_url)
        else:
            logger.info(f"시작 URL이 제공되지 않아 google 검색 시작")
            start_url = await google_search_homepage_async(driver, company_name)
            logger.info(f"구글 검색 결과: {start_url}")
            visited, tree, parent_map, queue = await initialize_crawler_async(driver, start_url)
            start_url = driver.current_url

        logger.info(f"초기화 및 페이지 로드 완료 : {start_url}")
        tree[start_url] = {"url": start_url, "text": "", "children": []}
        
        while queue:
            current_url, parent = queue.popleft()

            if current_url not in tree:
                page_text = await get_page_content_async(driver, current_url)
                # 여기서 노이즈 제거
                page_text = clean_text(page_text)
                tree[current_url] = {"url": current_url, "text": page_text, "children": []}
            else:
                if not tree[current_url]["text"]:
                    page_text = await get_page_content_async(driver, current_url)
                    # 여기서 노이즈 제거
                    page_text = clean_text(page_text)
                    tree[current_url]["text"] = page_text

            if parent is not None and current_url not in parent_map:
                parent_map[current_url] = parent
                tree[parent]["children"].append(tree[current_url])
            
            # 새로운 링크를 추출할 때 max_pages를 함께 전달
            new_links = await process_links_async(driver, current_url, start_url, visited, max_pages)
            for link in new_links:
                # 이미 visited에 추가되어 있으므로 중복 없이 큐에 넣음
                if link not in tree:
                    queue.append((link, current_url))
        
        # 여기서도 노이즈 제거
        data = transform_data(tree[start_url], company_name)
        for page in data.get('pages', []):
            page['text'] = clean_text(page['text'])
        
        save_json(data, f"{SAVE_PATH}/{company_name}.json")
        logger.info(f"기업 홈페이지 데이터가 {SAVE_PATH}/{company_name}.json에 저장되었습니다.")
        
        driver.quit()
        return data
    
    except Exception as e:
        logger.error(f"기업 홈페이지 크롤링 중 오류 발생: {e}")
        return None
