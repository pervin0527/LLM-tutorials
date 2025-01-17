import os
import json
import logging

## Vector DB
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

## Embedding Model
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

## Document
from uuid import uuid4
from langchain.docstore.document import Document

# HTTPX 로그 비활성화
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self, cfg, dataset):
        self.cfg = cfg
        self.dataset = dataset

        self.embed_model = self.load_embed_model(cfg['embed_model_provider'], cfg['embed_model_name'])
        logger.info(f"{cfg['embed_model_provider']}/{cfg['embed_model_name']} 로드 성공")

        self.documents = self.dataset_to_docs(cfg['page_content_fields'], cfg['metadata_fields'])
        logger.info(f"Documents 로드 성공: {len(self.documents)}")

        self.vector_db = self.create_vector_db(cfg['index_type'])
        logger.info(f"Vector DB 생성 완료")

        if self.cfg['index_load_path'] is not None:
            self.vector_db = self.load_vector_db(self.cfg['index_load_path'], self.embed_model)
        
        else:
            self.vector_db.add_documents(self.documents)
            self.save_vector_db(self.cfg['index_save_path'])
        

    def load_embed_model(self, embed_model_provider, embed_model_name):
        if embed_model_provider == "openai":
            return OpenAIEmbeddings(model=embed_model_name)
        elif embed_model_provider == "huggingface":
            return HuggingFaceEmbeddings(model_name=embed_model_name)
        else:
            raise ValueError(f"Invalid embed model name: {embed_model_name}")
        

    def dataset_to_docs(self, page_fields, metadata_fields):
        documents = []
        for data in self.dataset:
            page_content = ""
            for field in page_fields:
                page_content += f"{field}\n{data[field]}\n\n"

            metadata = {}
            for field in metadata_fields:
                metadata[field] = data[field]
                
            documents.append(Document(page_content=page_content, metadata=metadata, id=uuid4()))

        return documents

    
    def create_vector_db(self, index_type):
        sample_query = "Hello World!!"
        if index_type == "L2": ## L2 Distance(Euclidean Distance)
            index = faiss.IndexFlatL2(len(self.embed_model.embed_query(sample_query)))

        elif index_type == "IP": ## Inner Product
            index = faiss.IndexFlatIP(len(self.embed_model.embed_query(sample_query)))

        elif index_type == "HNSW":## ANN -> Hierarchical Navigable Small World
            index = faiss.IndexHNSWFlat(len(self.embed_model.embed_query(sample_query)))

        vector_db = FAISS(
            embedding_function=self.embed_model,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
    
        return vector_db
    

    def save_vector_db(self, path):
        os.makedirs(path, exist_ok=True)
        self.vector_db.save_local(path)


    def load_vector_db(self, index_path, embed_model):
        vector_db = FAISS.load_local(index_path, embeddings=embed_model)

        return vector_db


    def similarity_search_with_score(self, query, k=5):
        """
        Perform a similarity search and return the top k results with their scores.
        
        :param query: The query string to search for.
        :param k: The number of top results to return.
        :return: A list of tuples containing the document and its similarity score.
        """
        return self.vector_db.similarity_search_with_score(query, k=k)
