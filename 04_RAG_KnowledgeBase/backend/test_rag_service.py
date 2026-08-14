from services.rag_service import rag_query


query = "我的日报在哪里查看？"

result = rag_query(query)

print("\n===== AI回答 =====")
print(result["answer"])

print("\n===== 来源 =====")

for metadata in result["metadatas"]:
    print(f"📄 {metadata.get('source')}")
    print(f"📌 Chunk {metadata.get('chunk_index')}")