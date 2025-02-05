"""Embedding tools"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.internal.bdd_manager import create_collection, get_vector_store
from app.internal.embedder import get_embedder
from app.internal.parser import get_pdf_paths, get_text_chunker, parse_document
from app.settings import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

embedding_router = APIRouter(
    prefix="/embeddings",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

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

text_splitter = get_text_chunker()
logger.info("Text splitter initialized.")


def get_vectorstore(vectorstor_type):
    if vectorstor_type == "user":
        return user_vector_store

    if vectorstor_type == "doc":
        return doc_vector_store
    return None


class DocPathsInput(BaseModel):  # TODO move to schema.py
    doc_paths: str
    vectorstor_type: str


@embedding_router.post("/embedded/")
async def embedding(doc_paths_input: DocPathsInput):
    """
    Embeds documents provided via file paths and adds them to the vector store.

    Args:
        doc_paths_input (DocPathsInput): A Pydantic model containing
        a list of document file paths.

    Returns:
        dict: A response containing the number of documents added to the vector store.

    Raises:
        HTTPException: If the document parsing or embedding process fails.
    """

    logger.info("Received request to embed documents: %s", doc_paths_input.doc_paths)
    vector_store = get_vectorstore(doc_paths_input.vectorstor_type)

    try:
        folder_path = doc_paths_input.doc_paths
        logger.info(folder_path)
        doc_paths = get_pdf_paths(folder_path)
        logger.info(doc_paths)
        for path in doc_paths:
            try:
                logger.info("Parsing document at path: %s", path)
                parsed_documents = parse_document(path)
                doc_title = path.split("\\")[-1]
                logger.info("Document parsed: %s", doc_title)

                documents = text_splitter.create_documents(
                    parsed_documents,
                    metadatas=[
                        {"Title": doc_title} for _ in range(len(parsed_documents))
                    ],
                )
                logger.info(
                    "Created %d document chunks for: %s", len(documents), doc_title
                )

                vector_store.add_documents(documents)

                logger.info("Documents added to vector store: %s", doc_title)

            except Exception as e:
                logger.info(
                    f"An error occured during the parsing of the file {path}: {e}"
                )

        logger.info("All documents successfully processed and embedded.")
        return {
            "message": "Documents successfully embedded and stored",
            "documents_added": len(doc_paths),
        }

    except Exception as e:
        logger.error("An error occurred during the embedding process: %s", e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {e!s}")


class SearchQuery(BaseModel):  # TODO move to schema.py
    vectorstor_type: str
    query: str
    k: int = 2


@embedding_router.post("/similarity_search/")
async def search_documents(search_query: SearchQuery):
    """
    Search for documents in the vector store based on a query.

    Args:
        search_query (SearchQuery): A Pydantic model containing the query string and the number of results (k).

    Returns:
        List[dict]: A list of documents matching the query, including their content and metadata.

    Raises:
        HTTPException: If the search process fails or no documents are found.
    """
    logger.info("Received similarity search query: %s", search_query.query)

    vector_store = get_vectorstore(search_query.vectorstor_type)

    try:
        found_docs = vector_store.similarity_search(
            search_query.query, k=search_query.k
        )
        logger.info(
            "Found %d documents for query: %s", len(found_docs), search_query.query
        )

        if not found_docs:
            logger.warning("No documents found for query: %s", search_query.query)
            raise HTTPException(
                status_code=404, detail="No documents found for the given query."
            )

        logger.info("Returning results for query: %s", search_query.query)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata if hasattr(doc, "metadata") else None,
            }
            for doc in found_docs
        ]
    except Exception as e:
        logger.error("An error occurred during the similarity search: %s", e)
        raise HTTPException(
            status_code=500, detail=f"An error occurred during the search: {e}"
        )
