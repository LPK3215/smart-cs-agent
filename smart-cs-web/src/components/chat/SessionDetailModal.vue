<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('update:visible', false)">
      <div class="modal">
        <div class="modal-header">
          <h3>对话详情</h3>
          <button class="modal-close" @click="$emit('update:visible', false)">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="loading" style="text-align:center;padding:20px;color:var(--text-muted);">加载中...</div>
          <div v-for="msg in messages" :key="msg.id" class="msg-preview">
            <strong>{{ msg.role === 'user' ? '👤 用户' : '🤖 客服' }}</strong>
            <span v-if="msg.intent" class="intent-badge" :class="'intent-' + msg.intent" style="margin-left:8px;">
              {{ intentLabel(msg.intent) }}
            </span>
            <span v-if="msg.source" class="source-tag" :class="'source-' + msg.source" style="margin-left:4px;">
              {{ sourceLabel(msg.source) }}
            </span>
            <p style="margin-top:4px;font-size:13px;white-space:pre-wrap;">{{ msg.content }}</p>
            <div style="font-size:11px;color:#909399;margin-top:2px;">{{ formatTime(msg.timestamp) }}</div>
            <div v-if="msg.toolsCalled && msg.toolsCalled.length > 0" style="font-size:11px;color:#409eff;margin-top:2px;">
              🔧 工具调用: {{ msg.toolsCalled.join(', ') }}
            </div>
          </div>
          <div v-if="!loading && messages.length === 0" style="text-align:center;padding:20px;color:var(--text-muted);">
            暂无消息
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Message } from '@/types'
import { formatTime, intentLabel, sourceLabel } from '@/utils/format'
import * as api from '@/utils/api'

const props = defineProps<{
  visible: boolean
  sessionId: string | null
}>()

defineEmits<{ 'update:visible': [val: boolean] }>()

const messages = ref<Message[]>([])
const loading = ref(false)

watch(() => props.visible, async (val) => {
  if (val && props.sessionId) {
    loading.value = true
    try {
      messages.value = await api.fetchMessages(props.sessionId)
    } catch {
      messages.value = []
    } finally {
      loading.value = false
    }
  }
})
</script>
