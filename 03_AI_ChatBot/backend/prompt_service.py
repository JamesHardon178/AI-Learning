"""
作用：
负责构建发送给大语言模型的 Prompt。

职责：
1. 管理系统提示词
2. 处理历史聊天记录
3. 拼接当前用户问题

不负责：
- 调用模型
- HTTP请求
- 数据库操作
"""


def build_prompt(history, message):
    """
    构建大语言模型需要的 Prompt

    参数:
        history:
            历史聊天记录列表

        message:
            当前用户输入

    返回:
        str类型 Prompt
    """

    # 1. 系统提示词
    prompt_parts = []

    system_prompt = """
你是一名AI应用开发工程师。
回答要求：
1. 简单易懂
2. 有理有据
3. 包含实际例子
"""
    prompt_parts.append(system_prompt)
    # 2. 添加历史消息
    if history:
        prompt_parts.append("历史聊天记录：")
        for msg in history:
            prompt_parts.append(
                f"{msg.role}: {msg.content}"
            )
    # 3. 添加当前用户问题
    prompt_parts.append(
        f"user: {message}"
    )
    # 4. 拼接成最终Prompt
    prompt = "\n\n".join(prompt_parts)
    return prompt