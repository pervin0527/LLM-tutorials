from fastapi import APIRouter, HTTPException, Request

from src.crawler.web_tree import crawl_website
from src.crawler.utils import transform_data, save_tree

from src.db.mongo import save_to_mongo, connect_to_mongo
from src.rag.data.dataset import convert_to_documents

from app.utils.logging import logger

router = APIRouter()

@router.post("/crawler/crawling_company")
def crawl_website_api(request: Request, root_url: str, root_name: str):
    try:
        web_tree = crawl_website(root_url)
        formatted_data = transform_data(web_tree, root_name)

        collection = connect_to_mongo()
        save_to_mongo(collection, formatted_data)

        documents = convert_to_documents(formatted_data)
        
        try:
            logger.info("벡터 DB에 문서 추가 중...")
            vector_db = request.app.state.vector_store.vector_db
            vector_db.add_documents(documents)
            logger.info("✅ 벡터 DB에 문서 추가 완료")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"벡터 데이터베이스에 문서 추가 중 오류 발생: {str(e)}")

        return {"status": True, "message": "크롤링 및 저장 성공", "data": formatted_data}
    
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        logger.error(f"vector_db type : {type(vector_db)}, documents_type : {type(documents)}, document_type : {type(documents[0])}")
        logger.error(f"vector_db.add_documents type: {type(vector_db.add_documents)}")
        logger.error(f"vector_db.add_texts type: {type(vector_db.add_texts)}")


        return {"status": False, "message": f"크롤링 실패: {e}"} 
