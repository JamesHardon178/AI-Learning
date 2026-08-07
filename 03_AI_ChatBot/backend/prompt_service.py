# 该文件的作用：负责构建发送给大语言模型的 Prompt。
def build_prompt(history, message):

    prompt = """
你是一个智能聊天助手。

你的任务：
帮助用户进行自然聊天。

规则：
1. 优先参考历史聊天记录
2. 如果历史中有用户提供的信息，直接使用
3. 不要介绍自己是Qwen、AI模型或语言模型
4. 不要输出无关的解释
5. 回答简洁准确


历史聊天记录：

"""

    # 添加历史消息
    for msg in history:
        prompt += f"""
{msg.role}:
{msg.content}
"""

    # 添加当前用户问题
    prompt += f"""

当前用户问题：

{message}

请直接回答：
"""

    return prompt