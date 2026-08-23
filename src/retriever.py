"""Query the Chroma vector store for relevant runbook chunks."""

import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import CHROMA_DIR, EMBED_MODEL, OLLAMA_BASE_URL, TOP_K

COLLECTION_NAME = "runbooks"


def get_retriever():
    """Load the persisted Chroma store and return a retriever."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    return retriever


def retrieve_context(query: str) -> str:
    """
    Retrieve the top-K most relevant chunks for a query.
    
    Args:
        query: User's question or search string
        
    Returns:
        Formatted context string with retrieved chunks and sources
    """
    retriever = get_retriever()
    docs = retriever.invoke(query)
    
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"[{i}] Source: {source}\n{doc.page_content}")
    
    return "\n\n---\n\n".join(context_parts)