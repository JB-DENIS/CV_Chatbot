import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.internal.bdd_manager import (
    create_collection,
    get_ensemble_retriever,
    get_retriever,
    get_vector_store,
)
from app.internal.embedder import get_embedder
from app.internal.export_report import create_pdf_report
from app.internal.llm_chat import (
    generate_summary,
    get_chat_llm,
    get_conversational_rag_chain,
    get_documents_retrieve,
    get_format_output,
    get_history_retriever,
    get_llm_answer,
    get_rag_chain,
    get_session_history,
    get_system_prompt_chain,
    question_to_conversational_rag_chain,
)
from app.internal.template_prompt import contextualize_q_prompt, qa_prompt
from app.settings import settings

# Initialisation du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chat_router = APIRouter(
    prefix="/chatting",
    tags=["question_anwser"],
    responses={404: {"description": "Not found"}},
)


class QueryRequest(BaseModel):
    user_query: str
    session_id: str = settings.session_id


class ResponseOutput(BaseModel):
    answer: str
    context: List[str]
    formatted_output: str


class Conversation(BaseModel):
    messages: List[Any]


class ResponseOutputSum(BaseModel):
    summary: str


# Initialisation des ressources
user_collection_name = settings.user_collection_name
logger.info("Initializing collection: %s", user_collection_name)
create_collection(user_collection_name)

doc_collection_name = settings.doc_collection_name
logger.info("Initializing collection: %s", doc_collection_name)
create_collection(doc_collection_name)

embedder = get_embedder(provider=settings.provider)
logger.info("Embedder initialized.")

doc_vector_store = get_vector_store(embedder, doc_collection_name)
logger.info("Vector store initialized with collection: %s", doc_collection_name)

user_vector_store = get_vector_store(embedder, user_collection_name)
logger.info("Vector store initialized with collection: %s", user_collection_name)

logger.info("Initializing LLM and retrievers...")
llm = get_chat_llm()
user_retriever = get_retriever(user_vector_store)
doc_retriever = get_retriever(doc_vector_store)
retriever = get_ensemble_retriever(doc_retriever, user_retriever)

logger.info("Creating history-aware retriever...")
history_retriever = get_history_retriever(llm, retriever, contextualize_q_prompt)

logger.info("Creating system prompt chain...")
qa_chain = get_system_prompt_chain(llm, qa_prompt)

logger.info("Creating RAG chain...")
rag_chain = get_rag_chain(history_retriever, qa_chain)

logger.info("Initializing conversational RAG chain...")
conversational_chain = get_conversational_rag_chain(
    rag_chain,
    lambda sid: get_session_history(settings.session_id, settings.history_store),
)


@chat_router.post("/chat", response_model=ResponseOutput)
async def chat_with_rag_chain(request: QueryRequest):
    """
    Route pour interagir avec le RAG (Retrieval-Augmented Generation) Chain.
    """
    logger.info("Received chat request with session_id: %s", request.session_id)
    logger.info("User query: %s", request.user_query)

    try:
        logger.info("Processing user query...")
        response = question_to_conversational_rag_chain(
            request.user_query, conversational_chain, request.session_id
        )
        logger.info("LLM response received: %s", response)

        answer = get_llm_answer(response)
        documents = get_documents_retrieve(response)

        logger.info("Formatting output...")
        formatted_output = get_format_output(answer, documents)

        logger.info(
            "Successfully processed chat request for session_id: %s", request.session_id
        )
        return {
            "answer": answer,
            "context": documents,
            "formatted_output": formatted_output,
        }

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Internal server error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@chat_router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Route pour récupérer l'historique des messages pour une session donnée.
    """
    logger.info("Fetching chat history for session_id: %s", session_id)

    try:
        history = get_session_history(session_id, settings.history_store)
        logger.info(
            "Successfully retrieved chat history for session_id: %s", session_id
        )
        return {"session_id": session_id, "history": history.messages}
    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Internal server error while fetching history: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@chat_router.post("/chat", response_model=ResponseOutput)
async def chat_with_rag_chain(request: QueryRequest):
    """
    Route pour interagir avec le RAG (Retrieval-Augmented Generation) Chain.
    """
    logger.info("Received chat request with session_id: %s", request.session_id)
    logger.info("User query: %s", request.user_query)

    try:
        logger.info("Processing user query...")
        response = question_to_conversational_rag_chain(
            request.user_query, conversational_chain, request.session_id
        )

        answer = get_llm_answer(response)
        documents = get_documents_retrieve(response)

        logger.info("Formatting output...")
        formatted_output = get_format_output(answer, documents)

        logger.info(
            "Successfully processed chat request for session_id: %s", request.session_id
        )
        return {
            "answer": answer,
            "context": documents,
            "formatted_output": formatted_output,
        }

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Internal server error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@chat_router.post("/summary", response_model=ResponseOutputSum)
async def summarize_conversation(conversation: Conversation):
    """
    Génère un résumé de la conversation et liste les documents PDF référencés.

    Args:
        conversation (Conversation): Objet contenant les messages de la conversation.

    Returns:
        dict: Résumé de la conversation et liste des documents PDF référencés.
    """
    outpur_path = r"..\Shared_data\export.pdf"
    # outpur_path = r"C:\Users\jeanb\Documents\kzs-team\Shared_data\export.pdf"
    logo_path = r"app\resources\logo_ademe.png"
    summary_text = generate_summary(llm, conversation.messages)

    create_pdf_report(outpur_path, logo_path, summary_text)

    return {"summary": summary_text}
