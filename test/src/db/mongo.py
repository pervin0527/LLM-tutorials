import json

from datetime import datetime
from pymongo import MongoClient

from app.utils.logging import logger


def connect_to_mongo(db_name,collection_name):
    """MongoDB 연결"""
    try:
        client = MongoClient("mongodb://ai:glab0110!!@local-mongodb:27017/?authSource=admin")
        db = client[db_name]
        collection = db[collection_name]
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
    
    try:
        existing_data = collection.find_one({"company": data["company"]})
        if existing_data:
            data["updated_date"] = datetime.today().strftime("%y.%m.%d-%H:%M:%S")
        
        collection.update_one(
            {"company": data["company"]},
            {"$set": data},
            upsert=True
        )
        logger.info(f"✅ {data['company']} 데이터가 MongoDB에 저장되었습니다.")
    
    except Exception as e:
        logger.error(f"❌ MongoDB 저장 중 오류 발생: {e}")
        return {"status": False, "message": f"MongoDB 저장 중 오류 발생: {e}"}
