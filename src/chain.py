"""RAG chain: retrieves context from runbooks and queries Groq LLM."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from config import GROQ_API_KEY, GROQ_MODEL
from retriever import get_retriever


def _format_docs(docs) -> str:
    """Join retrieved documents into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)


def get_rag_chain():
    """Create a RAG chain that retrieves context and generates responses."""

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0.5,
        api_key=GROQ_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert infrastructure and IoT operations engineer. 
Your role is to help troubleshoot issues using the provided runbooks.

Answer the user's question based ONLY on the provided runbook context.
If the context doesn't contain information to answer the question, say so clearly.
Be concise, actionable, and technical."""),
        ("human", """{context}

---

Question: {question}

Provide a clear, step-by-step response based on the runbooks above."""),
    ])

    retriever = get_retriever()
    chain = prompt | llm | StrOutputParser()

    return {
        "retriever": retriever,
        "chain": chain,
        "llm": llm,
        "prompt": prompt,
    }


def query_rag(question: str) -> str:
    """
    Query the RAG system and return the response.

    Args:
        question: User's question

    Returns:
        LLM's response based on retrieved runbook context
    """
    rag_chain = get_rag_chain()
    retriever = rag_chain["retriever"]
    chain = rag_chain["chain"]

    # Retrieve relevant documents
    docs = retriever.invoke(question)

    # Generate response
    response = chain.invoke({
        "context": _format_docs(docs),
        "question": question,
    })

    return response