from services.document_service import (
    extract_text_from_pdf,
    chunk_text
)


pdf_path = "data/documents/项目日志管理系统-产品手册.pdf"

text = extract_text_from_pdf(pdf_path)

chunks = chunk_text(text)

print("Chunk数量：", len(chunks))
for i, chunk in enumerate(chunks):
    print(f"\n===== Chunk {i} =====")
    print(chunk)



print("原始文本长度：", len(text))
print("Chunk数量：", len(chunks))

for i, chunk in enumerate(chunks[:3]):
    print(f"\n===== Chunk {i + 1} =====")
    print(chunk)