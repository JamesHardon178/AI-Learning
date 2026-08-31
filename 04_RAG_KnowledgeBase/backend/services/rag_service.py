import requests
from services.embedding_service import embed_text
from services.vector_service import search

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:7b-instruct"


def generate_answer(prompt: str) -> str:
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
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
        return "无法连接到 Ollama API。请检查服务是否运行。"
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
        return "请求 Ollama API 超时。请检查服务是否运行。"
    data = response.json()

    return data["response"]

DISTANCE_THRESHOLD = 0.75


def retrieve_documents(query: str):
    query_embedding = embed_text(query)

    result = search(
        query_embedding=query_embedding,
        top_k=1
    )

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    filtered_documents = []
    filtered_metadatas = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        if distance < DISTANCE_THRESHOLD:
            filtered_documents.append(document)
            filtered_metadatas.append(metadata)

    return filtered_documents, filtered_metadatas


def build_context(documents, metadatas):
    context_parts = []

    for document, metadata in zip(documents, metadatas):
        source = metadata.get("source", "未知来源")
        chunk_index = metadata.get("chunk_index", "未知")

        context_parts.append(
            f"【来源：{source}，Chunk：{chunk_index}】\n{document}"
        )

    return "\n\n---\n\n".join(context_parts)

def build_prompt(query: str, context: str) -> str:
    prompt = f"""
你是一个企业产品知识库问答助手。

请根据下面的【知识库内容】回答【用户问题】。

回答要求：

1. 只能使用知识库中明确提供的信息。
2. 如果知识库中存在与用户问题直接相关的内容，直接回答这些内容。
3. 如果知识库没有相关信息，只回答：
知识库中没有找到相关信息。
4. 不要使用知识库之外的信息进行推测。
5. 不要添加知识库中没有出现的操作步骤。
6. 如果知识库提供了完整的操作步骤，按照原来的顺序回答。
7. 保留知识库中的页面名称、按钮名称和功能名称。
8. 回答简洁，不要解释推理过程。

【知识库内容】
{context}

【用户问题】
{query}

现在直接回答用户问题。
"""

    return prompt

def build_citations(metadatas):
    citations = []

    for metadata in metadatas:
        source = metadata.get("source", "未知来源")
        chunk_index = metadata.get("chunk_index", 0)

        citations.append({
            "source": source,
            "chunk_index": int(chunk_index)
        })

    return citations

def rag_query(query: str):
    documents, metadatas = retrieve_documents(query)

    context = build_context(
        documents,
        metadatas
    )

    print("\n===== Context =====")
    print(context)

    prompt = build_prompt(
        query,
        context
    )
    print("\n===== Prompt =====")
    print(prompt)
    answer = generate_answer(prompt)

    citations = build_citations(metadatas)

    return {
        "answer": answer,
        "citations": citations
    }