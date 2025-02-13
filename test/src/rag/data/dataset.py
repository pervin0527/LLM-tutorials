from uuid import uuid4
from langchain.docstore.document import Document

from app.utils.logging import logger
from src.db.mongo import connect_to_mongo
from src.crud.company import get_all_companies

def load_documents_from_db(db_name, collection_name):
    collection = connect_to_mongo(db_name, collection_name)
    if collection is None:
        logger.warning(f"❌ {db_name} - {collection_name} 연결 실패")
        return []
    
    logger.info(f"✅ {db_name} - {collection_name} 연결 성공")

    # 모든 회사 데이터 가져오기
    result = get_all_companies(collection)
    if not result["success"]:
        logger.error(result["message"])
        return []

    all_companies = result["data"]
    total_docs = []
    for company in all_companies:
        company_name = company.get("company", "Unknown")
        company_id = company.get("company_id", "Unknown")
        pages = company.get("pages", [])

        logger.info(f"{company_name} - {len(pages)}")

        documents = [
            Document(
                page_content=page["text"],
                metadata={"company_name": company_name, "url": page["url"], "company_id": company_id},
                id=uuid4()
            )
            for page in pages
        ]
        total_docs.extend(documents)

    return total_docs


def convert_to_documents(formatted_data):
    try:
        # pages 리스트 가져오기
        pages = formatted_data.get("pages", [])

        # Document 객체 리스트 생성
        documents = [
            Document(
                page_content=item["text"],
                metadata={
                    "company": formatted_data.get("company", ""),
                    "url": item.get("url", ""),
                    "company_id": formatted_data.get("company_id", ""),
                },
                id=uuid4()
            )
            for item in pages
        ]

        logger.info(f"✅ 문서 변환 완료: {len(documents)}개")
        return documents

    except Exception as e:
        logger.error(f"❌ 문서 변환 중 오류 발생: {str(e)}")
        return []
