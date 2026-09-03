from pydantic import BaseModel

class RAGQueryRequest(BaseModel):
    query: str


class Citation(BaseModel):
    source: str
    chunk_index: int


class RAGQueryResponse(BaseModel):
    answer: str
    citations: list[Citation]




class RAGMetrics(BaseModel):
    retrieval_count: int
    filtered_count: int
    citation_count: int
    embedding_latency: float
    retrieval_latency: float
    llm_latency: float
    total_latency: float
    input_tokens: int 
    output_tokens: int
    total_tokens: int