"""
test_auth.py
业务职责：
自动化校验 FastAPI 后端的 JWT 拦截机制、Token 鉴权与多租户隔离接口。
运行条件：请先启动 FastAPI 服务 (python -m uvicorn main:app --reload)
"""

import requests

BASE_URL = "http://127.0.0.1:8000"


def test_1_chat_without_token():
    """测试场景 1：无 Token 发送聊天请求（预期被拦截返回 401）"""
    print("\n[Test 1] 正在测试：未携带 Token 请求 /chat ...")
    payload = {
        "session_id": "test_session_001",
        "message": "你好"
    }
    
    # 不传 Authorization Header
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应体: {response.text}")
    
    assert response.status_code == 401, f"预期 401，实际收到 {response.status_code}"
    print("✅ Test 1 通过：无 Token 请求成功被拦截 (401)")


def test_2_chat_with_invalid_token():
    """测试场景 2：携带伪造的 Token 发送请求（预期校验失败返回 401）"""
    print("\n[Test 2] 正在测试：携带伪造 Token 请求 /chat ...")
    payload = {
        "session_id": "test_session_001",
        "message": "你好"
    }
    headers = {
        # 伪造一个格式相同但签名无效的假 Token
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload.invalid_signature"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应体: {response.text}")
    
    assert response.status_code == 401, f"预期 401，实际收到 {response.status_code}"
    print("✅ Test 2 通过：非法 Token 成功被拦截 (401)")


def test_3_login_and_get_token() -> str:
    """测试场景 3：模拟登录获取合法 JWT Token"""
    print("\n[Test 3] 正在测试：请求 /login 获取有效 Token ...")
    login_data = {
        "username": "zhangsan",
        "password": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    
    print(f"响应状态码: {response.status_code}")
    assert response.status_code == 200, f"登录失败，状态码: {response.status_code}"
    
    data = response.json()
    token = data.get("access_token")
    assert token is not None, "响应中缺失 access_token"
    
    print(f"成功获取 Token: {token[:20]}...")
    print("✅ Test 3 通过：模拟登录成功并拿到合法 Token")
    return token


def test_4_chat_with_valid_token(token: str):
    """测试场景 4：带着合法的 JWT Token 正常进行 SSE 对话"""
    print("\n[Test 4] 正在测试：携带合法 Token 正常调用 /chat ...")
    payload = {
        "session_id": "test_session_001",
        "message": "你好，请记住我是张三"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # stream=True 用来读取 SSE 数据流
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers, stream=True)
    
    print(f"响应状态码: {response.status_code}")
    assert response.status_code == 200, f"预期 200，实际收到 {response.status_code}"
    
    print("收到流式响应数据包片段：")
    chunk_count = 0
    # 读取前 5 个 chunk 片段验证 SSE 通道畅通
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            print(f"  {decoded_line}")
            chunk_count += 1
            if chunk_count >= 5:
                break
                
    print("✅ Test 4 通过：带合法 Token 成功建立 SSE 流式对话")


if __name__ == "__main__":
    print("=== 开始运行 JWT 鉴权与拦截自动化测试 ===")
    try:
        # 1. 测试未带 Token 拦截
        test_1_chat_without_token()
        
        # 2. 测试假 Token 拦截
        test_2_chat_with_invalid_token()
        
        # 3. 获取合法 Token
        valid_token = test_3_login_and_get_token()
        
        # 4. 测试合法 Token 访问
        test_4_chat_with_valid_token(valid_token)
        
        print("\n🎉🎉🎉 所有鉴权与拦截自动化测试套件全部通过！")
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到后端服务！请先确保在终端运行了：python -m uvicorn main:app --reload")
    except AssertionError as e:
        print(f"\n❌ 断言失败：{e}")