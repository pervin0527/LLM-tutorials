import json

from datetime import datetime
from langchain.docstore.document import Document

from app.utils.logging import logger


def search_page(collection, root_name, target_url):
    """
    특정 회사 데이터를 조회한 후, 해당 페이지의 URL 또는 텍스트를 수정하고 저장하는 함수.
    """
    if collection is None:
        logger.error("❌ MongoDB 컬렉션을 찾을 수 없습니다.")
        return {"success": False, "message": "MongoDB 연결 실패"}

    document = collection.find_one({"company": root_name})
    if document is None:
        logger.error(f"❌ {root_name} 데이터를 찾을 수 없습니다.")
        return {"success": False, "message": f"{root_name} 데이터를 찾을 수 없습니다."}

    for page in document.get("pages", []):
        if page["url"] == target_url:
            return {"success": True, "data": page}

    logger.error(f"❌ {target_url} 페이지를 찾을 수 없습니다.")
    return {"success": False, "message": f"{target_url} 페이지를 찾을 수 없습니다."}


def add_new_page(collection, company_name, url, text, vector_store):
    """
    특정 회사의 데이터를 확인하고, 존재하면 신규 페이지를 등록하는 함수.

    :param company_name: 회사명 (company)
    :param url: 추가할 페이지 URL
    :param text: 추가할 페이지 내용
    """
    if collection is None:
        logger.error("❌ MongoDB 컬렉션을 찾을 수 없습니다.")
        return {"success": False, "message": "MongoDB 연결 실패"}

    # 해당 회사 데이터 검색
    document = collection.find_one({"company": company_name})
    if document is None:
        logger.error(f"❌ {company_name} 데이터를 찾을 수 없습니다.")
        return {"success": False, "message": f"{company_name} 데이터를 찾을 수 없습니다."}

    # 기존 페이지 목록 가져오기
    pages = document.get("pages", [])

    # 중복 확인 (이미 존재하는 URL이면 추가하지 않음)
    for page in pages:
        if page["url"] == url:
            logger.error(f"❌ {company_name}의 {url} 페이지가 이미 존재합니다.")
            return {"success": False, "message": f"{url} 페이지가 이미 존재합니다."}

    # 새로운 페이지 추가
    pages.append({"url": url, "text": text})
    
    # MongoDB 업데이트
    collection.update_one(
        {"company": company_name},
        {"$set": {"pages": pages, "updated_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S")}}
    )
    logger.info(f"✅ {company_name}의 새로운 페이지 {url} 등록 성공.")

    vector_store.vector_db.add_documents([Document(page_content=text, metadata={"url": url, "company_name": company_name})])
    logger.info(f"✅ {company_name}의 새로운 페이지 {url} 벡터 데이터베이스에 등록 성공.")
    
    return {"success": True, "message": "신규 페이지 등록 성공", "new_page": {"url": url, "text": text}}


def update_page_content(collection, vector_store, company_name, target_url, new_url=None, new_text=None,):
    """
    특정 회사 데이터를 조회한 후, 해당 페이지의 URL 또는 텍스트를 수정하고 저장하는 함수.

    :param collection: MongoDB 컬렉션 객체
    :param company_name: 수정할 대상 회사명 (company)
    :param target_url: 수정할 페이지의 기존 URL
    :param new_url: 변경할 새로운 URL (선택)
    :param new_text: 변경할 새로운 텍스트 (선택)
    :return: 성공 여부 및 메시지
    """
    if collection is None:
        logger.error("❌ MongoDB 컬렉션을 찾을 수 없습니다.")
        return {"success": False, "message": "MongoDB 연결 실패"}

    # 해당 회사 데이터 검색
    document = collection.find_one({"company": company_name})
    if document is None:
        logger.error(f"❌ {company_name} 데이터를 찾을 수 없습니다.")
        return {"success": False, "message": f"{company_name} 데이터를 찾을 수 없습니다."}

    # `pages` 리스트에서 target_url을 가진 페이지 찾기
    updated = False
    for page in document.get("pages", []):
        if page["url"] == target_url:
            if new_url:
                page["url"] = new_url
            if new_text:
                page["text"] = new_text
            updated = True
            break

    if not updated:
        logger.error(f"❌ {target_url} 페이지를 찾을 수 없습니다.")
        return {"success": False, "message": f"{target_url} 페이지를 찾을 수 없습니다."}
    
    # MongoDB에 업데이트
    collection.update_one(
        {"company": company_name},
        {"$set": {"pages": document["pages"], "updated_date": datetime.today().strftime("%y.%m.%d-%H:%M:%S")}}
    )
    logger.info(f"✅ {company_name}의 {target_url} 페이지가 성공적으로 업데이트되었습니다.")

    vector_store.update_document(company_name, target_url, new_text, new_url)
    logger.info(f"✅ {company_name}의 {target_url} 페이지가 벡터 데이터베이스에 성공적으로 업데이트되었습니다.")

    return {"success": True, "message": "페이지 업데이트 성공", "updated_page": {"url": new_url or target_url, "text": new_text}}


def delete_page(collection, vector_store, company_name, target_url):
    
    result = collection.update_one(
        {"company": company_name},
        {"$pull": {"pages": {"url": target_url}}}
    )
    
    if result.modified_count > 0:
        logger.info(f"✅ {company_name}의 {target_url} 페이지가 DB에서 삭제되었습니다.")
        
        # 벡터 데이터베이스에서도 삭제
        vector_store.delete_document(company_name, target_url)
        logger.info(f"✅ {company_name}의 {target_url} 페이지가 벡터 데이터베이스에서 삭제되었습니다.")
        return {"success": True, "message": "페이지 삭제 성공"}
    else:
        logger.warning(f"❌ {company_name}의 {target_url} 페이지를 DB에서 찾을 수 없습니다.")
        return {"success": False, "message": "페이지를 찾을 수 없습니다"}