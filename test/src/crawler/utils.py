import os
import json

from datetime import datetime

def save_tree(tree, filename="crawl_result.json"):
    """크롤링 결과를 JSON 파일로 저장"""

    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(tree, json_file, ensure_ascii=False, indent=4)
        
    print(f"크롤링 결과가 {filename} 파일로 저장되었습니다.")


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