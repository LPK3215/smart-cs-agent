<template>
  <div class="msg bot">
    <div class="msg-avatar">🤖</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <span v-html="renderedContent"></span>
        <span class="streaming-cursor"></span>
      </div>
      <div v-for="tc in toolCalls" :key="tc.tool" class="tool-status">
        <span :class="tc.done ? '' : 'spinner'" :style="tc.done ? 'width:12px;text-align:center;' : ''">
          {{ tc.done ? '✅' : '' }}
        </span>
        <span>{{ tc.tool }}{{ tc.done ? ' 完成' : ' 执行中...' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StreamingToolCall } from '@/types'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  content: string
  toolCalls: StreamingToolCall[]
}>()

const renderedContent = computed(() => renderMarkdown(props.content))
</script>
