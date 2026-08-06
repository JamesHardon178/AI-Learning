# 该文件的作用; 处理与大语言模型（LLM）交互的逻辑，包括发送请求和接收响应。
import requests
def chat_with_llm(message: str):
    url = "http://127.0.0.1:11434/api/generate"
    prompt = f"""
你是一名AI应用开发工程师。

请回答用户的问题。

回答要求：
1. 简单易懂
2. 有理有据
3. 包含实际例子

用户问题：
{message}
"""
    payload = {
        "model": "qwen2.5:0.5b",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(
        url,
        json=payload,
        timeout=60
    )
    result = response.json()
    return result["response"]