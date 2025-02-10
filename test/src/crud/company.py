import json

from datetime import datetime

from app.utils.logging import logger

def search_company(collection, company_name):
    """MongoDB에서 특정 회사 데이터를 검색"""
    document = collection.find_one({"company": company_name}, {"_id": 0})  # _id 필드 제외
    
    if document:
        logger.info(json.dumps(document, indent=4, ensure_ascii=False))
        return document
    else:
        logger.error("❌ 해당 회사의 데이터가 없습니다.")
        return None
    

def update_company(collection, company_name, url):
    """MongoDB에서 특정 회사를 다시 크롤링"""

    if collection is None:
        logger.error("❌ MongoDB 컬렉션을 찾을 수 없습니다.")
        return {"success": False, "message": "MongoDB 연결 실패"}
    
    docs = search_company(collection, company_name)
    if docs is None:
        logger.error(f"❌ {company_name} 데이터를 찾을 수 없습니다.")
        return {"success": False, "message": f"{company_name} 데이터를 찾을 수 없습니다."}

    collection.update_one({"company": company_name}, {"$set": {"url": url, "updated_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S")}})
    logger.info(f"✅ {company_name} 데이터가 업데이트되었습니다.")
    return {"success": True, "message": "회사 업데이트 성공"}


def delete_company(collection, vector_store, company_name):
    """MongoDB에서 특정 회사의 모든 데이터를 삭제"""
    result = collection.delete_one({"company": company_name})
    
    if result.deleted_count > 0:
        logger.info(f"✅ {company_name}의 모든 데이터가 DB에서 삭제되었습니다.")
        
        # 벡터 데이터베이스에서도 회사 데이터 삭제
        vector_store.delete_company(company_name)
        logger.info(f"✅ {company_name}의 모든 데이터가 벡터 데이터베이스에서 삭제되었습니다.")
        return {"success": True, "message": "회사 데이터 삭제 성공"}
    else:
        logger.warning(f"❌ {company_name} 회사를 DB에서 찾을 수 없습니다.")
        return {"success": False, "message": "회사를 찾을 수 없습니다"}


def get_all_companies(collection):
    """
    MongoDB에 저장된 모든 회사 데이터를 가져오는 함수.

    :param collection: MongoDB 컬렉션 객체
    :return: 모든 회사 데이터 목록
    """
    if collection is None:
        logger.error("❌ MongoDB 컬렉션을 찾을 수 없습니다.")
        return {"success": False, "message": "MongoDB 연결 실패"}

    # 모든 회사 데이터 조회 (_id 제외)
    companies = list(collection.find({}, {"_id": 0}))

    if not companies:
        logger.warning("⚠️ 저장된 회사 데이터가 없습니다.")
        return {"success": False, "message": "저장된 회사 데이터가 없습니다."}

    return {"success": True, "data": companies}
