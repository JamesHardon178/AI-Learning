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
    metadatas: list[dict],
    id_prefix: str = "doc"
):
    """
    将文本、向量、元数据写入 Chroma

    id 设计：{id_prefix}_chunk_{i}

    为什么带前缀：
    之前用 chunk_0, chunk_1... 全局编号，一旦入库第二个文档，
    id 就会冲突（Chroma 的 id 必须唯一，重复 add 会报错）。
    用「文档名 + chunk 序号」保证不同文档之间永不冲突。
    """

    ids = [
        f"{id_prefix}_chunk_{i}"
        for i in range(len(documents))
    ]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )


def reset_collection():
    """
    删除并重建 collection。

    使用场景：文档清洗规则更新后，旧数据已经不符合新规则，
    必须「清库重灌」，否则代码和数据不一致
    （这正是之前 18 个旧 chunk 混在库里的原因）。
    """

    global collection

    client.delete_collection(name="knowledge_base")

    collection = client.get_or_create_collection(
        name="knowledge_base"
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

def delete_document_by_source(filename: str):
    """
    根据 source 元数据删除文档的所有 chunk
    """
    collection.delete(
        where={"source": filename}
    )