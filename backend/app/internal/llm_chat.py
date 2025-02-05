import uuid
from typing import Any, Callable, Dict, List

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.base import Chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from app.internal.export_report import extract_pdf_references
from app.internal.template_prompt import summary_system_prompt
from app.settings import settings


def get_chat_llm() -> BaseChatModel:
    """
    Initializes and returns a ChatOpenAI instance configured with the provided settings.

    Returns:
        ChatOpenAI: An instance of ChatOpenAI configured to use the specified model, API endpoint, and API key.

    Raises:
        ValueError: If any of the required settings (endpoint, API key, or model name) is missing.
    """
    try:
        if settings.provider == "hf_local":
            pass

        if settings.provider == "hf_api":
            if not settings.hf_token:
                raise ValueError("The HugginFace APIs token is not set.")

            llm = HuggingFaceEndpoint(
                repo_id=settings.llm_model_name,
                task="text-generation",
                max_new_tokens=settings.max_length,
                do_sample=False,
                repetition_penalty=1.03,
                temperature=settings.temperature,
                # huggingfacehub_api_token=settings.hf_token,
            )

            return ChatHuggingFace(llm=llm)

        if settings.provider == "openai":
            if not settings.scw_generative_apis_endpoint:
                raise ValueError("The SCW Generative APIs endpoint is not set.")
            if not settings.scw_api_key:
                raise ValueError("The SCW API key is not set.")
            if not settings.llm_model_name:
                raise ValueError("The LLM model name is not set.")

            return ChatOpenAI(
                base_url=settings.scw_generative_apis_endpoint,
                api_key=settings.scw_api_key,
                model=settings.llm_model_name,
                temperature=settings.temperature,
            )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize ChatOpenAI: {e}")


def get_history_retriever(llm, retriever, contextualize_q_prompt) -> object:
    """
    Creates a history-aware retriever using the provided LLM, retriever, and contextualization prompt.

    Args:
        llm: The language model used for generating context-aware queries.
        retriever: The retriever instance for querying a vector store or similar.
        contextualize_q_prompt: A prompt template for contextualizing queries.

    Returns:
        object: A history-aware retriever instance.

    Raises:
        ValueError: If any of the required inputs are None or invalid.
    """
    if not llm or not retriever or not contextualize_q_prompt:
        raise ValueError(
            "LLM, retriever, and contextualize_q_prompt must all be provided."
        )

    try:
        return create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    except Exception as e:
        raise RuntimeError(f"Failed to create history-aware retriever: {e}")


def get_system_prompt_chain(llm, qa_prompt) -> object:
    """
    Creates a prompt chain for processing system-level instructions with a question-answering prompt.

    Args:
        llm: The language model used for processing the system prompt.
        qa_prompt: The prompt template for question-answering tasks.

    Returns:
        object: A chain instance for system prompt processing.

    Raises:
        ValueError: If either `llm` or `qa_prompt` is None.
    """
    if not llm or not qa_prompt:
        raise ValueError("LLM and qa_prompt must both be provided.")

    try:
        return create_stuff_documents_chain(llm, qa_prompt)
    except Exception as e:
        raise RuntimeError(f"Failed to create system prompt chain: {e}")


def get_rag_chain(history_aware_retriever, question_answer_chain) -> object:
    """
    Creates a Retrieval-Augmented Generation (RAG) chain using a history-aware retriever and a Q&A chain.

    Args:
        history_aware_retriever: A retriever configured to incorporate conversation history into queries.
        question_answer_chain: A chain for handling question-answering tasks.

    Returns:
        object: A RAG chain instance.

    Raises:
        ValueError: If either `history_aware_retriever` or `question_answer_chain` is None.
    """
    if not history_aware_retriever or not question_answer_chain:
        raise ValueError(
            "Both history_aware_retriever and question_answer_chain must be provided."
        )

    try:
        return create_retrieval_chain(history_aware_retriever, question_answer_chain)
    except Exception as e:
        raise RuntimeError(f"Failed to create RAG chain: {e}")


def get_session_history(session_id: str, history_store: dict) -> BaseChatMessageHistory:
    """
    Retrieves or initializes the chat history for a given session ID.

    Args:
        session_id (str): The unique identifier for the session.
        history_store (dict): A dictionary to store session histories.

    Returns:
        BaseChatMessageHistory: The chat message history for the session.

    Raises:
        ValueError: If `session_id` is not provided.
    """
    if not session_id:
        raise ValueError("A valid session_id must be provided.")

    if session_id not in history_store:
        history_store[session_id] = ChatMessageHistory()

    return history_store[session_id]


def get_conversational_rag_chain(
    rag_chain: Chain,
    session_history_func: Callable[[str], BaseChatMessageHistory],
) -> RunnableWithMessageHistory:
    """
    Creates a conversational Retrieval-Augmented Generation (RAG) chain with session history.

    Args:
        rag_chain (Chain): The RAG chain for handling retrieval and generation tasks.
        session_history_func (Callable): A function to retrieve or initialize session history.

    Returns:
        RunnableWithMessageHistory: A chain that maintains message history and processes input/output.

    Raises:
        ValueError: If `rag_chain` or `session_history_func` is not provided.
    """
    if not rag_chain:
        raise ValueError("A valid rag_chain must be provided.")
    if not session_history_func:
        raise ValueError("A valid session history function must be provided.")

    return RunnableWithMessageHistory(
        rag_chain,
        session_history_func,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )


def question_to_conversational_rag_chain(
    user_query: str, conversational_rag_chain: Any, session_id: str = None
) -> Dict[str, Any]:
    """
    Sends a user query to a conversational RAG chain and retrieves the response.

    Args:
        user_query (str): The query from the user.
        conversational_rag_chain (Any): The conversational RAG chain instance.
        session_id (str, optional): A unique identifier for the session. If not provided, a new session_id is generated.

    Returns:
        Dict[str, Any]: The response from the conversational RAG chain.

    Raises:
        ValueError: If the user query is empty or the RAG chain is not provided.
        RuntimeError: If an error occurs during the invocation of the RAG chain.
    """
    if not user_query:
        raise ValueError("The user query must be a non-empty string.")
    if not conversational_rag_chain:
        raise ValueError("A valid conversational RAG chain must be provided.")

    # Generate a session_id if none is provided
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        # Invoke the conversational RAG chain
        return conversational_rag_chain.invoke(
            {"input": user_query}, config={"configurable": {"session_id": session_id}}
        )
    except Exception as e:
        raise RuntimeError(f"Failed to process the query with the RAG chain: {e}")


def get_documents_retrieve(output: Dict[str, Any], max_docs: int = 3) -> List[str]:
    """
    Retrieves the titles of the documents from the output context.

    Args:
        output (Dict[str, Any]): The output containing context and metadata.
        max_docs (int): The maximum number of document titles to retrieve. Default is 3.

    Returns:
        List[str]: A list of document titles.

    Raises:
        ValueError: If the 'context' key is missing or empty in the output.
    """
    if "context" not in output:
        return None

    return [
        output["context"][i].metadata.get("Title", "Untitled Document")
        for i in range(min(len(output["context"]), max_docs))
    ]  # TODO add filtre sur le type de documents à retourner


def get_llm_answer(output: Dict[str, Any]) -> str:
    """
    Extracts the answer generated by the LLM from the output.

    Args:
        output (Dict[str, Any]): The output containing the answer.

    Returns:
        str: The LLM-generated answer.

    Raises:
        ValueError: If the 'answer' key is missing or empty in the output.
    """
    if "answer" not in output or not output["answer"]:
        raise ValueError("The output does not contain a valid 'answer'.")

    return output["answer"]


def get_format_output(answer: str, context: List[str]) -> str:
    """
    Formats the LLM answer with a list of related document titles.

    Args:
        answer (str): The LLM-generated answer.
        context (List[str]): A list of document titles related to the answer.

    Returns:
        str: A formatted string containing the answer and document references.

    Raises:
        ValueError: If the answer is empty or None.
    """
    if not answer:
        raise ValueError("The 'answer' must be a non-empty string.")

    formatted_output = f"{answer}"
    if context:
        uniques_doc = set(context)
        formatted_output += (
            "\n\nConsultez les documents suivants pour plus d'information:\n\n"
        )
        formatted_output += "\n\n".join(uniques_doc)

    return formatted_output


def clean_output(answer):  # TODO add clean process for output
    pass


def generate_summary(llm, conversation: List[dict]) -> str:
    """
    Generate a summary of the conversation with LangChain and append PDF references at the end.

    Args:
        conversation (List[dict]): List of dictionaries representing the conversation.
                                   Each dictionary contains 'role' ('user' or 'assistant')
                                   and 'content' (message string).
        llm (str): OpenAI model to use.

    Returns:
        str: The generated summary with PDF references appended.
    """
    # Extract unique PDF references
    pdf_references = extract_pdf_references(conversation)

    # Prepare the messages
    messages = summary_system_prompt

    for message in conversation:
        if message["role"] == "user":
            messages.append(HumanMessage(content=message["content"]))

        elif message["role"] == "assistant":
            messages.append(AIMessage(content=message["content"]))

    # Generate the summary
    summary_prompt = ChatPromptTemplate.from_messages(messages).format()

    summary = llm.invoke(summary_prompt)

    # Append the PDF references
    summary_text = summary.content
    if pdf_references:
        summary_text += (
            "\n\nDocuments pdf à consulter pour plus d'information:"
            + "\n".join(sorted(pdf_references))
        )

    return summary_text
