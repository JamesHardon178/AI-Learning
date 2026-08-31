<template>
  <article :class="['chat-message', `chat-message--${message.role}`]">
    <div class="chat-message__avatar">
      {{ message.role === 'user' ? '我' : 'AI' }}
    </div>
    <div class="chat-message__body">
      <div class="chat-message__meta">
        <span class="chat-message__role">{{ message.role === 'user' ? '用户' : 'AI 助手' }}</span>
        <span v-if="message.pending" class="chat-message__status">正在思考...</span>
      </div>
      <div class="chat-message__bubble">
        <div class="chat-message__text">{{ message.content }}</div>
      </div>
      <CitationList v-if="message.role === 'assistant' && !message.pending" :citations="message.citations" />
    </div>
  </article>
</template>

<script setup>
import CitationList from './CitationList.vue'

defineProps({
  message: {
    type: Object,
    required: true
  }
})
</script>
