import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from tqdm import tqdm
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity


def create_results_dataframe(vision_results, workstyle_results, summary_results):
    """Create separate dataframes for vision and workstyle results"""
    vision_df = pd.DataFrame(vision_results)
    vision_df['type'] = 'vision'

    workstyle_df = pd.DataFrame(workstyle_results)
    workstyle_df['type'] = 'workstyle'

    summary_df = pd.DataFrame(summary_results)
    summary_df['type'] = 'summary'
    
    # Combine the dataframes
    combined_df = pd.concat([vision_df, workstyle_df, summary_df], ignore_index=True)
    return combined_df


def calculate_embedding_similarity_and_embeddings(responses, client, embed_model):
    embeddings = []
    for response in responses:
        embedding_response = client.embeddings.create(
            input=response,
            model=embed_model
        )
        embeddings.append(embedding_response.data[0].embedding)

    embeddings = np.array(embeddings)
    similarity_matrix = cosine_similarity(embeddings)
    mean_similarity = similarity_matrix.mean()
    
    return mean_similarity, embeddings


def calculate_n_gram_similarity(responses, num_gram):
    def n_grams(text, n):
        words = text.split()
        return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]

    def n_gram_overlap(response1, response2, n):
        ngrams1 = set(n_grams(response1, n))
        ngrams2 = set(n_grams(response2, n))
        return len(ngrams1 & ngrams2) / len(ngrams1 | ngrams2) if ngrams1 | ngrams2 else 0

    n_gram_similarities = []
    for n in range(1, num_gram + 1):
        similarities = [
            n_gram_overlap(responses[i], responses[j], n)
            for i in range(len(responses)) for j in range(i + 1, len(responses))
        ]
        n_gram_similarities.append(sum(similarities) / len(similarities))

    return n_gram_similarities


def analyze_responses(df, client, ng_gram, embed_model):
    results = {}

    for response_type in ['vision', 'workstyle', 'summary']:
        type_responses = df[df['type'] == response_type]['response'].tolist()

        mean_similarity, embeddings = calculate_embedding_similarity_and_embeddings(type_responses, client, embed_model)
        n_gram_similarities = calculate_n_gram_similarity(type_responses, ng_gram)

        results[response_type] = {
            'semantic_similarity': mean_similarity,
            'n_gram_similarities': n_gram_similarities,
            'embeddings': embeddings
        }

    return results

def plot_ngram_similarities(analysis_results, save_path=None):
    """
    n-gram 유사도 결과를 선 그래프로 시각화
    """
    plt.figure(figsize=(12, 6))
    
    for response_type, metrics in analysis_results.items():
        n_gram_similarities = metrics['n_gram_similarities']
        n_values = range(1, len(n_gram_similarities) + 1)
        
        plt.plot(n_values, n_gram_similarities, marker='o', label=response_type)
    
    plt.xlabel('n-gram Size')
    plt.ylabel('Similarity Score')
    plt.title('N-gram Similarities Across Response Types')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    if save_path:
        plt.savefig(save_path)
    plt.show()


def plot_embeddings_tsne(df, client, save_path=None):
    """
    각 type별 응답들의 임베딩을 t-SNE로 2D 시각화
    """
    # 임베딩 생성
    def get_embedding(text, model="text-embedding-ada-002"):
        try:
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None

    # 각 type별로 임베딩 생성
    embeddings = []
    labels = []
    
    for idx, row in df.iterrows():
        embedding = get_embedding(row['response'])
        if embedding is not None:
            embeddings.append(embedding)
            labels.append(row['type'])
    
    if not embeddings:
        print("No valid embeddings generated")
        return
    
    # list를 numpy 배열로 변환
    embeddings_array = np.array(embeddings)
    
    # t-SNE 차원 축소 (2차원으로 변경)
    n_samples = len(embeddings_array)
    perplexity = min(30, n_samples - 1)  # perplexity는 n_samples보다 작아야 함
    
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)  # n_components를 2로 변경
    embeddings_2d = tsne.fit_transform(embeddings_array)  # 변수명 변경
    
    # 2D 시각화
    plt.figure(figsize=(10, 8))  # 크기 조정
    
    # 각 type별로 다른 색상 적용
    colors = {'vision': 'red', 'workstyle': 'blue', 'summary': 'green'}
    markers = {'vision': 'o', 'workstyle': '^', 'summary': 's'}
    
    for response_type in colors.keys():
        mask = np.array([label == response_type for label in labels])
        if np.any(mask):
            plt.scatter(
                embeddings_2d[mask, 0],  # 2D 데이터 사용
                embeddings_2d[mask, 1],
                c=colors[response_type],
                marker=markers[response_type],
                label=response_type,
                alpha=0.6,
                s=100  # 마커 크기
            )
    
    plt.xlabel('t-SNE 1')
    plt.ylabel('t-SNE 2')
    plt.title('2D t-SNE Visualization of Response Embeddings by Type')
    
    # 범례 위치 조정
    plt.legend(bbox_to_anchor=(1.15, 1), loc='upper right')
    
    # 그래프 여백 조정
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        plt.close()
        print(f"t-SNE plot saved to {save_path}")


def visualize_results(analysis_results, df, client, output_dir, prefix):
    """
    분석 결과를 시각화하고 저장
    """
    # 임베딩 t-SNE 시각화
    tsne_plot_path = os.path.join(output_dir, f'{prefix}_embedding_tsne.png')
    plot_embeddings_tsne(df, client, tsne_plot_path)

    # n-gram 유사도 그래프
    ngram_plot_path = os.path.join(output_dir, f'{prefix}_ngram_similarities.png')
    plot_ngram_similarities(analysis_results, ngram_plot_path)


def analyze_unique_responses(df):
    """
    각 type별로 고유한 response 값을 분석하고 출력
    
    Args:
        df (pd.DataFrame): 분석할 DataFrame (type과 response 컬럼 포함)
    """
    print("\n=== Unique Responses Analysis ===")
    
    # 각 type별로 처리
    for response_type in df['type'].unique():
        # type별 응답 추출
        type_responses = df[df['type'] == response_type]['response'].unique()
        
        print(f"\n[{response_type.upper()}] - {len(type_responses)} unique responses")
        print("-" * 50)
        
        # 각 고유 응답 출력
        for i, response in enumerate(type_responses, 1):
            print(f"{i}. {response}\n")