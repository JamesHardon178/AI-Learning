from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from services.rag_service import rag_query
from schemas.rag_schema import (
    RAGQueryRequest,
    RAGQueryResponse
)
from services.document_service import prepare_document
from services.vector_service import add_documents, delete_document_by_source
from services.embedding_service import embed_text
from services.document_registry_service import (
    add_document,
    get_documents,
    remove_document,
    calculate_file_hash,
)
from logging_filter import RequestIdFilter

DOCUMENTS_DIR = Path("data/documents")

# 文本提取量下限：低于此值说明 PDF 是扫描版（无文本层），
# 入库只会产生一堆无意义的孤立标题 chunk。
MIN_TEXT_LENGTH = 2000

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - [request_id=%(request_id)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)


@app.get("/")
def root():
    return {"message": "RAG Knowledge Base API"}


@app.post("/api/rag/query", response_model=RAGQueryResponse)
def rag_query_api(request: RAGQueryRequest):
    try:
        result = rag_query(request.query)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return result


@app.post("/api/rag/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    # 1. 校验文件类型
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="仅支持 PDF 文件。"
        )

    # 2. 校验是否已存在
    if any(doc["filename"] == file.filename for doc in get_documents()):
        raise HTTPException(
            status_code=409,
            detail=f"文档 '{file.filename}' 已存在。"
        )

    # 3. 保存文件
    file_path = DOCUMENTS_DIR / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 4. 解析 + 切分 + 校验文本量（扫描版 PDF 会在这一步被拦截）
    try:
        chunks = prepare_document(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)  # 解析失败就删掉刚保存的文件
        raise HTTPException(status_code=422, detail=f"PDF 解析失败：{e}")

    if len(chunks) == 0 or len("".join(chunks)) < MIN_TEXT_LENGTH:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=(
                f"文档 '{file.filename}' 提取文本过少（{len(''.join(chunks))} 字符），"
                "可能是扫描版 PDF，无法用于知识库检索。"
            )
        )

    # 5. 向量化 + 入库
    embeddings = [embed_text(chunk) for chunk in chunks]
    metadatas = [
        {
            "source": file.filename,
            "chunk_index": i
        }
        for i in range(len(chunks))
    ]
    add_documents(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        id_prefix=file.filename
    )
    
    # 6. 登记
    file_hash = calculate_file_hash(str(file_path))
    add_document(
        filename=file.filename,
        chunk_count=len(chunks),
        file_hash=file_hash
    )

    return {
        "filename": file.filename,
        "chunk_count": len(chunks),
        "file_hash": file_hash,
        "message": "文档上传并入库成功"
    }


@app.get("/api/rag/documents")
async def list_documents():
    documents = get_documents()
    return {"documents": documents}


@app.delete("/api/rag/documents/{filename}")
async def delete_document(filename: str):
    documents = get_documents()

    if not any(doc["filename"] == filename for doc in documents):
        raise HTTPException(
            status_code=404,
            detail=f"文档 '{filename}' 不存在。"
        )

    try:
        # 1. 从向量库删除该文档的所有 chunk
        delete_document_by_source(filename)
        # 2. 从注册表删除
        remove_document(filename)
        # 3. 删除物理文件
        file_path = DOCUMENTS_DIR / filename
        if file_path.exists():
            file_path.unlink()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"message": f"文档 '{filename}' 已删除。"}
