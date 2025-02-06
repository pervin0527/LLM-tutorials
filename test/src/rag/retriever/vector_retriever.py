import os
import faiss
import logging

from datetime import datetime
from fastapi import APIRouter, Request

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from src.utils.config_utils import save_config
from src.rag.data.dataset import load_documents_from_db


logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, cfg):
        """
        FAISS 벡터 스토어 초기화 및 로드
        """
        self.cfg = cfg
        if self.cfg['provider'] == "openai":
            self.embed_model = OpenAIEmbeddings(model=self.cfg['model_name'], api_key=self.cfg['openai_api_key'])

        elif self.cfg['provider'] == "huggingface":
            self.embed_model = HuggingFaceEmbeddings(model_name=self.cfg['model_name'], model_kwargs=self.cfg['model_kwargs'], encode_kwargs=self.cfg['encode_kwargs'])

    
    def create_vector_db(self, index_type):
        logger.info(f"🚀 벡터 DB 초기화 중... (타입: {index_type})")
        sample_query = "기업의 비전에 대해 알려주세요."

        if index_type == "L2": ## L2 Distance(Euclidean Distance)
            index = faiss.IndexFlatL2(len(self.embed_model.embed_query(sample_query)))

        elif index_type == "IP": ## Inner Product
            index = faiss.IndexFlatIP(len(self.embed_model.embed_query(sample_query)))

        elif index_type == "HNSW":## ANN -> Hierarchical Navigable Small World
            index = faiss.IndexHNSWFlat(len(self.embed_model.embed_query(sample_query)))

        else:
            raise ValueError("❌ 지원하지 않는 index_type")

        vector_db = FAISS(
            embedding_function=self.embed_model,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        logger.info("✅ 벡터 DB 초기화 완료")

        documents = load_documents_from_db()
        logger.info(f"🚀 문서 로드 완료 : {len(documents)}")
        
        vector_db.add_documents(documents)
        logger.info("✅ 문서 추가 완료")

        return vector_db
    
    def save_vector_db(self, vector_db):
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        save_path = f"../{self.cfg['index_save_path']}/{now}"
        
        os.makedirs(save_path, exist_ok=True)

        vector_db.save_local(save_path)
        save_config(self.cfg, f"{save_path}/config.yaml")

        logger.info(f"벡터 데이터베이스 생성 완료. 저장 경로: {save_path}")


    def load_vector_db(self, index_file_path, embed_model):
        vector_db = FAISS.load_local(index_file_path, embeddings=embed_model, allow_dangerous_deserialization=True)

        return vector_db