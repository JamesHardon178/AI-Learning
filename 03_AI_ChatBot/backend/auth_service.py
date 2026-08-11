"""
auth_service.py
业务职责：
1. JWT Token 的生成与解析（签发与校验身份证）
2. 提供 FastAPI 依赖注入关卡 (get_current_user_id)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# 从环境变量读取秘钥，若无则使用默认开发秘钥（生产环境必须通过 .env 配置强秘钥）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ai-learning-secret-key-change-it-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token 有效期：24 小时

# FastAPI 内置的 Authorization: Bearer <token> 提取器
security = HTTPBearer()


def create_access_token(user_id: str) -> str:
    """
    业务逻辑：用户登录成功后，根据 user_id 生成加密的 JWT Token
    :param user_id: 用户的唯一标识（如 user_001）
    :return: 签名后的加密 Token 字符串
    """
    # 算出 Token 的绝对过期时间（当前时间 + 24小时）
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 载荷（Payload）：放入 JWT 标准字段 sub (Subject) 和 exp (Expiration)
    payload = {
        "sub": user_id,
        "exp": expire
    }
    
    # 使用后端 SECRET_KEY 加密并返回 Token 字符串
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """
    FastAPI 依赖注入关卡（安检员）：
    1. 自动拦截请求，从 Request Header 提取 Bearer Token
    2. 校验 Token 的签名与过期时间 (exp)
    3. 校验通过解包返回 user_id，失败则直接中断请求并抛出 HTTP 401 异常
    """
    token = credentials.credentials
    
    # 定义标准的 401 身份未授权异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解密 Token，如果被篡改或已过期，jwt.decode 会直接抛出 JWTError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if not isinstance(user_id, str):
            raise credentials_exception
        return user_id  # 校验成功，将可信的 user_id 交付给后续路由处理函数
    except JWTError:
        # 拦截非法或已过期的请求，直接踢回 401
        raise credentials_exception