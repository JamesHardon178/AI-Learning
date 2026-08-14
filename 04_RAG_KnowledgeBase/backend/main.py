from fastapi import FastAPI

from services.rag_service import rag_query
from schemas.rag_schema import (
    RAGQueryRequest,
    RAGQueryResponse
)


app = FastAPI()


@app.get("/")
def root():
    return {"message": "RAG Knowledge Base API"}


@app.post(
    "/api/rag/query",
    response_model=RAGQueryResponse
)
def rag_query_api(request: RAGQueryRequest):
    result = rag_query(request.query)

    return result