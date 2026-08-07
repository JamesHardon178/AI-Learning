# 该文件的主要功能：
# 处理聊天API请求。
# 使用FastAPI接收用户消息，
# 构建Prompt，调用LLM流式生成，
# 同时保存聊天记录。


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from schemas import ChatRequest
from prompt_service import build_prompt
from llm_service import chat_with_llm_stream
from memory_service import get_history, save_message


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def chat(request: ChatRequest):

    # 1. 获取历史聊天记录
    history = get_history(request.session_id)

    # 2. 保存用户消息
    save_message(
        request.session_id,
        "user",
        request.message
    )

    # 3. 构建Prompt
    prompt = build_prompt(
        history,
        request.message
    )


    # 4. 包装LLM流式输出
    def generate_response():

        full_answer = ""

        # 逐段获取模型输出
        for chunk in chat_with_llm_stream(prompt):

            # 拼接完整答案
            full_answer += chunk

            # 立即发送给客户端
            yield chunk


        # 5. 模型结束后保存AI回复
        save_message(
            request.session_id,
            "assistant",
            full_answer
        )


    # 6. 返回流式响应
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )