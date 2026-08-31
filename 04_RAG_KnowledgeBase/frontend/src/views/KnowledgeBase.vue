<template>
  <div class="knowledge-base">
    <aside class="knowledge-base__sidebar">
      <div>
        <p class="knowledge-base__eyebrow">Enterprise RAG Demo</p>
        <h1 class="knowledge-base__title">企业知识库智能助手</h1>
        <p class="knowledge-base__description">
          连接 FastAPI RAG 服务，展示企业知识库问答、引用来源和加载状态。
        </p>
      </div>

      <div class="knowledge-base__panel">
        <div class="knowledge-base__panel-title">技术栈</div>
        <div class="knowledge-base__chips">
          <el-tag effect="dark">Vue 3</el-tag>
          <el-tag effect="dark">Vite</el-tag>
          <el-tag effect="dark">Element Plus</el-tag>
          <el-tag effect="dark">Axios</el-tag>
        </div>
      </div>

      <div class="knowledge-base__panel">
        <div class="knowledge-base__panel-title">接口</div>
        <code class="knowledge-base__code">POST http://127.0.0.1:8000/api/rag/query</code>
      </div>
    </aside>

    <main class="knowledge-base__main">
      <header class="knowledge-base__header">
        <div>
          <p class="knowledge-base__header-label">对话区域</p>
          <h2>企业知识库智能问答</h2>
        </div>
        <el-tag type="success" effect="light">前端已就绪</el-tag>
      </header>

      <section ref="conversationRef" class="knowledge-base__conversation">
        <div v-if="messages.length === 0" class="knowledge-base__empty">
          <p class="knowledge-base__empty-title">欢迎使用企业知识库助手</p>
          <p class="knowledge-base__empty-text">你可以直接问：</p>
          <div class="knowledge-base__suggestions">
            <el-button
              v-for="question in suggestions"
              :key="question"
              class="knowledge-base__suggestion"
              plain
              @click="useSuggestion(question)"
            >
              {{ question }}
            </el-button>
          </div>
        </div>

        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
        />
      </section>

      <footer class="knowledge-base__footer">
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          :closable="false"
          show-icon
          class="knowledge-base__alert"
        />
        <ChatInput
          v-model="draft"
          :disabled="loading"
          :loading="loading"
          placeholder="请输入你的问题..."
          @send="sendQuestion"
        />
      </footer>
    </main>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import ChatInput from '../components/ChatInput.vue'
import ChatMessage from '../components/ChatMessage.vue'
import { queryRAG } from '../api/rag'

const suggestions = [
  '怎么修改日报？',
  '我的日报在哪里查看？',
  'AI 报告怎么生成？',
  '忘记写日报怎么办？'
]

const draft = ref('')
const loading = ref(false)
const errorMessage = ref('')
const messages = ref([])
const conversationRef = ref(null)

function createId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function scrollToBottom() {
  nextTick(() => {
    const el = conversationRef.value
    if (!el) {
      return
    }

    el.scrollTop = el.scrollHeight
  })
}

function normalizeCitations(citations) {
  if (!Array.isArray(citations)) {
    return []
  }

  return citations.map((citation) => ({
    source: citation?.source || '未知来源',
    chunk_index: citation?.chunk_index ?? 0
  }))
}

function replacePendingAssistantMessage(message) {
  const index = messages.value.findIndex((item) => item.id === message.id)
  if (index !== -1) {
    messages.value.splice(index, 1, message)
  }
}

async function sendQuestion(question) {
  if (loading.value) {
    return
  }

  errorMessage.value = ''
  draft.value = ''

  const userMessage = {
    id: createId('user'),
    role: 'user',
    content: question
  }

  const pendingMessage = {
    id: createId('assistant'),
    role: 'assistant',
    content: '正在思考...',
    citations: [],
    pending: true
  }

  messages.value.push(userMessage, pendingMessage)
  loading.value = true
  scrollToBottom()

  try {
    const { data } = await queryRAG(question)
    replacePendingAssistantMessage({
      ...pendingMessage,
      content: data?.answer || '知识库中没有返回可用答案。',
      citations: normalizeCitations(data?.citations),
      pending: false
    })
  } catch (error) {
    console.error('RAG request failed:', error)
    errorMessage.value = '抱歉，知识库服务暂时不可用，请稍后重试。'
    replacePendingAssistantMessage({
      ...pendingMessage,
      content: '抱歉，知识库服务暂时不可用，请稍后重试。',
      citations: [],
      pending: false,
      error: true
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function useSuggestion(question) {
  draft.value = question
  sendQuestion(question)
}
</script>
