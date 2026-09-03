import fitz
import re
from collections import Counter


# =========================
# 1. 噪声识别：判断一行是否为页眉/页码/目录
# =========================

# 页码行的样子：— 2 —  /  - 12 -
PAGE_NUMBER_PATTERN = re.compile(r"^[—–-]\s*\d+\s*[—–-]$")

# 章标题：第四章 AI 报告管理
CHAPTER_PATTERN = re.compile(r"^第[一二三四五六七八九十百]+章\s*.+$")

# 目录行的样子：1.1 系统简介............（一大串连续点号）
TOC_DOT_PATTERN = re.compile(r"\.{4,}")

# 需要整体丢弃的短行
DROP_EXACT_LINES = {"目录", "目录 ", "目 录"}


def detect_page_headers(
    lines: list[str],
    page_count: int,
    min_count: int = 8,
    min_len: int = 6,
    max_ratio: float = 1.5
) -> set[str]:
    """
    自动识别页眉行。

    原理：页眉在每一页的相同位置重复出现，出现次数接近 PDF 页数。
    所以统计每一行的出现次数，把「出现次数 ≈ 页数」的行判定为页眉。

    两个关键约束：

    1. 出现次数不能太少（>= min(8, 页数)）：
       太少说明不是「每页都有」，不具备页眉特征。

    2. 出现次数不能太多（<= 页数 * 1.5）：
       这是防误伤的护栏。如果某行出现次数远大于页数
       （比如每页出现 30 次），说明它是正文里的重复内容
       （如产品宣传语、测试填充文本），不是页眉。
       页眉每页只出现 1 次，最多偶尔跳页，不会超过 1.5 倍页数。

    为什么要求 min_len：
    「字段」「说明」「操作」这类短行是表格列头，也会重复出现，
    但它们是正文内容，不能删。页眉一般是一句完整的长标题。
    """

    counter = Counter(line.strip() for line in lines if line.strip())

    # 出现次数的合理下限：页眉应该「几乎每页都有」，
    # 所以下限取 min(8, 页数)，页数很少时放宽到页数本身。
    lower_bound = min(min_count, max(3, page_count))

    # 出现次数的合理上限：页眉每页最多出现 1 次，
    # 超过 页数 * 1.5 说明是正文重复，不是页眉。
    upper_bound = page_count * max_ratio

    headers = {
        line
        for line, count in counter.items()
        if lower_bound <= count <= upper_bound
        and len(line) >= min_len
    }

    return headers


def clean_lines(lines: list[str], page_count: int = 1) -> list[str]:
    """
    清洗 PDF 提取出的原始文本行，去掉四类噪声：

    1. 页码行（— 2 —）
    2. 页眉行（项目日志管理系统·产品手册，每页重复）
    3. 目录行（带一长串点号的行）
    4. 孤立的「目录」标题行

    为什么要在「行」级别清洗而不是整段删：
    fitz 提取 PDF 时，页眉/页码/正文混在同一个字符串流里，
    只有逐行判断才能精确剔除，且不影响正文。
    """

    headers = detect_page_headers(lines, page_count=page_count)

    cleaned = []

    for line in lines:

        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # 1. 页码行
        if PAGE_NUMBER_PATTERN.match(line):
            continue

        # 2. 页眉行
        if line in headers:
            continue

        # 3. 目录行（连续 4 个以上点号）
        if TOC_DOT_PATTERN.search(line):
            continue

        # 4. 孤立的「目录」标题
        if line in DROP_EXACT_LINES:
            continue

        cleaned.append(line)

    return cleaned


# =========================
# 2. 判断是否为章节标题
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
        r"^\d+\.\d+\s*.+$",                   # 3.1 我的日报
        r"^第[一二三四五六七八九十百]+章\s*.+$"   # 第四章 AI 报告管理
    ]

    return any(re.match(pattern, line) for pattern in patterns)


def get_section_title(chunk: str) -> str:
    """
    从 chunk 内容推断它属于哪个章节。

    chunk_text 切分时会把章节标题放在 chunk 的第一行，
    所以只需要检查第一行；如果第一行不是标题（说明是同章节
    的延续 chunk），则返回「未知」，由调用方决定如何标注。
    """

    first_line = chunk.splitlines()[0].strip() if chunk else ""

    if is_section_title(first_line):
        return first_line

    return ""


def is_faq_question(line: str) -> bool:
    """
    判断一行是否为 FAQ 问题，例如：
    Q1：忘记写日报怎么办？
    Q2：AI 报告生成需要多久？失败了怎么办？
    """
    return bool(re.match(r"^Q\d+[：:]", line.strip()))

# =========================
# 3. 从 PDF 提取文本（原始 + 清洗后）
# =========================

def extract_text_from_pdf(file_path: str, clean: bool = True) -> str:
    """
    从 PDF 中提取全部文本。

    clean=True 时（默认）返回清洗后的文本；
    clean=False 返回原始文本，用于对比和调试。
    """

    document = fitz.open(file_path)

    texts = []
    page_count = len(document)

    for page in document:
        text = page.get_text()
        texts.append(text)

    document.close()

    raw = "\n".join(texts)

    if not clean:
        return raw

    # 先按行拆开，逐行清洗，再拼回去
    cleaned_lines = clean_lines(raw.splitlines(), page_count=page_count)

    return "\n".join(cleaned_lines)


# =========================
# 4. 文本切分
# =========================

def chunk_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100
) -> list[str]:
    """
    按章节标题进行 Chunk 切分。

    规则：

    1. 遇到小节标题（X.Y），开启新的 Chunk
    2. 章标题（第X章）不单独成块，而是拼到它下面第一个
       小节/正文的前面 —— 避免产生「第一章系统概述」这种
       只有几个字的废 chunk
    3. Chunk 超过 chunk_size 后进行切分
    4. 切分时保留 overlap，并重复章/节标题保持上下文
    """

    chunks = []

    # 按行拆分
    lines = text.splitlines()

    current_chunk = ""
    current_title = ""

    # 章标题前缀：遇到「第X章」先记下来，等下一行决定拼给谁
    chapter_prefix = ""

    for line in lines:

        line = line.strip()

        # 跳过空行
        if not line:
            continue
        if is_faq_question(line):

            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            if chapter_prefix:
                current_chunk = chapter_prefix + "\n" + line
                chapter_prefix = ""
            else:
                current_chunk = line

            current_title = line

            continue

        # =========================
        # 章标题：不单独成块，先记下来
        # =========================

        if CHAPTER_PATTERN.match(line):

            # 如果之前已经存在 Chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            chapter_prefix = line
            current_title = line
            current_chunk = ""

            continue

        # =========================
        # 小节标题：开启新的 Chunk
        # =========================

        if is_section_title(line):

            # 如果之前已经存在 Chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # 新 Chunk 的开头 = 章标题（如果有）+ 小节标题
            if chapter_prefix:
                current_title = chapter_prefix + "\n" + line
                chapter_prefix = ""      # 章前缀只能使用一次
            else:
                current_title = line

            current_chunk = current_title

            continue

        # =========================
        # 普通正文
        # =========================

        # 正文如果直接跟在章标题后面（章有简介的情况），
        # 同样要把章标题拼进去
        if chapter_prefix:
            current_chunk = chapter_prefix + "\n" + line
            chapter_prefix = ""
        elif current_chunk:
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
# 5. 一键完成：提取 -> 清洗 -> 切分
# =========================

def prepare_document(file_path: str) -> list[str]:
    """
    完整的文档预处理管道：提取 -> 清洗 -> 切分。

    入库脚本只需要调用这一个函数。
    """

    text = extract_text_from_pdf(file_path, clean=True)

    return chunk_text(text)


# =========================
# 6. 测试
# =========================

if __name__ == "__main__":

    # PDF 路径
    file_path = "data/documents/项目日志管理系统-产品手册.pdf"

    # =========================
    # 对比：清洗前 vs 清洗后
    # =========================

    raw_text = extract_text_from_pdf(file_path, clean=False)
    clean_text = extract_text_from_pdf(file_path, clean=True)

    print("PDF 文本提取完成")
    print(f"清洗前字符数：{len(raw_text)}")
    print(f"清洗后字符数：{len(clean_text)}")
    print(f"去除噪声字符数：{len(raw_text) - len(clean_text)}")

    # =========================
    # Chunk
    # =========================

    chunks = chunk_text(clean_text, chunk_size=700, overlap=100)

    print(f"\nChunk 数量：{len(chunks)}")

    # =========================
    # 输出 Chunk
    # =========================

    for i, chunk in enumerate(chunks):

        print("\n" + "=" * 60)
        print(f"Chunk {i}")
        print("=" * 60)

        print(chunk)
