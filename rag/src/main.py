import os
import logging

from datetime import datetime

from utils.config import load_config
from data.dataset import connect_to_db, get_dataset, get_documents

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
    
    db_query = """
        SELECT * 
        FROM recruit
        WHERE platform_type IN ('WANTED');
    """
    dataset = get_dataset(connection, db_query)[:100]
    documents = get_documents(dataset, cfg['page_content_fields'], cfg['metadata_fields'])
    logger.info(f"Dataset Successfully Loaded")

    now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    cfg['save_path'] = f"{cfg['save_path']}/{now}"
    os.makedirs(cfg['save_path'], exist_ok=True)

    keyword_retriever = BM25Retriever.from_documents(
        documents=documents,
        bm25_params=cfg['bm25_params'],
        tokenizer_method=cfg['tokenizer'],
        save_path=cfg['save_path'],
        load_path=cfg.get('load_path'),
        k=cfg.get('k', 4)
    )

    query = "딥러닝 개발자 채용공고들을 보여줘."
    results = keyword_retriever.search_with_score(query, top_k=cfg['topk'])
    for i, (doc, score) in enumerate(results):
        print(f"[{i + 1}] Score: {score:.4f}\n {doc.page_content}\n\n")

    semantic_retriever = SemanticRetriever(cfg, documents)
    results = semantic_retriever.similarity_search_with_score(query, k=cfg['topk'])
    results = sorted(results, key=lambda x: x[1], reverse=True)
    for res, score in results:
        print(f"* Score={score:4f} \n {res.page_content} [{res.metadata}]\n\n")


if __name__ == "__main__":
    main()