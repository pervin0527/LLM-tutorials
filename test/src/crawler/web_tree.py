import time
import logging

from collections import deque
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

BLOCK_FILE_EXT = {".pdf", ".zip", ".exe", ".rar", ".tar.gz", ".dmg", ".jpg", ".png", ".hwp"}

logger = logging.getLogger(__name__)

def set_webdriver(root_url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0.0.0 Safari/537.36")
    options.add_argument(f"user-agent={user_agent}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(root_url)
    time.sleep(0.5)
    return driver


def initialize_crawler(start_url):
    """
    크롤러 초기화:
      - visited: 방문한 URL 집합 (중복 방문 방지)
      - tree: URL을 key로 노드를 저장 (각 노드는 {"url", "text", "children"} 형태)
      - parent_map: 각 URL의 최초 부모 URL을 기록 (한 URL은 최초 부모와만 연결)
      - queue: BFS를 위한 (URL, 부모 URL) 튜플 큐
    """
    visited = set([start_url])
    tree = {}         # {url: {"url": url, "text": ..., "children": []}}
    parent_map = {}   # {자식 URL: 부모 URL} -> 각 노드는 단 한 부모만 가짐
    queue = deque([(start_url, None)])
    return visited, tree, parent_map, queue


def get_page_content(driver, url):
    """
    해당 URL의 페이지를 로드하고, <body> 태그의 텍스트를 반환합니다.
    """
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        content = driver.find_element(By.TAG_NAME, "body").text.strip()
        return content
    except Exception as e:
        logger.error(f"페이지 로드 오류: {e} (URL: {url})")
        return ""


def process_links(driver, current_url, start_url, visited):
    """
    현재 페이지에서 <a> 태그의 링크를 찾아, 내부 도메인 링크 중 아직 방문하지 않은 URL을 반환합니다.
    특정 파일 확장자 (*.pdf, *.zip 등) 링크는 제외합니다.
    """
    links_to_visit = []

    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href:
                absolute_url = urljoin(current_url, href)
                parsed_url = urlparse(absolute_url)
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

                # 특정 파일 확장자가 포함된 URL 필터링
                if any(clean_url.lower().endswith(ext) for ext in BLOCK_FILE_EXT):
                    logger.info(f"차단된 파일 URL: {clean_url}")
                    continue

                # 도메인이 같고, 아직 방문하지 않은 URL만 추가
                if parsed_url.netloc == urlparse(start_url).netloc and clean_url not in visited:
                    visited.add(clean_url)
                    links_to_visit.append(clean_url)
    except Exception as e:
        logger.error(f"링크 처리 오류: {e} (URL: {current_url})")
    
    return links_to_visit


def crawl_website(start_url):
    """
    BFS 방식으로 웹사이트를 크롤링합니다.
    각 URL은 한 번만 노드로 생성되며, 최초 발견된 부모와만 연결됩니다.
    """
    driver = set_webdriver(start_url)
    visited, tree, parent_map, queue = initialize_crawler(start_url)

    # 루트 노드 생성 (초기에는 text는 빈 문자열; 이후 get_page_content로 채움)
    tree[start_url] = {"url": start_url, "text": "", "children": []}

    while queue:
        current_url, parent = queue.popleft()

        # 현재 URL에 대해 노드가 없다면 새로 생성
        if current_url not in tree:
            page_text = get_page_content(driver, current_url)
            tree[current_url] = {"url": current_url, "text": page_text, "children": []}
        else:
            # 노드가 있지만 text가 비어있다면 업데이트 (선택 사항)
            if not tree[current_url]["text"]:
                page_text = get_page_content(driver, current_url)
                tree[current_url]["text"] = page_text

        # 부모가 있다면, 아직 부모-자식 연결이 이루어지지 않은 경우에만 연결
        if parent is not None and current_url not in parent_map:
            parent_map[current_url] = parent
            tree[parent]["children"].append(tree[current_url])
        
        # 현재 페이지에서 새로운 링크들을 추출
        new_links = process_links(driver, current_url, start_url, visited)
        for link in new_links:
            # 새 노드이면 큐에 추가 (이미 visited에 추가되어 있으므로 중복 없음)
            if link not in tree:
                queue.append((link, current_url))
            # 이미 노드가 존재하면 최초 부모와의 연결만 유지
            
    driver.quit()
    # 최종 트리의 루트 노드는 start_url에 해당하는 노드입니다.
    return tree[start_url]


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