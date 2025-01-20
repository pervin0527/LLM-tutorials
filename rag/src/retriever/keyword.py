from __future__ import annotations

import os
import time
import pickle
import logging
import numpy as np

from pathlib import Path
from pydantic import Field
from rank_bm25 import BM25Okapi
from typing import Any, Callable, Dict, Iterable, List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from kiwipiepy import Kiwi
from konlpy.tag import Okt, Mecab, Kkma

from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


def parallel_tokenize(texts: List[str], tokenizer: KoreanTokenizer, max_workers: int = 4) -> List[List[str]]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(tokenizer.tokenize, texts))


class KoreanTokenizer:
    def __init__(self, method: str = "kiwi"):
        if method == "kiwi":
            self.tokenizer = Kiwi()
            self.tokenize = self.kiwi_tokenize
        elif method == "okt":
            self.tokenizer = Okt()
            self.tokenize = self.okt_tokenize
        elif method == "mecab":
            self.tokenizer = Mecab()
            self.tokenize = self.mecab_tokenize
        elif method == "kkma":
            self.tokenizer = Kkma()
            self.tokenize = self.kkma_tokenize
        else:
            raise ValueError(f"Unsupported tokenizer method: {method}")

    def kiwi_tokenize(self, text: str) -> List[str]:
        return [token.form for token in self.tokenizer.tokenize(text)]

    def okt_tokenize(self, text: str) -> List[str]:
        return self.tokenizer.morphs(text)

    def mecab_tokenize(self, text: str) -> List[str]:
        return self.tokenizer.morphs(text)

    def kkma_tokenize(self, text: str) -> List[str]:
        return self.tokenizer.morphs(text)


class BM25Retriever(BaseRetriever):
    vectorizer: Any
    docs: List[Document] = Field(repr=False)
    k: int = 4
    preprocess_func: Callable[[str], List[str]]

    @classmethod
    def from_texts(
        cls,
        texts: Iterable[str],
        metadatas: Optional[Iterable[dict]] = None,
        bm25_params: Optional[Dict[str, Any]] = None,
        tokenizer_method: str = "kiwi",
        save_path: Optional[str] = None,
        load_path: Optional[str] = None,
        **kwargs: Any,
    ) -> BM25Retriever:
        """
        텍스트로부터 BM25Retriever를 생성합니다.
        
        Args:
            texts: 텍스트 목록
            metadatas: 메타데이터 목록 (옵션)
            bm25_params: BM25 파라미터 (옵션)
            tokenizer_method: 토크나이저 방식 (기본값: "kiwi")
            save_path: 저장할 파일 경로 (옵션)
            load_path: 로드할 파일 경로 (옵션)
            **kwargs: 추가 파라미터
        """
        # load_path가 제공되면 저장된 모델을 로드
        if load_path:
            load_path = f"{load_path}/{tokenizer_method}.pkl"
            logger.info(f"Loading BM25Retriever from {load_path}")
            return cls.load(load_path)

        # 새로운 모델 생성
        tokenizer = KoreanTokenizer(method=tokenizer_method)
        logger.info(f"tokenizer: {tokenizer_method}")
        
        start_time = time.time()
        texts_processed = [tokenizer.tokenize(t) for t in texts]
        elapsed_time = time.time() - start_time
        logger.info(f"Tokenizing completed in {elapsed_time:.2f} seconds")

        bm25_params = bm25_params or {}
        vectorizer = BM25Okapi(texts_processed, **bm25_params)
        metadatas = metadatas or ({} for _ in texts)
        docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
        
        instance = cls(
            vectorizer=vectorizer,
            docs=docs,
            k=kwargs.get('k', 4),
            preprocess_func=tokenizer.tokenize
        )

        # save_path가 제공되면 모델 저장
        if save_path:
            save_path = f"{save_path}/{tokenizer_method}.pkl"
            instance.save(save_path)
            logger.info(f"Saved BM25Retriever to {save_path}")

        return instance

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[Document],
        *,
        bm25_params: Optional[Dict[str, Any]] = None,
        tokenizer_method: str = "kiwi",
        save_path: Optional[str] = None,
        load_path: Optional[str] = None,
        **kwargs: Any,
    ) -> BM25Retriever:
        """
        문서로부터 BM25Retriever를 생성합니다.
        
        Args:
            documents: Document 객체 목록
            bm25_params: BM25 파라미터 (옵션)
            tokenizer_method: 토크나이저 방식 (기본값: "kiwi")
            save_path: 저장할 파일 경로 (옵션)
            load_path: 로드할 파일 경로 (옵션)
            **kwargs: 추가 파라미터
        """
        texts, metadatas = zip(*((d.page_content, d.metadata) for d in documents))
        return cls.from_texts(
            texts=texts,
            bm25_params=bm25_params,
            metadatas=metadatas,
            tokenizer_method=tokenizer_method,
            save_path=save_path,
            load_path=load_path,
            **kwargs,
        )

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        processed_query = self.preprocess_func(query)
        return_docs = self.vectorizer.get_top_n(processed_query, self.docs, n=self.k)
        return return_docs

    @staticmethod
    def softmax(x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

    @staticmethod
    def argsort(seq, reverse):
        # http://stackoverflow.com/questions/3071415/efficient-method-to-calculate-the-rank-vector-of-a-list-in-python
        return sorted(range(len(seq)), key=seq.__getitem__, reverse=reverse)

    def search_with_score(self, query: str, top_k=None):
        normalized_score = BM25Retriever.softmax(self.vectorizer.get_scores(self.preprocess_func(query)))

        if top_k is None:
            top_k = self.k

        score_indexes = BM25Retriever.argsort(normalized_score, True)

        docs_with_scores = []
        for i in score_indexes[:top_k]:
            doc = self.docs[i]
            score = normalized_score[i]
            docs_with_scores.append((doc, score))

        return docs_with_scores
    
    def save(self, file_path: str) -> None:
        # tokenizer 메서드 이름 추출
        tokenizer_method = None
        if hasattr(self.preprocess_func, '__self__'):
            tokenizer_instance = self.preprocess_func.__self__
            if isinstance(tokenizer_instance, KoreanTokenizer):
                for method, func in [
                    ('kiwi', tokenizer_instance.kiwi_tokenize),
                    ('okt', tokenizer_instance.okt_tokenize),
                    ('mecab', tokenizer_instance.mecab_tokenize),
                    ('kkma', tokenizer_instance.kkma_tokenize)
                ]:
                    if self.preprocess_func == func.__get__(tokenizer_instance):
                        tokenizer_method = method
                        break
        
        if tokenizer_method is None:
            raise ValueError("Could not determine tokenizer method")

        save_dict = {
            'vectorizer': self.vectorizer,
            'docs': self.docs,
            'k': self.k,
            'tokenizer_method': tokenizer_method  # tokenizer 대신 메서드 이름만 저장
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(save_dict, f)
        
        logger.info(f"BM25Retriever saved to {file_path}")

    @classmethod
    def load(cls, file_path: str) -> 'BM25Retriever':
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            save_dict = pickle.load(f)
        
        # 토크나이저 재생성
        tokenizer = KoreanTokenizer(method=save_dict['tokenizer_method'])
        
        instance = cls(
            vectorizer=save_dict['vectorizer'],
            docs=save_dict['docs'],
            k=save_dict['k'],
            preprocess_func=tokenizer.tokenize
        )
        
        logger.info(f"BM25Retriever loaded from {file_path}")
        return instance