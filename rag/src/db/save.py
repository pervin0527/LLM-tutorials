from datetime import datetime
from pymongo import MongoClient

# MongoDB 연결 설정 (authSource=admin 추가)
mongo_client = MongoClient("mongodb://ai:glab0110!!@43.203.206.127:27017/?authSource=admin")
mongo_db = mongo_client["wanted"]
mongo_collection = mongo_db["recruitments"]

def save_crawl_data(final_response: dict):
    current_time = datetime.utcnow()
    final_response['created_at'] = current_time
    final_response['updated_at'] = current_time
    final_response['process_flag'] = False
    mongo_collection.insert_one(final_response)