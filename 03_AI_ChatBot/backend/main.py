# 该文件夹的主要功能是处理与聊天相关的API请求。它使用FastAPI框架来创建一个简单的Web服务，接收用户的聊天请求，并返回生成的回答。
from fastapi import FastAPI
from schemas import ChatRequest, ChatResponse
from prompt_service import build_prompt
from llm_service import chat_with_llm


app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    prompt = build_prompt(
        request.history,
        request.message
    )

    answer = chat_with_llm(prompt)

    return ChatResponse(
        answer=answer
    )