"""
memory_service.py
业务职责：
1. 结合 user_id 和 session_id 实现多租户数据物理隔离
2. 聊天记录持久化至 Redis 并通过 TTL 实现滑动过期
3. 自动对 Redis 历史消息列表做滑动窗口截断（保护 LLM 上下文）
"""

import os
from typing import Literal

import redis
from schemas import Message

# 初始化 Redis 客户端连接
redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)

# 默认会话存活时间：7天（单位：秒）
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", 7 * 24 * 3600))

# 单个 Session 允许保留的最大历史消息条数（例如最多保留近 20 条，即 10 轮对话）
MAX_HISTORY_LEN = int(os.getenv("MAX_HISTORY_LEN", 20))


def _history_key(user_id: str, session_id: str) -> str:
    """内部辅助函数：生成带 user_id 隔离的 Redis Key，彻底消除越权隐患"""
    return f"chat:{user_id}:{session_id}"


def save_message(
    user_id: str,
    session_id: str,
    role: Literal["system", "user", "assistant"],
    content: str,
) -> None:
    """
    业务逻辑：追加一条校验过的消息到 Redis，裁剪超出最大长度的历史消息，并重新续期 TTL（滑动过期）
    """
    key = _history_key(user_id, session_id)
    message = Message(role=role, content=content)

    # 1. 将 Pydantic 对象序列化为 JSON 字符串并压入 List 末尾
    redis_client.rpush(key, message.model_dump_json())

    # 2. 【新增】维护滑动窗口：裁剪 Redis List，只保留最新的 MAX_HISTORY_LEN 条记录
    # -MAX_HISTORY_LEN 表示倒数第 N 条，-1 表示最后一条
    redis_client.ltrim(key, -MAX_HISTORY_LEN, -1)

    # 3. 刷新 Key 的过期时间，实现“有新对话就自动续期 7 天”
    redis_client.expire(key, SESSION_TTL)


def get_history(user_id: str, session_id: str) -> list[Message]:
    """
    业务逻辑：从 Redis 中读取属于指定用户的特定 Session 聊天历史
    """
    key = _history_key(user_id, session_id)
    # 获取 List 内的所有原始 JSON 字符串
    raw_messages = redis_client.lrange(key, 0, -1)
    # 反序列化为 Pydantic Message 对象列表后返回
    return [Message.model_validate_json(raw_message) for raw_message in raw_messages]