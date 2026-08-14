import chromadb


CHROMA_PATH = "data/chroma"

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    name="knowledge_base"
)


def add_documents(
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict]
):
    """
    将文本、向量、元数据写入 Chroma
    """

    ids = [
        f"chunk_{i}"
        for i in range(len(documents))
    ]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )


def search(
    query_embedding: list[float],
    top_k: int = 3
):
    """
    根据查询向量检索最相关的 Chunk
    """

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return result