from services.embedding_service import embed_text


text = "员工每年享有10天带薪休假"

vector = embed_text(text)

print("向量维度：", len(vector))
print("前10个值：", vector[:10])