import streamlit as st
import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

from utils.db_config import get_db_info
from utils.config import load_config
from data.dataset import load_documents
from parser.pdf_text_extract import extract_text_with_pymupdf, pdf_text_alignment_v2
from retriever.keyword import BM25Retriever
from retriever.semantic import SemanticRetriever
from retriever.ensemble import EnsembleRetriever, EnsembleMethod

# 환경 변수 로드
load_dotenv("../keys.env")
OPENAI_API_KEY = os.getenv("GRAVY_LAB_OPENAI")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Streamlit 설정
st.set_page_config(page_title="RAG demo", layout="wide")

def main():
    st.title("RAG demo")
    st.sidebar.header("파일 업로드")
    
    # PDF 파일 업로드
    uploaded_file = st.sidebar.file_uploader("PDF 파일을 업로드하세요", type="pdf")
    
    if uploaded_file is not None:
        logger.info("파일 업로드 완료")
        
        cfg = load_config("../configs/config.yaml")
        logger.info("설정 로드 완료")
        
        db_info = get_db_info()
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 문서 로드
        documents = load_documents(cfg, db_info)
        logger.info("문서 로드 완료")
        
        # 검색기 초기화
        semantic_retriever = SemanticRetriever(cfg, documents)
        keyword_retriever = BM25Retriever.from_documents(
            documents=documents,
            bm25_params=cfg['bm25_params'],
            tokenizer_method=cfg['tokenizer'],
            save_path=cfg['save_path'],
            load_path=cfg.get('load_path'),
            k=cfg.get('k', 20)
        )
        logger.info("검색기 초기화 완료")
        
        dense = semantic_retriever.vector_db.as_retriever(search_type="mmr", search_kwargs={"k": cfg['topk']})
        ensemble_retriever = EnsembleRetriever(
            retrievers=[keyword_retriever, dense],
            weights=[0.4, 0.6],
            method=EnsembleMethod.CC
        )
        
        # 텍스트 추출 및 정렬
        with st.spinner("텍스트를 추출하고 정렬 중입니다..."):
            text = extract_text_with_pymupdf("../data/sample.pdf")
            logger.info("텍스트 추출 완료")
            
            aligned_text = pdf_text_alignment_v2(client, text)
            logger.info("텍스트 정렬 완료")
        
        query = aligned_text
        
        st.subheader("추출 및 정렬된 텍스트")
        st.text_area("텍스트 내용", query, height=600)
        
        # 키워드 검색 결과
        with st.spinner("키워드 검색 중입니다..."):
            st.subheader("Keyword 기반 검색")
            keyword_results = keyword_retriever.search_with_score(query, top_k=cfg['topk'])
            logger.info("키워드 검색 완료")
            
            for idx, (content, metadata, score) in enumerate(keyword_results):
                if score >= 0.5:
                    st.text_area(f"Keyword 검색 결과 {idx+1}", f"Score: {score:.2f}\nContent: {content}", height=200)
        
        # 시맨틱 검색 결과
        with st.spinner("시맨틱 검색 중입니다..."):
            st.subheader("Semantic 기반 결과")
            semantic_results = semantic_retriever.similarity_search_with_score(query, k=cfg['topk'])
            semantic_results = sorted(semantic_results, key=lambda x: x[1], reverse=True)
            logger.info("시맨틱 검색 완료")
            
            for idx, (res, score) in enumerate(semantic_results):
                if score >= 0.5:
                    st.text_area(f"Semantic 검색 결과 {idx+1}", f"Score: {score:.2f}\nContent: {res.page_content}", height=200)
        
        # 앙상블 검색 결과
        with st.spinner("앙상블 검색 중입니다..."):
            st.subheader("Hybrid 검색 결과")
            ensemble_results = ensemble_retriever.invoke(query)
            logger.info("앙상블 검색 완료")
            
            for idx, result in enumerate(ensemble_results):
                score = result.metadata.get('score')
                if score is not None and score >= 0.5:
                    st.text_area(f"Hybrid 검색 결과 {idx+1}", f"Score: {score:.2f}\nContent: {result.page_content}", height=200)

if __name__ == "__main__":
    main() 