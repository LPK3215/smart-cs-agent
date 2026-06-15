<template>
  <div class="chat-messages" ref="containerRef">
    <div v-if="messages.length === 0 && !isTyping && !isStreaming" class="empty-state">
      <div class="icon">👋</div>
      <p>您好！我是智能客服Agent「小智」，可以自主调用工具为您服务。有什么可以帮您的？</p>
    </div>

    <MessageBubble
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
      :is-expanded="!!expandedTraces[msg.id]"
      :is-streaming="isStreaming"
      @toggle-trace="(id) => $emit('toggle-trace', id)"
      @rate="(id, score) => $emit('rate', id, score)"
    />

    <StreamingIndicator
      v-if="isStreaming"
      :content="streamingContent"
      :tool-calls="streamingToolCalls"
    />

    <div v-if="isTyping && !isStreaming" class="msg bot">
      <div class="msg-avatar">🤖</div>
      <div class="msg-body">
        <div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Message, StreamingToolCall } from '@/types'
import MessageBubble from './MessageBubble.vue'
import StreamingIndicator from './StreamingIndicator.vue'

const props = defineProps<{
  messages: Message[]
  isStreaming: boolean
  isTyping: boolean
  streamingContent: string
  streamingToolCalls: StreamingToolCall[]
  expandedTraces: Record<string, boolean>
}>()

defineEmits<{
  'toggle-trace': [msgId: string]
  'rate': [msgId: string, score: number]
}>()

const containerRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

watch(() => props.messages.length, () => nextTick(scrollToBottom))
watch(() => props.streamingContent, () => nextTick(scrollToBottom))

defineExpose({ scrollToBottom })
</script>

<style scoped>
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
</style>
