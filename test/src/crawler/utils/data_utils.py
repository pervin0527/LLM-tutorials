import re
import json

from typing import Optional
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from app.utils.logging import logger


def save_json(data, filename="crawl_result.json"):
    """크롤링 결과를 JSON 파일로 저장"""

    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
        
    logger.info(f"크롤링 결과가 {filename} 파일로 저장되었습니다.")


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


def normalize_url(url: str) -> str:
    """URL을 정규화하는 함수
    
    Args:
        url (str): 정규화할 URL 문자열
    
    Returns:
        str: 정규화된 URL 문자열
        
    Examples:
        >>> normalize_url("www.koreaedugroup.com")
        "http://www.koreaedugroup.com"
        >>> normalize_url("koreaedugroup.com")
        "http://www.koreaedugroup.com"
    """
    if not url:
        return ""
    
    # 프로토콜이 없는 경우 http:// 추가
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # URL 파싱
    parsed = urlparse(url)
    
    # 도메인을 소문자로 변환하고 www가 없으면 추가
    netloc = parsed.netloc.lower()
    if not netloc.startswith('www.'):
        netloc = 'www.' + netloc
    
    # 경로 정규화 - 슬래시 완전히 제거
    path = parsed.path.strip('/')
    if path:
        path = '/' + path
    
    # URL 재조립
    normalized = urlunparse((
        'http',  # 프로토콜은 http로 통일
        netloc,  # 정규화된 도메인 (www 포함)
        path,    # 정규화된 경로
        '',      # params 제거
        '',      # query 제거
        ''       # fragment 제거
    )).rstrip('/')  # 마지막에 한번 더 슬래시 제거
    
    return normalized


def extract_company_id(url: str) -> Optional[str]:
    """
    URL에서 /companies/ 뒤에 나오는 숫자(기업 ID)를 추출합니다.
    예) 'https://www.jobplanet.co.kr/companies/93880/premium_reviews/카카오' → '93880'
    """
    pattern = r'/companies/(\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None