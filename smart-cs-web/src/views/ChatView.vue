<template>
  <div class="chat-page">
    <ChatSidebar
      :sessions="chatStore.sessions"
      :current-session-id="chatStore.currentSessionId"
      :loading="chatStore.isLoading"
      @new-session="chatStore.createSession()"
      @select-session="(id) => chatStore.switchSession(id)"
    />

    <div class="chat-main">
      <template v-if="chatStore.currentSession">
        <ChatHeader
          :session="chatStore.currentSession"
          @close-session="chatStore.closeCurrentSession()"
        />

        <MessageList
          :messages="chatStore.currentMessages"
          :is-streaming="chatStore.isStreaming"
          :is-typing="chatStore.isTyping"
          :streaming-content="chatStore.streamingContent"
          :streaming-tool-calls="chatStore.streamingToolCalls"
          :expanded-traces="chatStore.expandedTraces"
          @toggle-trace="(id) => chatStore.toggleTrace(id)"
          @rate="(id, score) => chatStore.rateMessage(id, score)"
        />

        <div style="padding: 0 20px;">
          <QuickActions
            v-if="chatStore.currentSession.status === 'active'"
            @quick-send="handleQuickSend"
          />
        </div>

        <ChatInput
          ref="chatInputRef"
          :disabled="chatStore.currentSession.status !== 'active' || chatStore.isTyping || chatStore.isStreaming"
          :session-status="chatStore.currentSession.status"
          @send="handleSend"
        />
      </template>

      <div v-else class="empty-state">
        <div class="icon">💬</div>
        <p>选择一个对话或新建对话开始</p>
      </div>
    </div>

    <SessionDetailModal v-model:visible="modalVisible" :session-id="modalSessionId" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatHeader from '@/components/chat/ChatHeader.vue'
import MessageList from '@/components/chat/MessageList.vue'
import QuickActions from '@/components/chat/QuickActions.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import SessionDetailModal from '@/components/chat/SessionDetailModal.vue'

const chatStore = useChatStore()
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null)
const modalVisible = ref(false)
const modalSessionId = ref<string | null>(null)

onMounted(async () => {
  await chatStore.loadSessions()
})

function handleSend(text: string) {
  chatStore.sendMessage(text)
}

function handleQuickSend(text: string) {
  chatStore.sendMessage(text)
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
