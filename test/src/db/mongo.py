import json
import logging

from datetime import datetime
from pymongo import MongoClient

logger = logging.getLogger(__name__)

def connect_to_mongo():
    """MongoDB 연결"""
    try:
        client = MongoClient("mongodb://ai:glab0110!!@local-mongodb:27017/?authSource=admin")
        db = client["culture_db"]
        collection = db["company_websites"]
        logger.info("✅ MongoDB 연결 성공")
        return collection
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 실패: {e}")
        return None
    
    
def save_to_mongo(collection, data):
    """크롤링 데이터를 MongoDB에 저장"""
    if collection is None:
        logger.error("❌ MongoDB 연결이 없으므로 저장할 수 없습니다.")
        return
    
    existing_data = collection.find_one({"company": data["company"]})
    if existing_data:
        data["updated_date"] = datetime.today().strftime("%y.%m.%d-%H:%M:%S")
    
    collection.update_one(
        {"company": data["company"]},
        {"$set": data},
        upsert=True
    )
    logger.info(f"✅ {data['company']} 데이터가 MongoDB에 저장되었습니다.")