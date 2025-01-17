import os
import logging

from utils.config import load_config
from data.dataset import connect_to_db, get_dataset

from semantic.vector_db import VectorDB

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
    dataset = get_dataset(connection, query)
    logger.info(f"Dataset Successfully Loaded")
    vector_db = VectorDB(cfg, dataset)
    results = vector_db.similarity_search_with_score("프론트엔드 개발자 공고 찾아줘.", k=5)
    
    results = sorted(results, key=lambda x: x[1], reverse=True)
    for res, score in results:
        print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")


if __name__ == "__main__":
    main()