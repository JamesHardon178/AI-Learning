import requests
def get_weather(city: str):
    return f"{city}今天晴，27℃"
def calculate(expression: str):
    return eval(expression)
tool_registry = {
    "get_weather": get_weather,
    "calculate": calculate
}
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string"
                }
            },
            "required": ["city"]
        }
    }
}
calculate_tool = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "根据表达式进行计算",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "需要计算的数学表达式"
                }
            },
            "required": ["expression"]
        }
    }
}
url = "http://127.0.0.1:11434/api/chat"

messages = [
    {
        "role": "user",
        "content": "请计算 123 + 456。"
    }
]


while True:
    payload = {
    "model": "qwen2.5:7b-instruct",
    "messages": messages,
    "tools": [weather_tool, calculate_tool],
    "stream": False
    }
    response = requests.post(
        url,
        json=payload,
        timeout=(10, 300)
    )


    if response.status_code != 200:
        print("状态码:", response.status_code)
        print("错误信息:", response.text)

    response.raise_for_status()

    data = response.json()

    print(data)
    tool_calls = data["message"].get("tool_calls")

    if not tool_calls:
        print("最终回答:", data["message"]["content"])
        break

    else:
        for tool_call in tool_calls:
            print("工具名称:", tool_call["function"]["name"])
            print("工具参数:", tool_call["function"]["arguments"])

            tool_name = tool_call["function"]["name"]

            tool = tool_registry[tool_name]

            arguments = tool_call["function"]["arguments"]

            result = tool(**arguments)

            print("工具执行结果:", result)

            messages.append({
                "role": "assistant",
                "tool_calls": data["message"]["tool_calls"]
            })

            messages.append({
                "role": "tool",
                "content": str(result)
            })
