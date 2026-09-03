from services.token_service import count_tokens


prompt = """
请严格根据下面提供的知识库内容回答用户问题。

用户问题：
我的日报在哪里查看？

知识库内容：
在列表中找到目标日期的日报→点击【查看】。
"""

answer = "在列表中找到目标日期的日报，点击【查看】即可查看。"

print("Input Tokens：", count_tokens(prompt))
print("Output Tokens：", count_tokens(answer))
print("Total Tokens：", count_tokens(prompt) + count_tokens(answer))