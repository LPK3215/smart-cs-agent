<template>
  <div class="profile-page" v-loading="isLoading">
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
            <el-tag :type="authStore.isAdmin ? 'danger' : 'primary'" size="small" round>
              {{ authStore.isAdmin ? '管理员' : '普通用户' }}
            </el-tag>
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ authStore.user?.createdAt ? new Date(authStore.user.createdAt).toLocaleDateString('zh-CN') : '-' }}</span>
        </div>
      </div>
    </div>

    <!-- Usage Statistics -->
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
      <div v-if="profile.top_intents && Object.keys(profile.top_intents).length > 0" style="margin-top: 16px;">
        <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px;">常见问题类型</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <el-tag
            v-for="(count, intent) in profile.top_intents"
            :key="intent"
            :type="intentTagType(intent as string)"
            size="small"
          >
            {{ intentLabel(intent as string) }} ×{{ count }}
          </el-tag>
        </div>
      </div>

      <!-- Last active -->
      <div v-if="profile.last_active" style="margin-top: 12px; font-size: 12px; color: var(--text-muted);">
        最近活跃：{{ formatTime(profile.last_active) }}
      </div>
    </div>

    <!-- Memories Timeline -->
    <div class="profile-card" v-if="memories && memories.length > 0">
      <h3>跨会话记忆</h3>
      <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 16px;">
        Agent 从对话中自动提取的长期记忆，用于个性化后续交互
      </p>
      <div class="memory-timeline">
        <div v-for="mem in memories" :key="mem.id" class="memory-item">
          <div class="memory-meta">
            <el-tag size="small" :type="categoryType(mem.category)" effect="plain">{{ categoryLabel(mem.category) }}</el-tag>
            <span class="memory-time">{{ formatTime(mem.created_at) }}</span>
          </div>
          <div class="memory-content">{{ mem.content }}</div>
        </div>
      </div>
    </div>
    <div class="profile-card" v-else-if="!isLoading">
      <h3>跨会话记忆</h3>
      <div style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 13px;">
        暂无记忆数据 — 关闭会话后 Agent 会自动提取关键信息
      </div>
    </div>

    <!-- Account Actions -->
    <div class="profile-card">
      <h3>账户操作</h3>
      <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { intentLabel, formatTime } from '@/utils/format'
import * as api from '@/utils/api'
import type { UserProfile } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const isLoading = ref(false)
const profile = ref<UserProfile['profile']>(null)
const memories = ref<UserProfile['memories']>([])

onMounted(async () => {
  isLoading.value = true
  try {
    const data = await api.getMe()
    profile.value = data.profile
    memories.value = data.memories || []
  } catch {
    // Profile may not exist yet
  } finally {
    isLoading.value = false
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function intentTagType(intent: string): string {
  const map: Record<string, string> = { refund: 'danger', order: 'warning', tech: 'info', faq: 'success', human: 'danger' }
  return map[intent] || ''
}

function categoryLabel(cat: string): string {
  const map: Record<string, string> = { preference: '偏好', fact: '事实', issue: '问题', feedback: '反馈' }
  return map[cat] || cat
}

function categoryType(cat: string): string {
  const map: Record<string, string> = { preference: 'primary', fact: 'success', issue: 'warning', feedback: 'info' }
  return map[cat] || 'info'
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--primary); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* Memories Timeline */
.memory-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.memory-item {
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  transition: border-color 0.2s;
}

.memory-item:hover {
  border-color: var(--primary);
}

.memory-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.memory-time {
  font-size: 12px;
  color: var(--text-muted);
}

.memory-content {
  font-size: 14px;
  line-height: 1.6;
}
</style>
