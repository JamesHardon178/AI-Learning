import requests
import logging
from services.embedding_service import embed_text
from services.vector_service import search
import time

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:7b-instruct"


def generate_answer(prompt: str) -> str:
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
    }
    llm_start=time.time()
    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return "无法连接到 Ollama API。请检查服务是否运行。"
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        return "请求 Ollama API 超时。请检查服务是否运行。"
    data = response.json()

    llm_elapsed_time=time.time()-llm_start
    logger.info(
        "LLM生成完成，耗时 %.2f 秒",
        llm_elapsed_time
    )
    return data["response"]

# 距离阈值：基于实测数据标定（2026-09-01）
#
# 标定方法：用 10 个知识库内问题和 5 个知识库外问题测 top-1 距离：
#   库内问题距离范围：0.548 ~ 0.918
#   库外问题距离范围：1.155 ~ 1.306
# 两条分布之间存在 0.92 ~ 1.16 的隔离带，取 1.0 作为阈值：
#   - 低于 1.0：判定为「知识库内问题」，放行
#   - 高于 1.0：判定为「知识库外问题」，过滤（触发空检索兜底话术）
#
# 注意：更换 Embedding 模型后距离分布会整体变化，必须重新标定。
DISTANCE_THRESHOLD = 1.0


def retrieve_documents(query: str):
    start_time=time.time()
    query_embedding = embed_text(query)
    elapsed_time=time.time()-start_time
    logger.info(
        "Embedding生成完成，耗时 %.2f 秒",
        elapsed_time
    )

    retrieval_start=time.time()
    result = search(
        query_embedding=query_embedding,
        top_k=1
    )
    retrieval_elapsed_time=time.time()-retrieval_start
    logger.info(
        "向量检索完成，耗时 %.2f 秒",
        retrieval_elapsed_time
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
        chunk_index = metadata.get("chunk_index", "未知")

        if distance < DISTANCE_THRESHOLD:
            logger.debug(
                f"Chunk={chunk_index}, "
                f"distance={distance}, "
                f"threshold={DISTANCE_THRESHOLD}, "
                f"status=通过"
            )

            filtered_documents.append(document)
            filtered_metadatas.append(metadata)

        else:
            logger.debug(
                f"Chunk={chunk_index}, "
                f"distance={distance}, "
                f"threshold={DISTANCE_THRESHOLD}, "
                f"status=过滤"
            )
    if not filtered_documents:
        logger.warning(
            "没有找到满足 Distance Threshold 的 Chunk，"
            "query=%r, threshold=%.2f",
            query, DISTANCE_THRESHOLD
        )
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

# 检索知识库内容，生成回答，并返回引用信息
def rag_query(query: str):
    rag_start = time.time()
    logger.info("RAG请求开始，query=%r", query)

    documents, metadatas = retrieve_documents(query)

    context = build_context(
        documents,
        metadatas
    )

    logger.info(
        "检索完成，命中 %d 个 Chunk",
        len(documents)
    )

    logger.debug("\n===== Context =====")
    logger.debug(context)

    prompt = build_prompt(
        query,
        context
    )     

    logger.debug("\n===== Prompt =====")
    logger.debug(prompt)

    answer = generate_answer(prompt)

    citations = build_citations(metadatas)
    rag_elapsed_time = time.time() - rag_start
    logger.info(
        "RAG请求完成，耗时 %.2f 秒",
        rag_elapsed_time
    )
    logger.info(
        "RAG请求完成，耗时 %.2f 秒",
        rag_elapsed_time
    )
    return {
        "answer": answer,
        "citations": citations
    }