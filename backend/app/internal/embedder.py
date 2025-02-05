from langchain_openai import OpenAIEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from app.settings import settings


def get_embedder(provider: str = "hf_api"):
    if provider == "hf_local":
        return HuggingFaceEmbeddings(
            model_name=settings.embedding_model_name,
        )

    if provider == "hf_api":
        return HuggingFaceInferenceAPIEmbeddings(
            model_name=settings.embedding_model_name,
            api_key=settings.hf_token,
        )

    if provider == "openai":
        return OpenAIEmbeddings(
            openai_api_key=settings.scw_api_key,
            openai_api_base=settings.scw_generative_apis_endpoint,
            model=settings.embedding_model_name,
            tiktoken_enabled=False,
        )
    return None
