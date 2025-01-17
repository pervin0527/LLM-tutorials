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

    connection = connect_to_db(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    logger.info(f"DB 연결 성공")

    query = """
        SELECT * 
        FROM recruit
        WHERE platform_type IN ('WANTED');
    """
    dataset = get_dataset(connection, query)
    logger.info(f"데이터셋 로드 성공: {len(dataset)}")

    vector_db = VectorDB(cfg, dataset)
    vector_db.similarity_search_with_score("프론트엔드 개발자 공고 찾아줘.", k=5)


if __name__ == "__main__":
    main()