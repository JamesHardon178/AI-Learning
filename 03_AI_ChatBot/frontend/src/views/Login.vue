<script setup>
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { API_BASE_URL, setToken } from "../utils/auth"

const router = useRouter()
const route = useRoute()

const username = ref("")
const password = ref("")
const errorMessage = ref("")
const isLoading = ref(false)

function getRedirectPath() {
  const redirect = route.query.redirect

  if (
    typeof redirect === "string" &&
    redirect.startsWith("/") &&
    redirect !== "/login"
  ) {
    return redirect
  }

  return "/chat"
}

async function login() {
  if (!username.value.trim() || !password.value) {
    errorMessage.value = "请输入用户名和密码。"
    return
  }

  errorMessage.value = ""
  isLoading.value = true

  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value
      })
    })

    let data = {}

    try {
      data = await response.json()
    } catch {
      data = {}
    }

    if (!response.ok) {
      throw new Error(data.detail || "用户名或密码错误。")
    }

    if (!data.access_token) {
      throw new Error("登录响应中缺少 access_token。")
    }

    setToken(data.access_token)
    await router.replace(getRedirectPath())
  } catch (error) {
    console.error("Login failed:", error)
    errorMessage.value =
      error instanceof Error ? error.message : "登录失败，请稍后重试。"
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-brand" aria-hidden="true">AI</div>
      <p class="login-eyebrow">AI CHAT</p>
      <h1 id="login-title">登录 AI 对话助手</h1>
      <p class="login-subtitle">登录后开始你的智能对话。</p>

      <form class="login-form" @submit.prevent="login">
        <label for="username">用户名</label>
        <input
          id="username"
          v-model="username"
          type="text"
          name="username"
          autocomplete="username"
          placeholder="请输入用户名"
          required
        />

        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          name="password"
          autocomplete="current-password"
          placeholder="请输入密码"
          required
        />

        <p v-if="errorMessage" class="login-error" role="alert">
          {{ errorMessage }}
        </p>

        <button type="submit" :disabled="isLoading">
          {{ isLoading ? "登录中..." : "登录" }}
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background:
    radial-gradient(circle at top left, rgba(47, 109, 246, 0.12), transparent 34%),
    #edf2f7;
}

.login-panel {
  width: min(100%, 420px);
  padding: 38px;
  border: 1px solid #dce5ee;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 18px 45px rgba(46, 67, 94, 0.11);
}

.login-brand {
  display: grid;
  width: 52px;
  height: 52px;
  margin-bottom: 20px;
  place-items: center;
  border-radius: 15px;
  color: #ffffff;
  background: #2f6df6;
  box-shadow: 0 10px 20px rgba(47, 109, 246, 0.22);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.login-eyebrow {
  margin: 0 0 6px;
  color: #718096;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.3px;
}

h1 {
  margin: 0;
  color: #172033;
  font-size: 28px;
  line-height: 1.25;
}

.login-subtitle {
  margin: 10px 0 28px;
  color: #718096;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.login-form label {
  margin-top: 7px;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}

.login-form input {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  border: 1px solid #dce5ee;
  border-radius: 8px;
  outline: 0;
  color: #26334a;
  background: #f8fafc;
  font-size: 14px;
}

.login-form input:focus {
  border-color: #8db0ff;
  box-shadow: 0 0 0 4px rgba(47, 109, 246, 0.1);
}

.login-form button {
  width: 100%;
  height: 44px;
  margin-top: 17px;
  border: 0;
  border-radius: 8px;
  color: #ffffff;
  background: #2f6df6;
  font-size: 14px;
  font-weight: 800;
}

.login-form button:hover:not(:disabled) {
  background: #245bd4;
}

.login-form button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.login-error {
  margin: 9px 0 0;
  color: #c24141;
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 480px) {
  .login-page {
    padding: 16px;
  }

  .login-panel {
    padding: 28px 22px;
  }
}
</style>
