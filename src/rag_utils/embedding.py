import json
from typing import List, Dict, Any

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

def create_vector_store_from_json(file_path: str) -> FAISS:
    """
    Loads news data from a JSON file, creates embeddings, and builds a FAISS vector store.

    Args:
        file_path (str): The path to the JSON file. 
                         It is assumed that the JSON file contains a list of dictionaries, 
                         and each dictionary has a 'DETAIL' key with the text content.

    Returns:
        FAISS: The created FAISS vector store.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        # If the file is not found, return an empty vector store with a warning.
        print(f"Warning: JSON file not found at {file_path}. Returning an empty vector store.")
        data = []

    # The content is in the 'DETAIL' field of each JSON object
    documents = [Document(page_content=item.get('DETAIL', '')) for item in data if item.get('DETAIL')]
    
    if not documents:
        # If no documents were created (e.g., file not found or empty), create a dummy store.
        # This prevents the application from crashing if the data file is missing.
        embeddings = OpenAIEmbeddings(chunk_size=100)
        return FAISS.from_texts(["No data available"], embeddings)

    embeddings = OpenAIEmbeddings(chunk_size=100)
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore
