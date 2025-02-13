from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient

from app.utils.logging import logger


def connect_to_mongo(db_name, collection_name):
    """MongoDB 연결"""
    try:
        client = MongoClient("mongodb://ai:glab0110!!@local-mongodb:27017/?authSource=admin")
        db = client[db_name]
        collection = db[collection_name]
        # logger.info(f"✅ {db_name} - {collection_name} 연결 성공")
        return collection
    
    except Exception as e:
        # logger.error(f"❌ {db_name} - {collection_name} 연결 실패: {e}")
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


def get_or_create_company(company_name: str, homepage: str = None):
    """기업 정보를 company 컬렉션에서 조회하거나 추가"""
    collection = connect_to_mongo("culture_db", "company")
    
    # ✅ 기존 데이터가 있는지 정확히 확인
    company = collection.find_one({"company_name": company_name})
    if company:
        return str(company["_id"])  # 기존 `_id` 반환

    # ✅ 존재하지 않으면 새로 추가
    new_company = {
        "company_name": company_name,
        "homepage": homepage,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = collection.insert_one(new_company)

    logger.info(f"새로운 회사 추가: {company_name}, company_id: {str(result.inserted_id)}")

    return str(result.inserted_id)  # 새로 생성된 `_id` 반환


def get_company(company_name:str):
    collection = connect_to_mongo("culture_db", "company")
    company = collection.find_one({"company_name": company_name})
    return company


def convert_objectid_to_str(data):
    """MongoDB에서 가져온 데이터를 JSON 변환 가능하도록 처리"""
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    return data