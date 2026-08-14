import fitz
import re

def is_section_title(line: str) -> bool:
    pattern = r"^\d+\.\d+\s+.+$"
    return bool(re.match(pattern, line.strip()))

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


def chunk_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100
) -> list[str]:
    """
    将文本切分成多个 Chunk
    """

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

if __name__ == "__main__":
    test_lines = [
        "3.1 我的日报",
        "3.2 团队日报",
        "第四章AI 报告管理",
        "我的日报列表",
        "写一份新日报"
    ]

    for line in test_lines:
        print(line, "=>", is_section_title(line))