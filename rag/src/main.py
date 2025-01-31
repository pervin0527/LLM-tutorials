import os
import json
import logging

from openai import OpenAI
from datetime import datetime

from utils.db_config import get_db_info
from utils.config import load_config, save_config

from data.dataset import load_documents
from parser.pdf_text_extract import extract_text_with_pymupdf, pdf_text_alignment_v2

from retriever.keyword import BM25Retriever
from retriever.semantic import SemanticRetriever
from retriever.ensemble import EnsembleRetriever, EnsembleMethod

from dotenv import load_dotenv
load_dotenv("../keys.env")
OPENAI_API_KEY = os.getenv("GRAVY_LAB_OPENAI")

from logging import getLogger
logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    cfg = load_config("../configs/config.yaml")
    logger.info(f"Config Successfully Loaded")
    db_info = get_db_info()
    client = OpenAI(api_key=OPENAI_API_KEY)

    if cfg.get('load_path') is None:
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        cfg['save_path'] = f"{cfg['save_path']}/{now}"
        os.makedirs(cfg['save_path'], exist_ok=True)
        
        config_file_path = os.path.join(cfg['save_path'], 'config.yaml')
        save_config(cfg, config_file_path)

    documents = load_documents(cfg, db_info)
    semantic_retriever = SemanticRetriever(cfg, documents)
    keyword_retriever = BM25Retriever.from_documents(
        documents=documents,
        bm25_params=cfg['bm25_params'],
        tokenizer_method=cfg['tokenizer'],
        save_path=cfg['save_path'],
        load_path=cfg.get('load_path'),
        k=cfg.get('k', 20)
    )

    dense = semantic_retriever.vector_db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": cfg['topk'], "score_threshold": 0.5})
    ensemble_retriever = EnsembleRetriever(
        retrievers=[keyword_retriever, dense],
        weights=[0.4, 0.6],
        method=EnsembleMethod.CC
    )


    text = extract_text_with_pymupdf("../data/sample.pdf")
    aligned_text = pdf_text_alignment_v2(client, text)
    query = aligned_text

    keyword_results = keyword_retriever.search_with_score(query, top_k=cfg['topk'], score_threshold=0.5)
    keyword_ret_result_path = "../data/keyword_ret_result.json"
    with open(keyword_ret_result_path, 'w', encoding='utf-8') as f:
        json.dump(
            [
                {
                    'score': float(score),
                    'content': content,
                    'metadata': {**metadata, 'score': float(score)}
                }
                for content, metadata, score in keyword_results
            ],
            f, ensure_ascii=False, indent=4
        )
    logger.info(f"Keyword Retriever results saved to {keyword_ret_result_path}")

    semantic_results = semantic_retriever.similarity_search_with_score(query, k=cfg['topk'])
    semantic_results = sorted(semantic_results, key=lambda x: x[1], reverse=True)
    semantic_ret_result_path = "../data/semantic_ret_result.json"
    with open(semantic_ret_result_path, 'w', encoding='utf-8') as f:
        json.dump(
            [
                {
                    'score': float(score),
                    'content': res.page_content,
                    'metadata': {**res.metadata, 'score': float(score)}
                }
                for res, score in semantic_results
            ],
            f, ensure_ascii=False, indent=4
        )
    logger.info(f"Semantic Retriever results saved to {semantic_ret_result_path}")
    
    ensemble_results = ensemble_retriever.invoke(query)
    ensemble_ret_result_path = "../data/ensemble_ret_result.json"
    with open(ensemble_ret_result_path, 'w', encoding='utf-8') as f:
        json.dump(
            [
                {
                    'score': float(result.metadata['score']),
                    'content': result.page_content,
                    'metadata': {**result.metadata, 'score': float(result.metadata['score'])}
                }
                for result in ensemble_results
            ],
            f, ensure_ascii=False, indent=4
        )
    logger.info(f"Ensemble Retriever results saved to {ensemble_ret_result_path}")

if __name__ == "__main__":
    main()