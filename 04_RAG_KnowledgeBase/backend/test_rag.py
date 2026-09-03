from services.rag_service import rag_query


test_cases = [
    {
        "query": "在“启眸生翼”智能救援集成平台中，面向抗震救灾的软件系统核心逻辑层主要负责什么，封装了哪些算法模型？",
        "expected_chunks": [2]
    },
    {
        "query": "软件系统在发现疑似人体特征并触发报警前，需要满足什么判断条件？",
        "expected_chunks": [2]
    },
    {
        "query": "在项目日志管理系统中，不同角色的员工对“日报”的数据可见范围是如何划分的？",
        "expected_chunks": [1]
    },
    {
        "query": "忘记写日报或者历史草稿超过多少天之后无法直接编辑？补录机制是什么？",
        "expected_chunks": [5, 26]
    },
    {
        "query": "项目详情中的“毛利”是如何计算出来的？项目状态是否可以手动修改？",
        "expected_chunks": [13, 29, 30]
    }
]


for i, case in enumerate(test_cases, start=1):

    query = case["query"]
    expected_chunks = case["expected_chunks"]

    result = rag_query(query)

    print("\n" + "=" * 60)
    print(f"测试问题 {i}")
    print("=" * 60)

    print("\n===== 用户问题 =====")
    print(query)

    print("\n===== AI回答 =====")
    print(result["answer"])

    print("\n===== 检索来源 =====")

    retrieved_chunks = []

    for citation in result["citations"]:
        source = citation.get("source", "未知来源")
        chunk_index = citation.get("chunk_index", "未知")

        print(f"📄 {source}")
        print(f"📌 Chunk {chunk_index}")

        if chunk_index != "未知":
            retrieved_chunks.append(chunk_index)

    print("\n===== 评估 =====")

    hit_count = sum(
    chunk in retrieved_chunks
    for chunk in expected_chunks
    )
    recall = hit_count / len(expected_chunks)
    print(f"正确 Chunk：{expected_chunks}")
    print(f"检索 Chunk：{retrieved_chunks}")
    print(f"命中数量：{hit_count}")
    print(f"Recall@3：{recall:.2%}")
    precision= hit_count / len(retrieved_chunks) if retrieved_chunks else 0
    print(f"Precision@3：{precision:.2%}")

    if recall == 1:
        print("✅ 所有正确 Chunk 都被召回")
    else:
     print("⚠️ 有正确 Chunk 没有被召回")

    #  mrr计算
    mrr = 0
    for index, chunk in enumerate(retrieved_chunks):
        if chunk in expected_chunks:
            rank = index + 1
            mrr = 1 / rank
            break
    print(f"MRR@3：{mrr:.2%}")