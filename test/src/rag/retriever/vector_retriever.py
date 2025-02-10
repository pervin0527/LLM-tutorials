import os
import faiss
import numpy as np

from datetime import datetime
from fastapi import APIRouter, Request

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.docstore.document import Document

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from app.utils.logging import logger
from src.utils.config_utils import save_config
from src.rag.data.dataset import load_documents_from_db

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

        self.vector_db = None

    
    def create_vector_db(self, index_type):
        logger.info(f"🚀 벡터 DB 초기화 중")
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
        logger.info(f"문서 로드 완료 : {len(documents)}")
        
        vector_db.add_documents(documents)
        logger.info("✅ 문서 추가 완료")

        self.vector_db = vector_db

        return vector_db
    

    def save_vector_db(self, vector_db):
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        save_path = f"{self.cfg['index_save_path']}/{now}"
        
        os.makedirs(save_path, exist_ok=True)

        vector_db.save_local(save_path)
        save_config(self.cfg, f"{save_path}/config.yaml")

        logger.info(f"✅ 벡터 데이터베이스 생성 완료. 저장 경로: {save_path}")


    def load_vector_db(self, index_file_path, embed_model):
        logger.info(f"벡터 데이터베이스 로드 중... (경로: {index_file_path})")
        vector_db = FAISS.load_local(index_file_path, embeddings=embed_model, allow_dangerous_deserialization=True)
        logger.info("✅ 벡터 데이터베이스 로드 완료")

        self.vector_db = vector_db
        return vector_db
       

    def search_company(self, company_name):
        """
        주어진 회사명이 벡터 데이터베이스에 존재하는지 확인하고, 몇 개의 문서가 있는지 반환합니다.
        """
        logger.info(f"🔍 '{company_name}' 회사의 문서 검색 중...")
        count = 0

        # 벡터 데이터베이스에서 모든 문서를 검색
        for doc_id, document in self.vector_db.docstore._dict.items():
            if isinstance(document, Document) and document.metadata.get("company_name") == company_name:
                count += 1

        logger.info(f"🔍 '{company_name}' 회사의 문서 개수: {count}")
        return count


    def delete_company(self, company_name):
        """
        주어진 회사명에 해당하는 모든 문서를 벡터 데이터베이스에서 삭제하고, 삭제 여부를 반환합니다.
        """
        logger.info(f"🗑️ '{company_name}' 회사의 문서 삭제 중...")
        to_delete = []

        # 삭제할 문서 수집
        for doc_id, document in self.vector_db.docstore._dict.items():
            if isinstance(document, Document) and document.metadata.get("company_name") == company_name:
                to_delete.append(doc_id)

        # 문서 삭제
        for doc_id in to_delete:
            del self.vector_db.docstore._dict[doc_id]

        logger.info(f"✅ '{company_name}' 회사의 문서 {len(to_delete)}개 삭제 완료")
        return len(to_delete) > 0


    def get_company_documents(self, company_name):
        """
        주어진 회사명을 가진 모든 문서를 벡터 데이터베이스에서 검색하여 반환합니다.
        """
        logger.info(f"🔍 Vector DB에서 '{company_name}' 회사의 문서 검색 중...")
        results = []

        # 벡터 데이터베이스에서 모든 문서를 검색
        for doc_id, document in self.vector_db.docstore._dict.items():
            if isinstance(document, Document) and document.metadata.get("company_name") == company_name:
                results.append({
                    "url": document.metadata.get("url"),
                    "text": document.page_content
                })

        logger.info(f"🔍 검색 완료: {len(results)}개의 문서 발견")
        return results
    

    def search_document(self, company_name, url):
        """
        주어진 회사명과 URL에 해당하는 문서를 검색하여 반환합니다.
        """
        logger.info(f"🔍 '{company_name}' 회사의 URL '{url}'에 해당하는 문서 검색 중...")
        
        # 회사명으로 문서 검색
        documents = self.get_company_documents(company_name)
        
        # URL에 해당하는 문서 찾기
        for document in documents:
            if document['url'] == url:
                logger.info(f"✅ 문서 발견: {document}")
                return document
        
        logger.warning(f"'{company_name}' 회사의 URL '{url}'에 해당하는 문서를 찾을 수 없습니다.")
        return None


    def update_document(self, company_name, url, new_text=None, new_url=None):
        """
        주어진 회사명과 URL에 해당하는 문서를 업데이트합니다.
        """
        logger.info(f"🔄 '{company_name}' 회사의 문서 업데이트 중... (URL: {url})")
        
        # 기존 문서의 docstore ID 찾기
        doc_id = None
        for id_, doc in self.vector_db.docstore._dict.items():
            if (isinstance(doc, Document) and 
                doc.metadata.get("company_name") == company_name and 
                doc.metadata.get("url") == url):
                doc_id = id_
                break
        
        if doc_id is None:
            logger.warning(f"'{company_name}' 회사의 URL '{url}'에 해당하는 문서를 찾을 수 없습니다.")
            return None

        # 1. Docstore에서 문서 삭제
        original_doc = self.vector_db.docstore._dict.pop(doc_id)
        
        # 2. FAISS 인덱스에서 벡터 삭제
        # docstore ID를 FAISS 인덱스 ID로 변환
        index_id = list(self.vector_db.index_to_docstore_id.keys())[
            list(self.vector_db.index_to_docstore_id.values()).index(doc_id)
        ]
        self.vector_db.index_to_docstore_id.pop(index_id)
        self.vector_db.index.remove_ids(np.array([index_id]))

        # 3. 새로운 문서 생성
        updated_text = new_text if new_text else original_doc.page_content
        updated_url = new_url if new_url else url
        
        updated_document = Document(
            page_content=updated_text,
            metadata={"company_name": company_name, "url": updated_url}
        )

        # 4. 새로운 문서 추가
        self.vector_db.add_documents([updated_document])
        
        logger.info("✅ 문서 업데이트 완료")
        return updated_document


    def delete_document(self, company_name, url):
        """
        주어진 회사명과 URL에 해당하는 문서를 벡터 데이터베이스에서 삭제합니다.
        """
        logger.info(f"🗑️ '{company_name}' 회사의 URL '{url}'에 해당하는 문서 삭제 중...")
        
        # docstore에서 문서 ID 찾기
        doc_id = None
        for id_, doc in self.vector_db.docstore._dict.items():
            if (isinstance(doc, Document) and 
                doc.metadata.get("company_name") == company_name and 
                doc.metadata.get("url") == url):
                doc_id = id_
                break
        
        if doc_id is None:
            logger.warning(f"'{company_name}' 회사의 URL '{url}'에 해당하는 문서를 찾을 수 없습니다.")
            return False

        try:
            # 1. Docstore에서 문서 삭제
            self.vector_db.docstore._dict.pop(doc_id)
            
            # 2. FAISS 인덱스에서 벡터 삭제
            # docstore ID를 FAISS 인덱스 ID로 변환
            index_id = list(self.vector_db.index_to_docstore_id.keys())[
                list(self.vector_db.index_to_docstore_id.values()).index(doc_id)
            ]
            self.vector_db.index_to_docstore_id.pop(index_id)
            self.vector_db.index.remove_ids(np.array([index_id]))
            
            logger.info(f"✅ 문서 삭제 완료 (doc_id: {doc_id}, index_id: {index_id})")
            return True
            
        except Exception as e:
            logger.error(f"문서 삭제 중 오류 발생: {str(e)}")
            return False
    

    def similarity_search_with_score(self, query):
        k = int(self.cfg.get('top_k', 10))
        fetch_k = k * 2

        results = self.vector_db.similarity_search_with_score(query, k=k)

        # numpy.float32 → float 변환 및 score로 내림차순 정렬
        results = sorted([(doc, float(score)) for doc, score in results], key=lambda x: x[1], reverse=True)

        return results
        
    def similarity_search_with_relevance_scores(self, query):
        k = int(self.cfg.get('top_k', 10))
        fetch_k = k * 2

        results = self.vector_db.similarity_search_with_relevance_scores(query, k=k)

        # numpy.float32 → float 변환 및 score로 내림차순 정렬
        results = sorted([(doc, float(score)) for doc, score in results], key=lambda x: x[1], reverse=True)

        return results
