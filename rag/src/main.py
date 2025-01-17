import os
import logging

from utils.config import load_config
from data.dataset import connect_to_db, get_dataset

from data.dataset import get_documents
from retriever.keyword import BM25Retriever
from retriever.semantic import SemanticRetriever

from dotenv import load_dotenv
load_dotenv("../keys.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

from logging import getLogger
logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    cfg = load_config("../configs/config.yaml")
    logger.info(f"Config Successfully Loaded")

    connection = connect_to_db(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    logger.info(f"DB Connection Successfully Established")
    
    query = """
        SELECT * 
        FROM recruit
        WHERE platform_type IN ('WANTED');
    """
    dataset = get_dataset(connection, query)[:1000]
    documents = get_documents(dataset, cfg['page_content_fields'], cfg['metadata_fields'])
    logger.info(f"Dataset Successfully Loaded")

    keyword_retriever = BM25Retriever.from_documents(
        documents=documents,
        bm25_params=cfg['bm25_params'],
        tokenizer_method=cfg['tokenizer']
    )
    query = "프론트엔드"
    results = keyword_retriever.search_with_score(query, top_k=2)
    for i, (doc, score) in enumerate(results):
        print(f"[{i + 1}] Score: {score:.4f}\n {doc.page_content}")

    semantic_retriever = SemanticRetriever(cfg, dataset)
    results = semantic_retriever.similarity_search_with_score("프론트엔드 개발자 공고 찾아줘.", k=5)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    for res, score in results:
        print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")


if __name__ == "__main__":
    main()