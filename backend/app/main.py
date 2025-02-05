"""Main module."""

import logging
from typing import Any
import uvicorn
from fastapi import FastAPI

from app.routers.chatting import chat_router
from app.routers.embedding import embedding_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(embedding_router)
app.include_router(chat_router)


@app.get("/")
async def root() -> Any:  # noqa: ANN401
    """Return greetings."""
    return {"message": "Hello ADEME!"}


if __name__ == "__main__":
    uvicorn.run(app, log_level="info")
