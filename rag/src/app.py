import streamlit as st

import os
import json
import logging
import tempfile
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
        logger.info(f"파일 업로드 완료: {uploaded_file.name}")

        # 임시 디렉토리에 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_pdf_path = temp_file.name
        
        logger.info(f"임시 파일 저장 완료: {temp_pdf_path}")

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)  # :white_check_mark: OpenAI Client 객체 초기화

            # 텍스트 추출 및 정렬
            with st.spinner("텍스트를 추출하고 정렬 중입니다..."):
                text = extract_text_with_pymupdf(temp_pdf_path)  # :white_check_mark: 임시 파일 경로 사용
                logger.info("텍스트 추출 완료")

                aligned_text = pdf_text_alignment_v2(client, text)  # :white_check_mark: client를 초기화한 후 전달
                logger.info("텍스트 정렬 완료")

            query = aligned_text
            
            st.subheader("추출 및 정렬된 텍스트")
            st.text_area("텍스트 내용", query, height=600)

            cfg = load_config("../configs/config.yaml")
            logger.info("설정 로드 완료")

            db_info = get_db_info()

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

            # 키워드 검색 결과
            with st.spinner("Keyword 검색 중..."):
                st.subheader("Keyword 검색 결과")
                keyword_results = keyword_retriever.search_with_score(query, top_k=cfg['topk'])
                logger.info("keyword 검색 완료")

                for idx, (content, metadata, score) in enumerate(keyword_results):
                    if score >= 0.5:
                        st.text_area(f"Keyword 검색 결과 {idx+1}", f"Score: {score:.2f}\nContent: {content}", height=200)

            # 시맨틱 검색 결과
            with st.spinner("Semantic 검색 중..."):
                st.subheader("Semantic 검색 결과")
                semantic_results = semantic_retriever.similarity_search_with_score(query, k=cfg['topk'])
                semantic_results = sorted(semantic_results, key=lambda x: x[1], reverse=True)
                logger.info("semantic 검색 완료")

                for idx, (res, score) in enumerate(semantic_results):
                    if score >= 0.5:
                        st.text_area(f"Semantic 검색 결과 {idx+1}", f"Score: {score:.2f}\nContent: {res.page_content}", height=200)

            # 앙상블 검색 결과
            with st.spinner("Hybrid 검색 중..."):
                st.subheader("Hybrid 검색 결과")
                ensemble_results = ensemble_retriever.invoke(query)
                logger.info("hybrid 검색 완료")

                for idx, result in enumerate(ensemble_results):
                    score = result.metadata.get('score')
                    if score is not None and score >= 0.5:
                        st.text_area(f"Hybrid 검색 결과 {idx+1}", f"Score: {score:.2f}\nContent: {result.page_content}", height=200)

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            st.error(f"오류가 발생했습니다: {e}")

        finally:
            # :white_check_mark: 사용이 끝난 임시 파일 삭제 (파일이 존재하는 경우만)
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                logger.info(f"임시 파일 삭제 완료: {temp_pdf_path}")

if __name__ == "__main__":
    main()