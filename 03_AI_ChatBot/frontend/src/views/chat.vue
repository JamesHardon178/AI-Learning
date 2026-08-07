<script setup>
import { ref } from "vue"

const messages = ref([])

const input = ref("")


async function sendMessage() {

  if (!input.value.trim()) {
    return
  }


  // 保存用户消息
  messages.value.push({
    role: "user",
    content: input.value
  })


  // 创建AI占位消息
  messages.value.push({
    role: "assistant",
    content: ""
  })


  const message = input.value

  input.value = ""


  const response = await fetch(
    "http://127.0.0.1:8000/chat",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id: "001",
        message: message
      })
    }
  )


  const reader = response.body.getReader()

  const decoder = new TextDecoder()


  while (true) {

    const {
      done,
      value
    } = await reader.read()


    if (done) {
      break
    }


    const chunk = decoder.decode(value)


    // 追加AI回复
    messages.value[
      messages.value.length - 1
    ].content += chunk

  }

}

</script>


<template>

<div class="chat">

  <div class="messages">

    <div
      v-for="(msg,index) in messages"
      :key="index"
      class="message"
    >

      <b>{{msg.role}}:</b>

      {{msg.content}}

    </div>

  </div>


  <input
    v-model="input"
    @keyup.enter="sendMessage"
    placeholder="输入问题"
  />


  <button @click="sendMessage">
    发送
  </button>


</div>

</template>


<style scoped>

.chat {
  width: 600px;
  margin: 40px auto;
}


.messages {
  min-height: 400px;
  border: 1px solid #ddd;
  padding: 20px;
  margin-bottom: 20px;
}


.message {
  margin-bottom: 15px;
}


input {
  width: 80%;
  padding: 10px;
}


button {
  padding: 10px 20px;
}

</style>