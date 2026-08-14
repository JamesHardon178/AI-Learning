import requests
from services.embedding_service import embed_text
from services.vector_service import search

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:0.5b"


def generate_answer(prompt: str) -> str:
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload
    )

    response.raise_for_status()

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

你的唯一任务是：
从【知识库内容】中找到与【用户问题】直接相关的信息，并进行准确、简洁的回答。

【绝对规则】

1. 只能使用【知识库内容】中明确出现的信息。
2. 不允许使用你的常识、经验、推测或猜测。
3. 不允许补充知识库没有出现的页面、按钮、菜单、字段、操作步骤或功能。
4. 不允许重新设计操作流程。
5. 不允许把不同业务场景中的步骤组合起来。
6. 如果知识库没有明确回答用户问题，只回答：
“知识库中没有找到相关信息。”
7. 如果知识库只提供了部分步骤，只回答这些明确存在的步骤。
8. 对于操作步骤问题，必须严格按照知识库出现的操作顺序回答。
9. 不要添加知识库中不存在的前置步骤或后置步骤。
10. 不要使用“通常”“一般”“应该”“例如”“比如”等词语进行推测。
11. 不要解释你是如何找到答案的。
12. 不要输出“首先，我们需要……”“通过这个过程……”等分析过程。
13. 不要改变知识库中的页面名称、按钮名称和功能名称。
14. 如果知识库明确写出了操作步骤，优先直接引用这些步骤，不要自行改写成新的操作流程。
15. 对于“怎么修改”“怎么编辑”“怎么查看”等操作问题，只提取与该操作直接对应的知识库内容。

【特别重要】

你的回答必须能够在【知识库内容】中逐句找到依据。

如果你准备输出一句话，请先确认这句话是否在知识库中有明确依据。

如果没有明确依据，就不要输出。

【知识库内容】
{context}

【用户问题】
{query}

现在直接回答用户问题，不要解释你的思考过程。
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

    answer = generate_answer(prompt)

    citations = build_citations(metadatas)

    return {
        "answer": answer,
        "citations": citations
    }