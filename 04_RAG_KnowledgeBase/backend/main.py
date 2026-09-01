from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 导入HttpException类
from fastapi import HTTPException
import logging
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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)

@app.get("/")
def root():
    return {"message": "RAG Knowledge Base API"}


@app.post(
    "/api/rag/query",
    response_model=RAGQueryResponse
)
def rag_query_api(request: RAGQueryRequest):
    try:
        result=rag_query(request.query)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return result