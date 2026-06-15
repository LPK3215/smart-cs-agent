<template>
  <div class="msg" :class="message.role">
    <div class="msg-avatar">{{ message.role === 'bot' ? '🤖' : '👤' }}</div>
    <div class="msg-body">
      <div class="msg-bubble" v-html="renderedContent"></div>
      <div class="msg-meta">
        <span>{{ formatTime(message.timestamp) }}</span>
        <span v-if="message.intent" class="intent-badge" :class="'intent-' + message.intent">
          {{ intentLabel(message.intent) }}
        </span>
        <span v-if="message.source" class="source-tag" :class="'source-' + message.source">
          {{ sourceLabel(message.source) }}
        </span>
        <span v-if="message.confidence" style="font-size:10px;color:#c0c4cc;">
          {{ (message.confidence * 100).toFixed(0) }}%
        </span>
        <span
          v-if="message.toolsCalled && message.toolsCalled.length > 0"
          class="trace-toggle"
          @click="$emit('toggle-trace', message.id)"
        >
          🔧 {{ message.toolsCalled.length }} 次工具调用 ▾
        </span>
      </div>
      <AgentTrace v-if="isExpanded && message.trace && message.trace.length > 0" :trace="message.trace" />
      <div v-if="message.role === 'bot' && !isStreaming && message.source" class="satisfaction">
        <template v-if="!message._rated">
          <span v-for="n in 5" :key="n" class="sat-star" @click="$emit('rate', message.id, n)">☆</span>
        </template>
        <template v-else>
          <span style="font-size:12px;color:#e6a23c;">
            {{ '★'.repeat(message._ratedScore!) }}{{ '☆'.repeat(5 - message._ratedScore!) }}
          </span>
          <span style="font-size:11px;color:#909399;">已评价</span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/types'
import { formatTime, intentLabel, sourceLabel } from '@/utils/format'
import { renderMarkdown } from '@/utils/markdown'
import AgentTrace from './AgentTrace.vue'

const props = defineProps<{
  message: Message
  isExpanded: boolean
  isStreaming: boolean
}>()

defineEmits<{
  'toggle-trace': [msgId: string]
  'rate': [msgId: string, score: number]
}>()

const escapeHtml = (str: string) =>
  str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

const renderedContent = computed(() => {
  if (props.message.role === 'user') {
    return escapeHtml(props.message.content).replace(/\n/g, '<br>')
  }
  return renderMarkdown(props.message.content)
})
</script>
