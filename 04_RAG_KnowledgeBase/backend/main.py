from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.rag_service import rag_query
from schemas.rag_schema import (
    RAGQueryRequest,
    RAGQueryResponse
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
