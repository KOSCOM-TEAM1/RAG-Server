import json
from typing import Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

def create_hybrid_retriever(file_path: str) -> Optional[EnsembleRetriever]:
    """
    Loads news data from a JSON file, creates embeddings, and builds a hybrid retriever
    combining semantic search (FAISS) and keyword search (BM25).

    Args:
        file_path (str): The path to the JSON file. 
                         It is assumed that the JSON file contains a list of dictionaries, 
                         and each dictionary has a 'DETAIL' key with the text content.

    Returns:
        Optional[EnsembleRetriever]: The created hybrid retriever, or None if no documents
                                     could be loaded.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: JSON file not found at {file_path}. No retriever will be created.")
        return None

    # The content is in the 'DETAIL' field of each JSON object
    documents = [Document(page_content=item.get('DETAIL', '')) for item in data if item.get('DETAIL')]
    
    if not documents:
        print("Warning: No documents found in the JSON file. No retriever will be created.")
        return None

    # 1. Initialize BM25 retriever for keyword search
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 2

    # 2. Initialize FAISS retriever for semantic search
    embeddings = OpenAIEmbeddings(chunk_size=100)
    vectorstore = FAISS.from_documents(documents, embeddings)
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # 3. Initialize Ensemble Retriever to combine both
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5]
    )
    
    return ensemble_retriever
