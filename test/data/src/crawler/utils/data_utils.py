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
        "company_name": company_name,
        "collected_date": current_time,
        "updated_date": None,
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


def format_business_number(biz_number: str) -> str:
    """
    사업자 등록번호를 표준 형식(XXX-XX-XXXXX)으로 변환
    """
    try:
        # 숫자만 추출
        digits = re.sub(r'\D', '', biz_number)
        
        # 길이 확인 및 패딩
        if len(digits) > 10:
            digits = digits[:10]
        elif len(digits) < 10:
            digits = digits.zfill(10)
            
        # 형식 변환
        formatted_number = f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
        logger.debug(f"Formatted business number: {biz_number} -> {formatted_number}")
        return formatted_number
        
    except Exception as e:
        logger.error(f"Business number formatting failed: {biz_number} - {str(e)}")
        return biz_number  # 오류 시 원본 반환


def clean_text(text):
    # 불필요한 노이즈 문자 및 공백 제거
    cleaned_text = re.sub(r'[\n�߸]+', ' ', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text


def clean_company_name(company_name: str) -> str:
    """
    기업명에서 불필요한 접두어 및 특수문자를 제거하는 함수

    Args:
        company_name (str): 원본 기업명

    Returns:
        str: 정제된 기업명
    """
    # 제거할 패턴 정의
    noise_patterns = [
        r"^\(주\)",  # (주)
        r"^㈜",  # ㈜ (특수문자)
        r"^주식회사",  # 주식회사
        r"\s*㈜\s*",  # 공백 포함된 ㈜
        r"\s*\(주\)\s*",  # 공백 포함된 (주)
        r"\s*주식회사\s*"  # 공백 포함된 주식회사
    ]
    
    # 패턴 순차적으로 제거
    for pattern in noise_patterns:
        company_name = re.sub(pattern, "", company_name).strip()
    
    return company_name