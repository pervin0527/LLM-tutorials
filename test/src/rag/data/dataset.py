import logging

from uuid import uuid4
from langchain.docstore.document import Document

from src.db.mongo import connect_to_mongo
from src.crud.company import get_all_companies

logger = logging.getLogger(__name__)

def load_documents_from_db():
    collection = connect_to_mongo()
    if collection is None:
        logger.warning("MongoDB collection is None.")
        return []

    # 모든 회사 데이터 가져오기
    result = get_all_companies(collection)
    if not result["success"]:
        logger.error(result["message"])
        return []

    all_companies = result["data"]
    total_docs = []
    for company in all_companies:
        company_name = company.get("company", "Unknown")
        pages = company.get("pages", [])

        logger.info(f"{company_name} - {len(pages)}")

        documents = [
            Document(
                page_content=page["text"],
                metadata={"company_name": company_name, "url": page["url"]},
                id=uuid4()
            )
            for page in pages
        ]
        total_docs.extend(documents)

    return total_docs