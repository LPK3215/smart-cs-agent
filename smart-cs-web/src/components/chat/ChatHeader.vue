<template>
  <div class="chat-header">
    <div class="title">{{ session.title }}</div>
    <div class="header-actions">
      <span class="status">
        <span class="dot" :style="{ background: dotColor }"></span>
        {{ statusLabel(session.status) }}
      </span>
      <button
        v-if="session.status === 'active'"
        class="close-btn"
        @click="$emit('close-session')"
        title="关闭对话"
      >✕</button>
    </div>
  </div>
  <div v-if="session.status === 'transferred'" class="transfer-banner" style="margin: 0 20px;">
    ⚠️ 该对话已转接人工客服，AI 自动回复已暂停
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Session } from '@/types'
import { statusLabel } from '@/utils/format'

const props = defineProps<{ session: Session }>()
defineEmits<{ 'close-session': [] }>()

const dotColor = computed(() => {
  if (props.session.status === 'transferred') return '#e6a23c'
  if (props.session.status === 'closed') return '#909399'
  return '#67c23a'
})
</script>

<style scoped>
.header-actions { display: flex; align-items: center; gap: 12px; }
.close-btn {
  background: none; border: 1px solid var(--border); border-radius: 4px;
  cursor: pointer; font-size: 12px; color: var(--text-muted);
  padding: 2px 8px; transition: all 0.2s;
}
.close-btn:hover { border-color: var(--danger); color: var(--danger); background: #fef0f0; }
</style>
