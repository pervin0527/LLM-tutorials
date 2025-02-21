import asyncio
import numpy as np
from typing import List
from kiwipiepy import Kiwi
from datetime import datetime
from langchain.docstore.document import Document
from sklearn.feature_extraction.text import TfidfVectorizer

from app.utils.logging import logger
from src.llm.utils import process_string_to_json
from src.llm.commercial_models import chatgpt_response

from src.culture.vision.prompts import (
    VISION_TITLES, 
    VISION_CONTEXTS, 
    VISION_INITIAL_MESSAGES, 
    get_vision_messages
)

def extract_keywords(text: str, num_keywords: int = 20) -> str:
    # Kiwi 초기화
    kiwi = Kiwi()
    
    # 명사 추출 (Kiwi는 형태소 분석 결과에서 명사만 필터링 필요)
    analyzed = kiwi.analyze(text)
    nouns = []
    for token_list in analyzed:
        for token in token_list[0]:
            if token[1].startswith('N'):  # 명사 태그로 시작하는 형태소 선택
                nouns.append(token[0])
    
    noun_text = ' '.join(nouns)
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=num_keywords)
    tfidf_matrix = vectorizer.fit_transform([noun_text])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray().flatten()
    
    top_indices = np.argsort(tfidf_scores)[::-1][:num_keywords]
    top_keywords = [feature_names[i] for i in top_indices]
    
    return ','.join(top_keywords)

def extract_keywords_textrank(
    text: str,
    num_keywords: int = 20,
    window_size: int = 4,
    damping: float = 0.85,
    max_iter: int = 50,
    tol: float = 1e-4
) -> str:
    """
    TextRank 알고리즘을 활용하여 키워드를 추출하는 함수.
    """
    kiwi = Kiwi()
    analyzed = kiwi.analyze(text)
    words = []
    for token_list in analyzed:
        for token in token_list[0]:
            if token[1].startswith('N'):
                words.append(token[0])
                
    if not words:
        return ""
    
    unique_words = list(set(words))
    index_dict = {word: idx for idx, word in enumerate(unique_words)}
    n = len(unique_words)
    
    graph = np.zeros((n, n))
    for i, word in enumerate(words):
        window_end = min(i + window_size, len(words))
        for j in range(i + 1, window_end):
            word2 = words[j]
            idx1 = index_dict[word]
            idx2 = index_dict[word2]
            if idx1 == idx2:
                continue
            graph[idx1][idx2] += 1.0
            graph[idx2][idx1] += 1.0

    scores = np.ones(n)
    for iteration in range(max_iter):
        prev_scores = np.copy(scores)
        for i in range(n):
            summation = 0.0
            for j in range(n):
                if graph[j][i] != 0:
                    summation += (graph[j][i] / np.sum(graph[j])) * scores[j]
            scores[i] = (1 - damping) + damping * summation
        
        if np.abs(scores - prev_scores).sum() < tol:
            break
    
    word_scores = {word: scores[index_dict[word]] for word in unique_words}
    sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [word for word, score in sorted_words[:num_keywords]]
    
    return ','.join(top_keywords)


async def company_vision_analysis(documents: List[Document]):
    """회사의 비전을 분석하여 키워드를 추출하고 16개 항목에 대해 병렬 평가하는 함수"""
    try:
        request = {}
        formatted_results = []  # formatted_results 초기화

        ## 문서들을 리스트로 변환 --> db 저장용
        document_list = []
        for doc in documents:
            if isinstance(doc, Document):
                document_list.append(doc.page_content)
            else:
                document_list.append(doc)
        request["page_content"] = document_list
        
        ## 키워드 추출
        combined_data = ' '.join(document_list)
        keywords = extract_keywords_textrank(combined_data, num_keywords=20)
        request["keywords"] = keywords
        logger.info(f"[vision_analysis] keywords: {keywords}")
        keyword_str = ", ".join(keywords.split(','))  # 쉼표로 분리된 문자열을 리스트로 변환 후 다시 문자열화

        ## 각 비전 항목에 대해 병렬로 API 호출
        prompts = [VISION_INITIAL_MESSAGES]
        response_list = []
        for i, (ko_title, en_title) in enumerate(VISION_TITLES.items()):
            contexts = VISION_CONTEXTS.get(ko_title, "")
            messages = VISION_INITIAL_MESSAGES + get_vision_messages(i+1, en_title, contexts, combined_data, keyword_str)
            prompts.append(get_vision_messages(i+1, f"{ko_title}({en_title})", contexts, combined_data, keyword_str))
            response_list.append(chatgpt_response(prompt=messages))

        ## 동시에 모든 요청을 실행
        all_responses = await asyncio.gather(*response_list)

        ## 응답 후처리도 병렬 처리
        process_tasks = [process_string_to_json(response) for response in all_responses]
        results = await asyncio.gather(*process_tasks)
        
        # 응답을 [{'en_title' : "ko_title", "score" : float, "summary" : str}] 형식으로 변환
        for i, result in enumerate(results):
            ko_title, en_title = list(VISION_TITLES.items())[i]
            for keyword, data in result.items():
                formatted_results.append({
                    "code" : en_title,
                    "score": data['score'],
                    "summary": data['summary']
                })
        
        request["prompts"] = prompts
        return {"request": request, "response": formatted_results}

    except Exception as e:
        logger.error(f"키워드 추출 중 오류 발생: {str(e)}")
        return {"error": str(e)}