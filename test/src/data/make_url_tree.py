import os
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

def get_links_and_text(driver, url, root_url):
    """ 주어진 URL에서 내부 링크와 페이지의 텍스트 콘텐츠를 가져옴 """
    try:
        driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기

        driver.execute_script("window.localStorage.clear();")  # 로컬 스토리지 삭제
        driver.execute_script("window.sessionStorage.clear();")  # 세션 스토리지 삭제
        driver.delete_all_cookies()  # 쿠키 삭제
        # print("✅ 캐시 및 쿠키 삭제 완료")

        for i in range(2):
            driver.refresh()
            # print("✅ 새로고침 완료")

        # 모든 내부 링크 가져오기
        links = set()
        elements = driver.find_elements(By.TAG_NAME, "a")
        for elem in elements:
            link = elem.get_attribute("href")
            if link and link.startswith(root_url):  # 내부 링크만 저장
                links.add(link)

        # 페이지의 텍스트 콘텐츠 가져오기
        page_content = driver.find_element(By.TAG_NAME, "body").text

        return links, page_content.strip()
    
    except Exception as e:
        print(f"Error while accessing {url}: {e}")
        return set(), ""

def crawl_website(root_name, root_url, max_depth=2, save_path="./"):
    """ 특정 사이트를 시작으로 내부 링크를 크롤링 (Depth별로 저장) 및 페이지 텍스트 저장 """
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    site_structure = {}  # Depth별 URL 저장
    page_contents = {}  # URL별 텍스트 저장
    visited = {}  # 방문한 URL 저장 (url: depth)

    def crawl(url, depth):
        if depth > max_depth or url in visited:
            return
        visited[url] = depth

        print(f"Crawling: {url} (Depth: {depth})")
        child_links, page_text = get_links_and_text(driver, url, root_url)

        # Depth별로 URL 저장
        if depth not in site_structure:
            site_structure[depth] = []
        site_structure[depth].append(url)

        # URL별 텍스트 저장
        page_contents[url] = page_text

        for link in child_links:
            crawl(link, depth + 1)

    crawl(root_url, 0)
    driver.quit()

    # JSON 파일 저장 (사이트 구조)
    with open(f"{save_path}/{root_name}_site_structure.json", "w", encoding="utf-8") as f:
        json.dump(site_structure, f, indent=4, ensure_ascii=False)

    # JSON 파일 저장 (페이지 콘텐츠)
    with open(f"{save_path}/{root_name}_page_contents.json", "w", encoding="utf-8") as f:
        json.dump(page_contents, f, indent=4, ensure_ascii=False)

    return site_structure, page_contents