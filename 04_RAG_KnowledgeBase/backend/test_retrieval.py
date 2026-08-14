from services.embedding_service import embed_text
from services.vector_service import search


query = "我的日报在哪里查看？"


# 1. 用户问题 → 向量
query_embedding = embed_text(query)


# 2. 向量 → Chroma检索
result = search(
    query_embedding=query_embedding,
    top_k=3
)


# 3. 输出检索结果
documents = result["documents"][0]
metadatas = result["metadatas"][0]
distances = result["distances"][0]


for i in range(len(documents)):
    print(f"\n===== Top {i + 1} =====")
    print("距离：", distances[i])
    print("来源：", metadatas[i]["source"])
    print("Chunk：")
    print(documents[i])