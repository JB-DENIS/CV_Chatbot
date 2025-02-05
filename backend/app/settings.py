import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    llm_model_name: str = "HuggingFaceH4/zephyr-7b-beta"
    context_window_size: int = 5
    retrieval_top_k: int = 3
    temperature: float = 0.2
    max_length: int = 2048
    hf_token: str = os.getenv("HF_TOKEN")

    if not hf_token:
        raise ValueError(
            "ERREUR : Le token Hugging Face (HF_TOKEN) n'est pas défini ! Ajoute-le dans les variables d'environnement Hugging Face Spaces."
        )

    embedding_model_name: str = "sentence-transformers/sentence-t5-xxl"
    # qdrant_url: str = "http://qdrant:6333"
    qdrant_url: str = "http://localhost:6333"
    parser: str = "openparse"
    history_store: dict = {}
    session_id: str = "user012025"
    user_collection_name: str = "User_Ademe_collection"
    doc_collection_name: str = "Doc_Ademe_collection"
    provider: str = "hf_api"


settings = Settings()
