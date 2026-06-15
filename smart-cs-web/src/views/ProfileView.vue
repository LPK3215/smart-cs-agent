<template>
  <div class="profile-page">
    <div class="profile-header">
      <h2>👤 个人中心</h2>
      <p>账户信息与使用统计</p>
    </div>

    <!-- User Info -->
    <div class="profile-card">
      <h3>账户信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">用户名</span>
          <span class="info-value">{{ authStore.user?.username || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">显示名称</span>
          <span class="info-value">{{ authStore.user?.displayName || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">角色</span>
          <span class="info-value">
            <span class="role-tag" :class="authStore.isAdmin ? 'admin' : 'user'">
              {{ authStore.isAdmin ? '管理员' : '普通用户' }}
            </span>
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ authStore.user?.createdAt ? new Date(authStore.user.createdAt).toLocaleDateString('zh-CN') : '-' }}</span>
        </div>
      </div>
    </div>

    <!-- Usage Statistics (from backend profile) -->
    <div class="profile-card" v-if="profile">
      <h3>使用统计</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ profile.total_sessions || 0 }}</div>
          <div class="stat-label">总会话数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ profile.transfer_count || 0 }}</div>
          <div class="stat-label">转人工次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ profile.avg_rating ? profile.avg_rating.toFixed(1) : '-' }}</div>
          <div class="stat-label">平均评分</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ ((profile.transfer_rate || 0) * 100).toFixed(0) }}%</div>
          <div class="stat-label">转人工率</div>
        </div>
      </div>

      <!-- Top intents -->
      <div v-if="profile.top_intents && Object.keys(profile.top_intents).length > 0" style="margin-top: 16px">
        <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px">常见问题类型</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap">
          <span v-for="(count, intent) in profile.top_intents" :key="intent" class="intent-badge" :class="'intent-' + intent">
            {{ intentLabel(intent as string) }} ×{{ count }}
          </span>
        </div>
      </div>
    </div>

    <!-- Account Actions -->
    <div class="profile-card">
      <h3>账户操作</h3>
      <button class="action-btn danger" @click="handleLogout">退出登录</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { intentLabel } from '@/utils/format'
import * as api from '@/utils/api'

const router = useRouter()
const authStore = useAuthStore()
const profile = ref<any>(null)

onMounted(async () => {
  try {
    const data = await api.getMe()
    profile.value = data.profile
  } catch {
    // Profile may not exist yet
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.profile-page {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-width: 800px;
}

.profile-header { margin-bottom: 20px; }
.profile-header h2 { font-size: 20px; font-weight: 600; }
.profile-header p { color: var(--text-muted); font-size: 13px; margin-top: 4px; }

.profile-card {
  background: var(--card);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.profile-card h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label { font-size: 12px; color: var(--text-muted); }
.info-value { font-size: 14px; font-weight: 500; }

.role-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}
.role-tag.admin { background: #fef0f0; color: var(--danger); }
.role-tag.user { background: var(--primary-bg); color: var(--primary); }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value { font-size: 24px; font-weight: 700; color: var(--primary); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.action-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  font-family: inherit;
}

.action-btn.danger:hover {
  border-color: var(--danger);
  color: var(--danger);
  background: #fef0f0;
}
</style>
