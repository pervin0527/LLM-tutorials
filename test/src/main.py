import os
import json
from datetime import datetime
from pymongo import MongoClient
import logging

from crawler.web_tree import crawl_website
from crawler.utils import save_tree, transform_data

from db.mongo import connect_to_mongo, save_to_mongo, search_company, update_page_content

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    os.makedirs("./data", exist_ok=True)
    
    root_name = "현대자동차그룹"
    # root_url = "https://audit.hyundai.com/"
    # web_tree = crawl_website(root_url)
    # save_tree(web_tree, f"./data/{root_name}.json")

    with open(f"./data/{root_name}.json", "r", encoding="utf-8") as file:
        web_tree = json.load(file)

    formatted_data = transform_data(web_tree, root_name)
    save_tree(formatted_data, f"./data/{root_name}_normalized.json")

    collection = connect_to_mongo()
    save_to_mongo(collection, formatted_data)
    search_company(collection, root_name)

    update_page_content(
        root_name="현대자동차그룹",
        target_url="https://audit.hyundai.com/",
        new_url="https://new.audit.hyundai.com/",
        new_text="업데이트된 윤리경영 텍스트입니다."
    )

if __name__ == "__main__":
    main()