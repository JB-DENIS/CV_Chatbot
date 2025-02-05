from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    api_url_chat: str = "http://backend/chatting/chat"
    api_url_embedding: str = "http://backend/embeddings/embedded"
    api_url_sum: str = "http://backend/chatting/summary"


settings = Settings()
