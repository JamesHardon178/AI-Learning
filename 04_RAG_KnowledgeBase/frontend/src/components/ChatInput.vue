<template>
  <form class="chat-input" @submit.prevent="submit">
    <el-input
      v-model="draft"
      class="chat-input__field"
      size="large"
      :placeholder="placeholder"
      clearable
      :disabled="disabled"
      @keyup.enter.prevent="submit"
    />
    <el-button
      class="chat-input__button"
      type="primary"
      size="large"
      :disabled="disabled || !draft.trim()"
      :loading="loading"
      @click="submit"
    >
      发送
    </el-button>
  </form>
  <p class="chat-input__hint">Enter 发送，输入框已锁定，避免重复提交。</p>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入你的问题...'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send'])

const draft = ref(props.modelValue)

watch(
  () => props.modelValue,
  (value) => {
    draft.value = value
  }
)

watch(draft, (value) => {
  emit('update:modelValue', value)
})

function submit() {
  const value = draft.value.trim()
  if (!value || props.disabled || props.loading) {
    return
  }

  emit('send', value)
}
</script>
