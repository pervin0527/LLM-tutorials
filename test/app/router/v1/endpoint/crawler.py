from fastapi import APIRouter, HTTPException, Request

from src.crawler.web_tree import crawl_website
from src.crawler.jobplanet import crawl_jobplanet
from src.crawler.utils import transform_data, save_tree

from src.db.mongo import save_to_mongo, connect_to_mongo
from src.rag.data.dataset import convert_to_documents

from app.utils.logging import logger

router = APIRouter()

@router.post("/crawler/crawling_company")
def crawl_website_api(request: Request, company_name: str, start_url: str):
    try:
        web_tree = crawl_website(start_url)
        formatted_data = transform_data(web_tree, company_name)
        save_tree(formatted_data, f"./data/{company_name}.json")
        logger.info(f"크롤링 결과가 ./data/{company_name}.json에 저장되었습니다.")

        collection = connect_to_mongo("culture_db", "company_websites")
        save_to_mongo(collection, formatted_data)

        documents = convert_to_documents(formatted_data)

        # 벡터 데이터베이스에서 기존 문서 확인 및 업데이트
        vector_store = request.app.state.vector_store

        if vector_store is None:
            logger.error("벡터 스토어가 초기화되지 않았습니다.")
            return

        existing_documents = vector_store.get_company_documents(company_name)

        for doc in documents:
            existing_doc = next((d for d in existing_documents if d['url'] == doc.metadata['url']), None)
            if existing_doc:
                # 문서 업데이트
                # vector_store.update_document(root_name, doc.metadata['url'], new_text=doc.page_content)
                # logger.info(f"문서 업데이트 완료: {doc.metadata['url']}")
                continue
            else:
                # 새 문서 추가
                vector_store.vector_db.add_documents([doc])
                logger.info(f"새 문서 추가 완료: {doc.metadata['url']}")

        return {"status": True, "message": "크롤링 및 저장 성공", "data": formatted_data}
    
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        return {"status": False, "message": f"크롤링 실패: {e}"} 


@router.post("/crawler/crawling_jobplanet")
def crawl_jobplanet_api(request: Request, company_name: str):
    crawl_jobplanet(company_name)
    return {"status": True, "message": "잡플래닛 크롤링 성공"}