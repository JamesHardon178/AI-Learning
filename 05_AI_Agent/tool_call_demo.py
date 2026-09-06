import requests
from enum import Enum


class AgentState(Enum):
    THINKING = "THINKING"
    TOOL_CALLING = "TOOL_CALLING"
    TOOL_EXECUTING = "TOOL_EXECUTING"
    TOOL_RESULT = "TOOL_RESULT"
    ERROR = "ERROR"
    FINAL = "FINAL"


def transition_from_thinking(tool_calls):
    if tool_calls:
        return AgentState.TOOL_CALLING

    return AgentState.FINAL


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
        "content": "123+456等于多少？"
    }
]


max_iterations = 5
iteration = 0

while iteration < max_iterations:

    iteration += 1

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

    # 根据 LLM 返回结果决定下一状态
    state = transition_from_thinking(tool_calls)

    print("当前状态:", state)

    # 如果不需要调用 Tool，直接结束
    if state == AgentState.FINAL:
        print("最终回答:", data["message"]["content"])
        break

    # 如果需要调用 Tool
    for tool_call in tool_calls:

        print("工具名称:", tool_call["function"]["name"])
        print("工具参数:", tool_call["function"]["arguments"])


        tool_name = tool_call["function"]["name"]

        tool = tool_registry.get(tool_name)

        if tool is None:

            result = f"工具不存在: {tool_name}"

            print("工具执行错误:", result)

            messages.append({
                "role": "tool",
                "content": result
            })

            continue

        arguments = tool_call["function"]["arguments"]

        try:

            result = tool(**arguments)

            state = AgentState.TOOL_RESULT

            print("当前状态:", state)

        except Exception as e:

            state = AgentState.ERROR

            print("当前状态:", state)

            result = f"工具执行失败: {str(e)}"

            print("工具执行错误:", result)

            messages.append({
                "role": "assistant",
                "tool_calls": data["message"]["tool_calls"]
            })

            messages.append({
                "role": "tool",
                "content": result
            })

            continue

        print("工具执行结果:", result)

        messages.append({
            "role": "assistant",
            "tool_calls": data["message"]["tool_calls"]
        })

        messages.append({
            "role": "tool",
            "content": str(result)
        })

        state = AgentState.THINKING

        print("当前状态:", state)

else:

   
    print("Agent 执行超过最大轮数，停止执行。")