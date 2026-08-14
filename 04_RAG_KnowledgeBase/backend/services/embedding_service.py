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

    response = requests.post(
        OLLAMA_URL,
        json=payload
    )

    response.raise_for_status()

    data = response.json()

    return data["embeddings"][0]