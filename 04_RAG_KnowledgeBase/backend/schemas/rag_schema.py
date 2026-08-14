from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str


class Citation(BaseModel):
    source: str
    chunk_index: int


class RAGQueryResponse(BaseModel):
    answer: str
    citations: list[Citation]