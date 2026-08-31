import requests


OLLAMA_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "qllama/bge-m3:q4_k_m"


def embed_text(text: str) -> list[float]:
    """
    将单段文本转换为向量
    """

    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        raise RuntimeError("无法连接到 Ollama API。请检查服务是否运行。")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
        raise RuntimeError("请求 Ollama API 超时。请检查服务是否运行。")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        raise RuntimeError("请求 Ollama API 时发生 HTTP 错误。")

    data = response.json()

    return data["embeddings"][0]