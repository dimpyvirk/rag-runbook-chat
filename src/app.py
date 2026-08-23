"""Chainlit UI for the RAG runbook chatbot."""

import chainlit as cl
from ingest import ingest_runbooks
from chain import query_rag


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chatbot on session start."""
    # Ensure vector store is populated
    try:
        ingest_runbooks()
    except Exception as e:
        await cl.Message(
            content=f"Error initializing vector store: {e}",
            author="System",
        ).send()
        return
    
    welcome = """Welcome to the Infrastructure Runbook Assistant! 🤖

I can help you troubleshoot IoT/infrastructure issues using your runbooks.

**Available topics:**
- MQTT broker connection loss
- Kubernetes pod CrashLoopBackOff
- Azure IoT Hub failover

Ask me anything like:
- "How do I fix MQTT connection loss?"
- "What should I do if my pod keeps crashing?"
- "What's the Azure failover procedure?"
"""
    
    await cl.Message(content=welcome).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    user_question = message.content
    
    try:
        # Query the RAG chain
        response = query_rag(user_question)
        
        await cl.Message(content=response).send()
    except Exception as e:
        await cl.Message(
            content=f"Error processing your question: {e}",
            author="System",
        ).send()