from services.vector_service import collection


def show_document_chunks(filename: str):
    result = collection.get(
        where={"source": filename},
        include=["documents", "metadatas"]
    )

    documents = result["documents"] or []
    metadatas = result["metadatas"] or []

    print(f"\n===== {filename} =====")
    print(f"Chunk 数量：{len(documents)}")

    for document, metadata in zip(documents, metadatas):
        print("\n" + "=" * 60)
        print(f"Chunk Index：{metadata.get('chunk_index')}")
        print("=" * 60)
        print(document)


if __name__ == "__main__":
    show_document_chunks("项目日志管理系统-产品手册.pdf")
    show_document_chunks("提纲第四部分.pdf")