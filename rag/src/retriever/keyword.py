from __future__ import annotations

import time
import logging
logger = logging.getLogger(__name__)

import numpy as np

from pydantic import Field
from operator import itemgetter
from typing import Any, Callable, Dict, Iterable, List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from kiwipiepy import Kiwi
from konlpy.tag import Okt, Mecab, Kkma


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
    """`BM25` retriever with support for multiple Korean tokenizers."""

    vectorizer: Any
    """ BM25 vectorizer."""
    docs: List[Document] = Field(repr=False)
    """ List of documents."""
    k: int = 4
    """ Number of documents to return."""
    preprocess_func: Callable[[str], List[str]]
    """ Preprocessing function to use on the text before BM25 vectorization."""

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @classmethod
    def from_texts(
        cls,
        texts: Iterable[str],
        metadatas: Optional[Iterable[dict]] = None,
        bm25_params: Optional[Dict[str, Any]] = None,
        tokenizer_method: str = "kiwi",
        **kwargs: Any,
    ) -> BM25Retriever:
        """
        Create a KiwiBM25Retriever from a list of texts.
        Args:
            texts: A list of texts to vectorize.
            metadatas: A list of metadata dicts to associate with each text.
            bm25_params: Parameters to pass to the BM25 vectorizer.
            tokenizer_method: The tokenizer method to use (kiwi, okt, mecab, kkma).
            **kwargs: Any other arguments to pass to the retriever.

        Returns:
            A KiwiBM25Retriever instance.
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(
                "Could not import rank_bm25, please install with `pip install rank_bm25`."
            )

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
        
        return cls(vectorizer=vectorizer, docs=docs, preprocess_func=tokenizer.tokenize, **kwargs)

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[Document],
        *,
        bm25_params: Optional[Dict[str, Any]] = None,
        tokenizer_method: str = "kiwi",
        **kwargs: Any,
    ) -> BM25Retriever:
        """
        Create a KiwiBM25Retriever from a list of Documents.
        Args:
            documents: A list of Documents to vectorize.
            bm25_params: Parameters to pass to the BM25 vectorizer.
            tokenizer_method: The tokenizer method to use (kiwi, okt, mecab, kkma).
            **kwargs: Any other arguments to pass to the retriever.

        Returns:
            A KiwiBM25Retriever instance.
        """
        texts, metadatas = zip(*((d.page_content, d.metadata) for d in documents))
        return cls.from_texts(
            texts=texts,
            bm25_params=bm25_params,
            metadatas=metadatas,
            tokenizer_method=tokenizer_method,
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

