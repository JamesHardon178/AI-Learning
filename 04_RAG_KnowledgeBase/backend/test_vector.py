from services.document_service import (
    extract_text_from_pdf,
    chunk_text
)

from services.embedding_service import embed_text

from services.vector_service import add_documents


pdf_path = "data/documents/项目日志管理系统-产品手册.pdf"


# 1. PDF → Text
text = extract_text_from_pdf(pdf_path)


# 2. Text → Chunks
chunks = chunk_text(text)


# 3. Chunk → Embedding
embeddings = []

for chunk in chunks:
    vector = embed_text(chunk)
    embeddings.append(vector)


# 4. 写入 Chroma
metadatas = [
    {
        "source": "项目日志管理系统-产品手册.pdf",
        "chunk_index": i
    }
    for i in range(len(chunks))
]


add_documents(
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadatas
)


print("知识库入库完成")
print("Chunk数量：", len(chunks))