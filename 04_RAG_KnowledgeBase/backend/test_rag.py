from services.rag_service import rag_query


query = "怎么修改日报？"

result = rag_query(query)


print("\n===== 用户问题 =====")
print(query)

print("\n===== AI回答 =====")
print(result["answer"])

print("\n===== 来源 =====")

for metadata in result["metadatas"]:
    source = metadata.get("source", "未知来源")
    chunk_index = metadata.get("chunk_index", "未知")

    print(f"📄 {source}")
    print(f"📌 Chunk {chunk_index}")