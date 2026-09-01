"""
知识库入库脚本

作用：把 data/documents/ 下的 PDF 清洗、切分、向量化后写入 Chroma。

什么时候要跑它：
1. 新增 / 修改了知识库文档
2. 修改了清洗规则或切分规则（document_service.py）
3. 更换了 Embedding 模型

用法（在 backend 目录下）：
    python ingest.py            # 清库重灌所有文档
    python ingest.py --dry-run  # 只预览切分结果，不写库
"""

import os
import sys
import time

from services.document_service import (
    extract_text_from_pdf,
    prepare_document,
    get_section_title
)
from services.embedding_service import embed_text
from services import vector_service


DOCUMENTS_DIR = "data/documents"


def ingest_all(dry_run: bool = False):
    """
    遍历文档目录，完成「提取 -> 清洗 -> 切分 -> 向量化 -> 入库」全流程。

    dry_run=True 时只打印切分结果，不真正写库。
    用途：改完清洗规则先 dry-run 检查 chunk 质量，确认没问题再入库。
    """

    pdf_files = [
        f for f in os.listdir(DOCUMENTS_DIR)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"目录 {DOCUMENTS_DIR} 下没有找到 PDF 文件")
        return

    # =========================
    # 第一步：清库（非 dry-run 时）
    # =========================

    if not dry_run:
        print("清空旧 collection ...")
        vector_service.reset_collection()

    total_chunks = 0

    for file_name in pdf_files:

        file_path = os.path.join(DOCUMENTS_DIR, file_name)

        print(f"\n===== 处理文档：{file_name} =====")

        # =========================
        # 第二步：提取 + 清洗 + 切分
        # =========================

        chunks = prepare_document(file_path)

        raw_text = extract_text_from_pdf(file_path, clean=False)
        clean_text = extract_text_from_pdf(file_path, clean=True)

        print(f"清洗前 {len(raw_text)} 字符 -> 清洗后 {len(clean_text)} 字符"
              f"（去除噪声 {len(raw_text) - len(clean_text)} 字符）")
        print(f"切分出 {len(chunks)} 个 chunk")

        if dry_run:
            for i, chunk in enumerate(chunks):
                section = get_section_title(chunk) or "(延续块)"
                preview = chunk.replace("\n", " ")[:50]
                print(f"  [{i:02d}] {section[:24]:<24} | {preview}")
            total_chunks += len(chunks)
            continue

        # =========================
        # 第三步：逐 chunk 向量化
        # =========================

        embeddings = []

        for i, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            embeddings.append(embedding)

            if (i + 1) % 10 == 0:
                print(f"  已向量化 {i + 1}/{len(chunks)}")

        print(f"  向量化完成：{len(embeddings)} 个向量")

        # =========================
        # 第四步：构造 metadata 并入库
        # =========================

        # id 前缀：文件名去掉 .pdf 后缀，保证不同文档 id 不冲突
        doc_id = os.path.splitext(file_name)[0]

        metadatas = [
            {
                "source": file_name,
                "chunk_index": i,
                "section": get_section_title(chunk) or "未知章节",
                "char_count": len(chunk)
            }
            for i, chunk in enumerate(chunks)
        ]

        vector_service.add_documents(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            id_prefix=doc_id
        )

        print(f"  入库完成：{len(chunks)} 条")

        total_chunks += len(chunks)

    # =========================
    # 汇总
    # =========================

    mode = "[预览模式]" if dry_run else ""

    print(f"\n{mode} 全部文档处理完成，共 {total_chunks} 个 chunk")

    if not dry_run:
        count = vector_service.collection.count()
        print(f"Chroma 当前库存量：{count}")

        # 入库后自检：找几个知识库内的问题试试检索
        print("\n===== 入库自检 =====")
        from services.rag_service import retrieve_documents

        check_questions = [
            "系统有哪些用户角色？",
            "忘记写日报了怎么办？",
        ]

        for question in check_questions:
            docs, metas = retrieve_documents(question)
            if docs:
                section = metas[0].get("section", "?")
                preview = docs[0].replace("\n", " ")[:40]
                print(f"  [OK] {question} -> {section} | {preview}")
            else:
                print(f"  [MISS] {question} -> 无命中，需要检查！")


if __name__ == "__main__":

    start = time.time()

    dry_run = "--dry-run" in sys.argv

    ingest_all(dry_run=dry_run)

    print(f"\n总耗时：{time.time() - start:.1f} 秒")
