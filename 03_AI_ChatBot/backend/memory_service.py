"""Redis-backed chat history storage."""

import os
from typing import Literal

import redis

from schemas import Message


redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)
key_prefix = os.getenv("REDIS_KEY_PREFIX", "chat:history:")


def _history_key(session_id: str) -> str:
    return f"{key_prefix}{session_id}"


def save_message(
    session_id: str,
    role: Literal["system", "user", "assistant"],
    content: str,
) -> None:
    """Append one validated chat message to the session history."""
    message = Message(role=role, content=content)
    redis_client.rpush(_history_key(session_id), message.model_dump_json())


def get_history(session_id: str) -> list[Message]:
    """Return all chat messages stored for the session."""
    raw_messages = redis_client.lrange(_history_key(session_id), 0, -1)
    return [Message.model_validate_json(raw_message) for raw_message in raw_messages]
