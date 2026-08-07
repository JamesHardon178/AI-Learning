"""
memory_service.py

作用：
负责管理聊天历史记录。

当前版本：
使用 Python dict 模拟存储。

企业版本：
Redis + MySQL
"""

from schemas import Message
# 模拟数据库/Redis
memory_store = {}


def save_message(session_id, role, content):
    """
    保存一条聊天消息

    参数:
        session_id:
            会话ID，用于区分不同聊天

        role:
            消息角色
            user / assistant / system

        content:
            消息内容
    """

    # 如果当前session不存在，则创建
    if session_id not in memory_store:
        memory_store[session_id] = []

    # 添加消息
    memory_store[session_id].append(
        Message(role=role, content=content)
    )


def get_history(session_id):
    """
    获取指定session的历史消息

    参数:
        session_id:
            会话ID

    返回:
        当前会话所有历史消息
    """

    return memory_store.get(session_id, [])