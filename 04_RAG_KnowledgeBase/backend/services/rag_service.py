import requests
import logging
from services.embedding_service import embed_text
from services.vector_service import search
import time
import uuid
from schemas.rag_schema import RAGMetrics
from services.token_service import count_tokens
from logging_context import request_id_context
logger=logging.getLogger(__name__)
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:7b-instruct"


def generate_answer(prompt: str) -> tuple:
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
        return "无法连接到 Ollama API。请检查服务是否运行。", 0
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        return "请求 Ollama API 超时。请检查服务是否运行。", 0
    data = response.json()

    llm_elapsed_time=time.time()-llm_start
    logger.info(
        "LLM生成完成，耗时 %.2f 秒",
        llm_elapsed_time
    )
    return data["response"],llm_elapsed_time

# 距离阈值：基于实测数据标定（2026-09-01 第二次标定）
#
# 库变化后必须重新标定！本次库从 28 chunks 扩到 241 chunks（3 个文档）后：
#   库内问题 top-1 距离：0.548 ~ 0.918
#   库外问题 top-1 距离：1.011 ~ 1.229
# 隔离带变窄（0.918 ~ 1.011），取中间偏保守的 0.95：
#   - 低于 0.95：判定为「知识库内问题」，放行
#   - 高于 0.95：判定为「知识库外问题」，过滤（触发空检索兜底话术）
#
# 注意：每次增删文档、更换 Embedding 模型后，距离分布都会变化，必须重新标定。
DISTANCE_THRESHOLD = 0.95

# 检索返回的候选 chunk 数量。
# 之前是 1（单点脆弱：第一个不相关就没有兜底）。
# 改成 3 后由阈值过滤，让「召回多个候选 → 过滤 → 只留相关的」成为完整流程。
TOP_K = 3


def retrieve_documents(query: str):
    start_time=time.time()
    query_embedding = embed_text(query)
    embedding_latency=time.time()-start_time
    logger.info(
        "Embedding生成完成，耗时 %.2f 秒",
        embedding_latency
    )

    retrieval_start=time.time()
    result = search(
        query_embedding=query_embedding,
        top_k=TOP_K
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
            logger.info(
                f"Chunk={chunk_index}, "
                f"distance={distance:.4f}, "
                f"threshold={DISTANCE_THRESHOLD}, "
                f"status=通过"
            )

            filtered_documents.append(document)
            filtered_metadatas.append(metadata)
        else:
            logger.info(
                f"Chunk={chunk_index}, "
                f"distance={distance:.4f}, "
                f"threshold={DISTANCE_THRESHOLD}, "
                f"status=过滤"
    )
    if not filtered_documents:
        logger.warning(
            "没有找到满足 Distance Threshold 的 Chunk，threshold=%.2f",
            DISTANCE_THRESHOLD
    )
    logger.info(
    "Retrieval统计：检索 %d 个 Chunk，过滤后保留 %d 个 Chunk",
    len(documents),
    len(filtered_documents)
    )
    return (
    filtered_documents,
    filtered_metadatas,
    len(documents),
    len(filtered_documents),
    embedding_latency,
    retrieval_elapsed_time
    )
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
    request_id = str(uuid.uuid4())
    request_id_context.set(request_id)
    start_time = time.time()
    rag_start=time.time()
    logger.info("RAG请求开始，request_id=%s", request_id)

    documents, metadatas, retrieval_count, filtered_count, embedding_latency, retrieval_latency = retrieve_documents(query)

    context = build_context(
        documents,
        metadatas
    )

    logger.info(
        "检索完成，request_id=%s，命中 %d 个 Chunk",
        request_id,
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

    answer, llm_latency = generate_answer(prompt)
    input_tokens = count_tokens(prompt)
    output_tokens = count_tokens(answer)
    total_tokens = input_tokens + output_tokens

    citations = build_citations(metadatas)
    logger.info(
    "Citation统计：生成 %d 个 Citation",
    len(citations)
    )
    rag_elapsed_time=time.time()-rag_start
    total_latency = time.time() - start_time
    request_metrics = RAGMetrics(
        retrieval_count=retrieval_count,
        filtered_count=filtered_count,
        citation_count=len(citations),
        embedding_latency=embedding_latency,
        retrieval_latency=retrieval_latency,
        llm_latency=llm_latency,
        total_latency=total_latency,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens
)
    logger.info(
        "RAG Metrics:%s",
        request_metrics
    )
    logger.info(
        "RAG请求完成，total_latency=%.2f 秒",
        total_latency
    )
    return {
        "answer": answer,
        "citations": citations
    }