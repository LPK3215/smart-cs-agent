<template>
  <div class="chat-sidebar">
    <div class="new-session-btn" @click="$emit('new-session')" :class="{ disabled: loading }">
      <span>＋</span> 新建对话
    </div>
    <div class="session-list">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: currentSessionId === s.id }"
        @click="$emit('select-session', s.id)"
      >
        <div class="title">{{ s.title }}</div>
        <div class="meta">
          <span>{{ formatTime(s.updated_at) }}</span>
          <span :class="'status-' + s.status">{{ statusLabel(s.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'
import { formatTime, statusLabel } from '@/utils/format'

defineProps<{
  sessions: Session[]
  currentSessionId: string | null
  loading: boolean
}>()

defineEmits<{
  'new-session': []
  'select-session': [sessionId: string]
}>()
</script>

<style scoped>
.chat-sidebar {
  width: 240px;
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  background: var(--card);
  flex-shrink: 0;
}
</style>
