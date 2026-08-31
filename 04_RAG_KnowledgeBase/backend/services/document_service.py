import fitz
import re


# =========================
# 1. 判断是否为章节标题
# =========================

def is_section_title(line: str) -> bool:
    """
    判断一行文本是否为章节标题

    支持：
    3.1 我的日报
    3.2 团队日报
    第四章 AI 报告管理
    """

    line = line.strip()

    patterns = [
        r"^\d+\.\d+\s+.+$",                  # 3.1 我的日报
        r"^第[一二三四五六七八九十百]+章\s*.+$"  # 第四章 AI 报告管理
    ]

    return any(re.match(pattern, line) for pattern in patterns)


# =========================
# 2. 从 PDF 提取文本
# =========================

def extract_text_from_pdf(file_path: str) -> str:
    """
    从 PDF 中提取全部文本
    """

    document = fitz.open(file_path)

    texts = []

    for page in document:
        text = page.get_text()
        texts.append(text)

    document.close()

    return "\n".join(texts)


# =========================
# 3. 文本切分
# =========================

def chunk_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100
) -> list[str]:
    """
    按章节标题进行 Chunk 切分。

    规则：

    1. 遇到章节标题，开启新的 Chunk
    2. 尽量保证章节标题和正文在一起
    3. Chunk 超过 chunk_size 后进行切分
    4. 切分时保留 overlap
    """

    chunks = []

    # 按行拆分
    lines = text.splitlines()

    current_chunk = ""
    current_title = ""

    for line in lines:

        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # =========================
        # 遇到新的章节标题
        # =========================

        if is_section_title(line):

            # 如果之前已经存在 Chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # 保存当前章节标题
            current_title = line

            # 新 Chunk 从标题开始
            current_chunk = line

            continue

        # =========================
        # 普通正文
        # =========================

        if current_chunk:
            current_chunk += "\n" + line
        else:
            current_chunk = line

        # =========================
        # Chunk 超过指定大小
        # =========================

        if len(current_chunk) >= chunk_size:

            chunks.append(current_chunk.strip())

            # 取最后 overlap 个字符
            overlap_text = current_chunk[-overlap:]

            # 下一 Chunk 保留章节标题
            current_chunk = (
                current_title
                + "\n"
                + overlap_text
            )

    # =========================
    # 保存最后一个 Chunk
    # =========================

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


# =========================
# 4. 测试
# =========================

if __name__ == "__main__":

    # PDF 路径
    file_path = "../data/documents/项目日志管理系统-产品手册.pdf"

    # =========================
    # 提取 PDF
    # =========================

    text = extract_text_from_pdf(file_path)

    print("PDF 文本提取完成")
    print(f"文本长度：{len(text)}")

    # =========================
    # Chunk
    # =========================

    chunks = chunk_text(
        text,
        chunk_size=700,
        overlap=100
    )

    print(f"\nChunk 数量：{len(chunks)}")

    # =========================
    # 输出 Chunk
    # =========================

    for i, chunk in enumerate(chunks):

        print("\n" + "=" * 60)
        print(f"Chunk {i}")
        print("=" * 60)

        print(chunk)