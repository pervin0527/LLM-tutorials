import streamlit as st
import os
from utils.config import load_config
from data.dataset import connect_to_db, get_dataset, get_documents
from retriever.keyword import BM25Retriever
from retriever.semantic import SemanticRetriever

from dotenv import load_dotenv
load_dotenv("../keys.env")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

def main():
    # Load configuration and initialize database connection
    cfg = load_config("../configs/config.yaml")
    connection = connect_to_db(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)

    # Fetch dataset and prepare documents
    query = """
        SELECT * 
        FROM recruit
        WHERE platform_type IN ('WANTED');
    """
    dataset = get_dataset(connection, query)
    documents = get_documents(dataset, cfg['page_content_fields'], cfg['metadata_fields'])

    # Initialize retrievers
    keyword_retriever = BM25Retriever.from_documents(
        documents=documents,
        bm25_params=cfg['bm25_params'],
        tokenizer_method=cfg['tokenizer']
    )
    semantic_retriever = SemanticRetriever(cfg, dataset)

    # Streamlit UI
    st.title("Document Search App")

    # Sidebar configuration
    with st.sidebar:
        st.header("Search Configuration")
        search_type = st.radio("Choose retrieval method", ["Keyword", "Embedding"], index=0)
        top_k = st.slider("Select Top-K results", 1, 10, 5)

    # Search interface
    search_query_container = st.container()
    with search_query_container:
        st.header("Search")
        query = st.text_input("Enter your query:", placeholder="Type your query here...")
        search_button = st.button("Search")

    # Results display
    if search_button and query:
        if search_type == "Keyword":
            results = keyword_retriever.search_with_score(query, top_k=top_k)
        else:
            results = semantic_retriever.similarity_search_with_score(query, k=top_k)
            results = sorted(results, key=lambda x: x[1], reverse=True)

        if results:
            current_result_index = st.session_state.get("current_result_index", 0)

            # Navigation buttons
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                if col1.button("⬅️ Previous"):
                    current_result_index = max(0, current_result_index - 1)
                    st.session_state["current_result_index"] = current_result_index

                col3.button("Next ➡️", key="next_button", on_click=lambda: st.session_state.update({"current_result_index": min(len(results) - 1, current_result_index + 1)}))

            # Display current result
            doc, score = results[current_result_index]
            with st.container():
                st.subheader(f"Result {current_result_index + 1} of {len(results)}")
                st.write(f"**Similarity Score:** {score:.4f}")
                st.write(f"**Content:** {doc.page_content}")
                st.write(f"**Metadata:** {doc.metadata}")

if __name__ == "__main__":
    main()
