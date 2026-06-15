<template>
  <div class="app-container">
    <!-- Mobile overlay -->
    <div v-if="sidebarOpen" class="mobile-overlay" @click="sidebarOpen = false"></div>

    <!-- Sidebar -->
    <div class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <div class="sidebar-header">
        <h2>🤖 智能客服</h2>
        <p>ReAct Agent + SSE 流式</p>
      </div>

      <div class="sidebar-nav">
        <router-link to="/chat" class="nav-item" :class="{ active: route.path === '/chat' }" @click="closeOnMobile">
          <span class="icon">💬</span><span>对话</span>
          <span v-if="chatStore.activeSessionCount" class="nav-badge">{{ chatStore.activeSessionCount }}</span>
        </router-link>
        <router-link v-if="authStore.isAdmin" to="/admin" class="nav-item" :class="{ active: route.path === '/admin' }" @click="closeOnMobile">
          <span class="icon">📊</span><span>管理后台</span>
        </router-link>
        <router-link to="/profile" class="nav-item" :class="{ active: route.path === '/profile' }" @click="closeOnMobile">
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
      <!-- Mobile hamburger -->
      <button class="mobile-menu-btn" @click="sidebarOpen = !sidebarOpen">
        <span class="hamburger" :class="{ open: sidebarOpen }"></span>
      </button>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const sidebarOpen = ref(false)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function closeOnMobile() {
  if (window.innerWidth <= 768) {
    sidebarOpen.value = false
  }
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

/* Mobile menu button - hidden on desktop */
.mobile-menu-btn {
  display: none;
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 100;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  background: var(--card);
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.hamburger {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--text);
  position: relative;
  transition: background 0.2s;
}
.hamburger::before,
.hamburger::after {
  content: '';
  position: absolute;
  left: 0;
  width: 18px;
  height: 2px;
  background: var(--text);
  transition: transform 0.2s;
}
.hamburger::before { top: -6px; }
.hamburger::after { top: 6px; }

.hamburger.open { background: transparent; }
.hamburger.open::before { transform: rotate(45deg); top: 0; }
.hamburger.open::after { transform: rotate(-45deg); top: 0; }

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 998;
}

@media (max-width: 768px) {
  .mobile-menu-btn { display: flex; }
  .mobile-overlay { display: block; }

  .sidebar {
    position: fixed;
    left: -280px;
    top: 0;
    bottom: 0;
    z-index: 999;
    transition: left 0.3s ease;
  }
  .sidebar.sidebar-open {
    left: 0;
  }
}
</style>
