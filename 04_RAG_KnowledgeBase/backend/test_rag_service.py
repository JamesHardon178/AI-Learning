from services.rag_service import retrieve_documents

query = "怎么查看项目操作记录？"

documents, metadatas = retrieve_documents(query)

print("\n===== 检索结果 =====")

for document, metadata in zip(documents, metadatas):
    print(f"\n📄 {metadata.get('source')}")
    print(f"📌 Chunk {metadata.get('chunk_index')}")
    print(f"内容：{document}")