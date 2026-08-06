# 该文件作用: 定义请求和响应的 Pydantic 模型，用于 FastAPI 的数据验证和序列化。
from pydantic import BaseModel, Field
from typing import Literal


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str