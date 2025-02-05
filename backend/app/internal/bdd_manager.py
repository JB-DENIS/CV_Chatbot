from typing import Any
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import CollectionStatus
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.vectorstores import VectorStore
from app.settings import settings


try:
    client = QdrantClient(url=settings.qdrant_url)

except Exception as e:
    raise Exception(f"Error connecting to Qdrant: {e}")


def create_collection(collection_name: str):
    """
    Create a collection in Qdrant if it does not already exist.

    Args:
        collection_name (str): The name of the collection to be created.

    Returns:
        str: A message indicating the result of the operation.

    Raises:
        Exception: If there is an error during the collection creation process.
    """
    try:
        existing_collections = client.get_collections()
        if any(col.name == collection_name for col in existing_collections.collections):
            return f"Collection '{collection_name}' already exists."

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        return f"Collection '{collection_name}' created successfully."

    except Exception as e:
        raise Exception(f"Error creating collection '{collection_name}': {e}")


def get_vector_store(embeddings, collection_name):
    """
    Retrieve or initialize a Qdrant vector store for a given collection.

    Args:
        embeddings: The embedding model or function to be used for vectorization.
        collection_name (str): The name of the Qdrant collection.

    Returns:
        QdrantVectorStore: A Qdrant vector store object tied to the specified collection.

    Raises:
        Exception: If the collection does not exist or there is an issue accessing it.
    """
    try:
        collection_info = client.get_collection(collection_name)

        if collection_info.status != CollectionStatus.GREEN:
            raise Exception(
                f"Collection '{collection_name}' is not active (status: {
                    collection_info.status})."
            )

        return QdrantVectorStore(
            client=client, collection_name=collection_name, embedding=embeddings
        )

    except UnexpectedResponse as e:
        raise Exception(
            f"Collection '{
                collection_name}' does not exist or could not be accessed: {e}"
        )

    except Exception as e:
        raise Exception(
            f"An error occurred while retrieving the vector store for '{
                collection_name}': {e}"
        )


def get_retriever(vector_store: VectorStore) -> VectorStoreRetriever:
    """
    Converts a vector store into a retriever instance.

    Args:
        vector_store: An object that represents the vector store. It must have an `as_retriever` method.

    Returns
    -------
        VectorStoreRetriever: An instance of VectorStoreRetriever for querying the vector store.

    Raises
    ------
        AttributeError: If the provided vector store does not have an `as_retriever` method.
    """  # noqa: D401
    if not hasattr(vector_store, "as_retriever"):
        raise AttributeError(
            "The provided vector store does not have an 'as_retriever' method."
        )

    return vector_store.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.7})


def get_ensemble_retriever(
    retriever_doc: VectorStoreRetriever, retriever_user: VectorStoreRetriever
) -> EnsembleRetriever:
    """
    Create an ensemble retriever that combines two retrievers with specified weights.

    Args:
        retriever_doc (VectorStoreRetriever): The first retriever,
        typically for document retrieval.
        retriever_user (VectorStoreRetriever): The second retriever,
        typically for user-specific retrieval.

    Returns:
        EnsembleRetriever: An instance of `EnsembleRetriever` combining the two retrievers
        with the specified weights (0.2 for `retriever_doc` and 0.8 for `retriever_user`).
    """
    return EnsembleRetriever(
        retrievers=[retriever_doc, retriever_user], weights=[0.2, 0.8]
    )
