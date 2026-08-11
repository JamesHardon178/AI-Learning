# 该文件的主要功能：
# 处理聊天与认证 API 请求。
# 使用 FastAPI 接收用户消息，利用 JWT 依赖项实现身份校验与多租户隔离，
# 构建 Prompt，调用 LLM 流式生成，同时将历史记录持久化至 Redis。

from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from schemas import ChatRequest
from prompt_service import build_prompt
from llm_service import chat_with_llm_stream
from memory_service import get_history, save_message
from auth_service import create_access_token, get_current_user_id


def format_sse_event(content: str) -> str:
    """格式化 SSE 消息格式，确保换行符标准且遵循 data: 协议"""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(f"data: {line}\n" for line in normalized.split("\n")) + "\n"


app = FastAPI(title="AI ChatBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    """登录请求体数据模型"""
    username: str
    password: str


@app.post("/login")
def login(request: LoginRequest):
    """
    模拟登录接口：
    校验用户名密码，通过后签发带有 user_id 的 JWT Access Token
    """
    if request.username == "zhangsan" and request.password == "123456":
        # 假设 zhangsan 的用户 ID 是 user_001
        token = create_access_token(user_id="user_001")
        return {"access_token": token, "token_type": "bearer"}
    elif request.username == "lisi" and request.password == "123456":
        # 假设 lisi 的用户 ID 是 user_002
        token = create_access_token(user_id="user_002")
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )


@app.post("/chat")
def chat(
    request: ChatRequest,
    # 核心关卡：FastAPI 自动解析 Header 中的 Token，验证失败直接踢回 401；成功则返回 current_user_id
    current_user_id: Annotated[str, Depends(get_current_user_id)]
):

    # 1. 传入 user_id，获取该用户专属的历史聊天记录
    history = get_history(
        user_id=current_user_id,
        session_id=request.session_id
    )

    # 2. 传入 user_id，保存当前用户发送的消息
    save_message(
        user_id=current_user_id,
        session_id=request.session_id,
        role="user",
        content=request.message
    )

    # 3. 构建 Prompt
    prompt = build_prompt(
        history,
        request.message
    )

    # 4. 包装 LLM 流式输出
    def generate_response():

        full_answer = ""

        try:
            # 逐段获取模型输出
            for chunk in chat_with_llm_stream(prompt):

                # 拼接完整答案
                full_answer += chunk

                # 立即发送给客户端
                yield format_sse_event(chunk)
        except Exception as error:
            print(f"Streaming response failed: {error}")
            yield format_sse_event("抱歉，生成过程中连接中断，请稍后重试。")
        else:
            # 5. 模型无异常生成结束后，保存 AI 回复（同样带上 user_id）
            save_message(
                user_id=current_user_id,
                session_id=request.session_id,
                role="assistant",
                content=full_answer
            )

    # 6. 返回流式响应
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )