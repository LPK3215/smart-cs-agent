<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>🤖 智能客服</h1>
        <p>{{ isLogin ? '登录您的账户' : '注册新账户' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" required minlength="3" autocomplete="username" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" required minlength="6" autocomplete="current-password" />
        </div>
        <div v-if="!isLogin" class="form-group">
          <label>显示名称</label>
          <input v-model="displayName" type="text" placeholder="您的称呼（可选）" autocomplete="name" />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '处理中...' : isLogin ? '登录' : '注册' }}
        </button>
      </form>

      <div class="login-toggle">
        <span v-if="isLogin">
          还没有账户？<a @click="switchMode">立即注册</a>
        </span>
        <span v-else>
          已有账户？<a @click="switchMode">返回登录</a>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const displayName = ref('')
const loading = ref(false)
const errorMsg = ref('')

function switchMode() {
  isLogin.value = !isLogin.value
  errorMsg.value = ''
}

async function handleSubmit() {
  loading.value = true
  errorMsg.value = ''

  try {
    if (isLogin.value) {
      await authStore.login(username.value, password.value)
    } else {
      await authStore.register(username.value, password.value, displayName.value || username.value)
    }
    router.push('/chat')
  } catch (e: any) {
    errorMsg.value = e.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
}

.login-card {
  background: var(--card);
  border-radius: 16px;
  padding: 40px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 28px;
  color: var(--primary);
  margin-bottom: 8px;
}

.login-header p {
  color: var(--text-muted);
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}

.form-group input:focus {
  border-color: var(--primary);
}

.error-msg {
  padding: 8px 12px;
  background: #fef0f0;
  color: var(--danger);
  border-radius: 6px;
  font-size: 13px;
}

.submit-btn {
  padding: 12px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
  font-family: inherit;
}

.submit-btn:hover {
  background: var(--primary-light);
}

.submit-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.login-toggle {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: var(--text-muted);
}

.login-toggle a {
  color: var(--primary);
  cursor: pointer;
  font-weight: 500;
}

.login-toggle a:hover {
  text-decoration: underline;
}
</style>
