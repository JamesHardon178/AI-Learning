<script setup>
import { computed, nextTick, ref } from "vue"

const messages = ref([])
const input = ref("")
const isSending = ref(false)
const messagesEl = ref(null)

const canSend = computed(() => input.value.trim().length > 0 && !isSending.value)

async function scrollToBottom() {
  await nextTick()

  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

function decodeSsePayload(payload) {
  let content = payload

  for (let attempt = 0; attempt < 2; attempt += 1) {
    if (typeof content !== "string") {
      break
    }

    try {
      const decoded = JSON.parse(content)

      if (typeof decoded !== "string") {
        break
      }

      content = decoded
    } catch {
      break
    }
  }

  return content
}

function appendSseEvent(event, assistantMessage) {
  const payload = event
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => (line.startsWith("data: ") ? line.slice(6) : line.slice(5)))
    .join("\n")

  if (!payload || payload === "[DONE]") {
    return
  }

  const content = decodeSsePayload(payload)

  if (typeof content === "string") {
    assistantMessage.content += content
  }
}

async function sendMessage() {
  const message = input.value.trim()

  if (!message || isSending.value) {
    return
  }

  const assistantMessage = {
    role: "assistant",
    content: "",
    streaming: true
  }

  messages.value.push({
    role: "user",
    content: message
  })
  messages.value.push(assistantMessage)
  input.value = ""
  isSending.value = true
  await scrollToBottom()

  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id: "001",
        message
      })
    })

    if (!response.ok || !response.body) {
      throw new Error(`Request failed with status ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        buffer += decoder.decode()
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split(/\r?\n\r?\n/)
      buffer = events.pop() ?? ""

      for (const event of events) {
        appendSseEvent(event, assistantMessage)
      }

      await scrollToBottom()
    }

    if (buffer) {
      appendSseEvent(buffer, assistantMessage)
    }
  } catch (error) {
    console.error("Failed to send message:", error)

    if (!assistantMessage.content) {
      assistantMessage.content = "暂时无法连接服务，请确认后端已启动后重试。"
    }
  } finally {
    assistantMessage.streaming = false
    isSending.value = false
    await scrollToBottom()
  }
}
</script>

<template>
  <main class="chat-shell">
    <header class="chat-header">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">AI</div>
        <div>
          <p class="eyebrow">AI CHAT</p>
          <h1>智能对话助手</h1>
          <p class="subtitle">清晰表达你的问题，获得连续、自然的回答。</p>
        </div>
      </div>

      <div class="connection-status">
        <span class="status-dot" aria-hidden="true"></span>
        <span>在线</span>
      </div>
    </header>

    <section class="chat-panel" aria-label="聊天窗口">
      <div class="panel-bar">
        <div>
          <p class="panel-label">当前会话</p>
          <p class="panel-title">与 AI 助手对话</p>
        </div>
        <span class="session-badge">SESSION 001</span>
      </div>

      <div ref="messagesEl" class="messages" aria-live="polite">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon" aria-hidden="true">✦</div>
          <h2>有什么想了解的？</h2>
          <p>从一个问题开始，AI 会在这里回复你。</p>
        </div>

        <article
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-row', msg.role]"
        >
          <div class="avatar" aria-hidden="true">
            {{ msg.role === "user" ? "我" : "AI" }}
          </div>

          <div class="message-content">
            <div class="message-meta">
              <span>{{ msg.role === "user" ? "你" : "AI 助手" }}</span>
              <span v-if="msg.streaming" class="typing-label">正在输入</span>
            </div>
            <div class="message-bubble">
              <span v-if="!msg.content && msg.streaming" class="typing-dots" aria-label="正在生成">
                <i></i>
                <i></i>
                <i></i>
              </span>
              <span class="message-text">{{ msg.content }}</span>
              <span v-if="msg.streaming && msg.content" class="stream-cursor" aria-hidden="true"></span>
            </div>
          </div>
        </article>
      </div>

      <form class="composer" @submit.prevent="sendMessage">
        <textarea
          v-model="input"
          rows="1"
          placeholder="输入你的问题..."
          aria-label="输入问题"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>
        <button type="submit" :disabled="!canSend" :aria-label="isSending ? '正在生成' : '发送消息'">
          <span>{{ isSending ? "生成中" : "发送" }}</span>
          <span class="send-icon" aria-hidden="true">↑</span>
        </button>
      </form>
    </section>

    <p class="footer-note">AI 助手可能会产生不准确的信息，请结合实际情况判断。</p>
  </main>
</template>
