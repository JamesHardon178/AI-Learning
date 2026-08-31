import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_RAG_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 60000
})

export function queryRAG(question) {
  return request.post('/api/rag/query', {
    query: question
  })
}

export { request }
