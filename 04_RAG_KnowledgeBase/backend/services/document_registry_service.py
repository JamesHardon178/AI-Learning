from pathlib import Path
import json
import hashlib
DOCUMENT_REGISTRY_PATH = Path("data/document_registry.json")


def calculate_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_document(filename: str) -> dict | None:
    documents = _load_registry()

    for doc in documents:
        if doc["filename"] == filename:
            return doc

    return None

def _load_registry() -> list[dict]:
    """
    读取注册表，统一返回「文档列表」。

    注册表 JSON 结构固定为：
        {"documents": [{"filename": "...", "chunk_count": N}, ...]}

    为什么用 dict 包一层而不是直接存 list：
    以后要加字段（如上传时间、文档类型）时，直接加顶层键，
    不用迁移数据结构。
    """
    try:
        with open(DOCUMENT_REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []

    documents = data.get("documents", []) if isinstance(data, dict) else data
    return documents


def _save_registry(documents: list[dict]):
    """
    把文档列表写回注册表，保持 {"documents": [...]} 结构。
    """
    with open(DOCUMENT_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"documents": documents},
            f,
            ensure_ascii=False,
            indent=4
        )


def add_document(filename: str, chunk_count: int,file_hash: str) -> dict:
    """
    将文档信息写入 document_registry.json。

    如果文件名已存在，抛 ValueError（调用方应转成 409/400）。
    """
    documents = _load_registry()

    for doc in documents:
        if doc["filename"] == filename:
            raise ValueError(f"文档 '{filename}' 已存在于注册表中。")

    document_info = {
        "filename": filename,
        "chunk_count": chunk_count,
        "file_hash": file_hash
    }
    documents.append(document_info)
    _save_registry(documents)
    return document_info

def update_document(filename: str, chunk_count: int,file_hash: str) -> dict:
    documents = _load_registry()

    for doc in documents:
        if doc["filename"] == filename:
            doc["chunk_count"] = chunk_count
            doc["file_hash"] = file_hash
            _save_registry(documents)
            return doc

    raise ValueError(
        f"文档 '{filename}' 不存在，无法更新。"
    )


def get_documents() -> list[dict]:
    """
    获取所有已注册的文档信息，返回文档列表（不是整个 dict）。
    """
    return _load_registry()


def remove_document(filename: str):
    """
    从 document_registry.json 中删除指定文档信息。

    如果不存在，抛 ValueError。
    """
    documents = _load_registry()

    if not any(doc["filename"] == filename for doc in documents):
        raise ValueError(f"文档 '{filename}' 不存在。")

    updated = [
        doc for doc in documents
        if doc["filename"] != filename
    ]
    _save_registry(updated)
