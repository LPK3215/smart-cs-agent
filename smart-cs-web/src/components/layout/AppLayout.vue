<template>
  <div class="app-container">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>🤖 智能客服</h2>
        <p>ReAct Agent + SSE 流式</p>
      </div>

      <div class="sidebar-nav">
        <router-link to="/chat" class="nav-item" :class="{ active: route.path === '/chat' }">
          <span class="icon">💬</span><span>对话</span>
          <span v-if="chatStore.activeSessionCount" class="nav-badge">{{ chatStore.activeSessionCount }}</span>
        </router-link>
        <router-link v-if="authStore.isAdmin" to="/admin" class="nav-item" :class="{ active: route.path === '/admin' }">
          <span class="icon">📊</span><span>管理后台</span>
        </router-link>
        <router-link to="/profile" class="nav-item" :class="{ active: route.path === '/profile' }">
          <span class="icon">👤</span><span>个人中心</span>
        </router-link>
      </div>

      <div class="sidebar-user" v-if="authStore.user">
        <div class="user-avatar">{{ authStore.user.displayName?.[0] || authStore.user.username[0] }}</div>
        <div class="user-info">
          <div class="user-name">{{ authStore.user.displayName || authStore.user.username }}</div>
          <div class="user-role">{{ authStore.isAdmin ? '管理员' : '用户' }}</div>
        </div>
        <button class="logout-btn" @click="handleLogout" title="退出登录">⏻</button>
      </div>

      <div class="sidebar-footer">
        LangChain ReAct Agent<br>DeepSeek + SSE Streaming
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-area">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin: 8px;
  background: var(--primary-bg);
  border-radius: var(--radius);
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-role { font-size: 11px; color: var(--text-muted); }
.logout-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-muted);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}
.logout-btn:hover { background: var(--border-light); color: var(--danger); }
</style>
