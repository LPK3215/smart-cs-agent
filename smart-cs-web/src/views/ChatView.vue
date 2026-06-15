<template>
  <div class="chat-page">
    <!-- Session List (in sidebar area) -->
    <div class="chat-sidebar" v-if="true">
      <div class="new-session-btn" @click="chatStore.createSession()" :class="{ disabled: chatStore.isLoading }">
        <span>＋</span> 新建对话
      </div>
      <div class="session-list">
        <div
          v-for="s in chatStore.sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: chatStore.currentSessionId === s.id }"
          @click="chatStore.switchSession(s.id)"
        >
          <div class="title">{{ s.title }}</div>
          <div class="meta">
            <span>{{ formatTime(s.updated_at) }}</span>
            <span :class="'status-' + s.status">{{ statusLabel(s.status) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Main -->
    <div class="chat-main">
      <template v-if="chatStore.currentSession">
        <div class="chat-header">
          <div class="title">{{ chatStore.currentSession.title }}</div>
          <div class="status">
            <span
              class="dot"
              :style="{
                background:
                  chatStore.currentSession.status === 'transferred'
                    ? '#e6a23c'
                    : chatStore.currentSession.status === 'closed'
                      ? '#909399'
                      : '#67c23a',
              }"
            ></span>
            {{ statusLabel(chatStore.currentSession.status) }}
          </div>
        </div>

        <div v-if="chatStore.currentSession.status === 'transferred'" class="transfer-banner" style="margin: 12px 20px 0">
          ⚠️ 该对话已转接人工客服，AI 自动回复已暂停
        </div>

        <div class="chat-messages" ref="messagesContainer">
          <div v-if="chatStore.currentMessages.length === 0 && !chatStore.isTyping && !chatStore.isStreaming" class="empty-state">
            <div class="icon">👋</div>
            <p>您好！我是智能客服Agent「小智」，可以自主调用工具为您服务。有什么可以帮您的？</p>
          </div>

          <div v-for="msg in chatStore.currentMessages" :key="msg.id" class="msg" :class="msg.role">
            <div class="msg-avatar">{{ msg.role === 'bot' ? '🤖' : '👤' }}</div>
            <div class="msg-body">
              <div class="msg-bubble" v-html="renderContent(msg.content)"></div>
              <div class="msg-meta">
                <span>{{ formatTime(msg.timestamp) }}</span>
                <span v-if="msg.intent" class="intent-badge" :class="'intent-' + msg.intent">{{ intentLabel(msg.intent) }}</span>
                <span v-if="msg.source" class="source-tag" :class="'source-' + msg.source">{{ sourceLabel(msg.source) }}</span>
                <span v-if="msg.confidence" style="font-size: 10px; color: #c0c4cc">{{ (msg.confidence * 100).toFixed(0) }}%</span>
                <span v-if="msg.toolsCalled && msg.toolsCalled.length > 0" class="trace-toggle" @click="chatStore.toggleTrace(msg.id)">
                  🔧 {{ msg.toolsCalled.length }} 次工具调用 ▾
                </span>
              </div>
              <!-- Agent Trace Panel -->
              <div v-if="chatStore.expandedTraces[msg.id] && msg.trace && msg.trace.length > 0" class="trace-panel">
                <div v-for="(step, idx) in msg.trace" :key="idx" class="trace-step" :class="step.type">
                  <div class="step-icon">
                    <template v-if="step.type === 'reasoning'">💭</template>
                    <template v-else-if="step.type === 'tool_call'">🔧</template>
                    <template v-else-if="step.type === 'tool_result'">✅</template>
                  </div>
                  <div class="step-content">
                    <div class="step-label">
                      <template v-if="step.type === 'reasoning'">推理</template>
                      <template v-else-if="step.type === 'tool_call'">调用 {{ step.tool }}</template>
                      <template v-else-if="step.type === 'tool_result'">{{ step.tool }} 返回</template>
                    </div>
                    <div v-if="step.type === 'reasoning'" class="step-detail">{{ step.thought }}</div>
                    <div v-if="step.input && Object.keys(step.input).length > 0" class="step-detail">
                      输入: {{ JSON.stringify(step.input) }}
                    </div>
                    <div v-if="step.output" class="step-detail">
                      {{ typeof step.output === 'string' ? step.output : JSON.stringify(step.output) }}
                    </div>
                    <div v-if="step.duration_ms" class="step-detail">耗时: {{ step.duration_ms }}ms</div>
                  </div>
                </div>
              </div>
              <!-- Satisfaction rating -->
              <div v-if="msg.role === 'bot' && !chatStore.isTyping && !chatStore.isStreaming && msg.source" class="satisfaction">
                <template v-if="!msg._rated">
                  <span v-for="n in 5" :key="n" class="sat-star" @click="chatStore.rateMessage(msg.id, n)">☆</span>
                </template>
                <template v-else>
                  <span style="font-size: 12px; color: #e6a23c">{{ '★'.repeat(msg._ratedScore!) }}{{ '☆'.repeat(5 - msg._ratedScore!) }}</span>
                  <span style="font-size: 11px; color: #909399">已评价</span>
                </template>
              </div>
            </div>
          </div>

          <!-- Streaming message -->
          <div v-if="chatStore.isStreaming" class="msg bot">
            <div class="msg-avatar">🤖</div>
            <div class="msg-body">
              <div class="msg-bubble">
                <span v-html="renderContent(chatStore.streamingContent)"></span>
                <span class="streaming-cursor"></span>
              </div>
              <div v-for="tc in chatStore.streamingToolCalls" :key="tc.tool" class="tool-status">
                <span :class="tc.done ? '' : 'spinner'" :style="tc.done ? 'width:12px;text-align:center;' : ''">{{ tc.done ? '✅' : '' }}</span>
                <span>{{ tc.tool }}{{ tc.done ? ' 完成' : ' 执行中...' }}</span>
              </div>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="chatStore.isTyping && !chatStore.isStreaming" class="msg bot">
            <div class="msg-avatar">🤖</div>
            <div class="msg-body">
              <div class="msg-bubble">
                <div class="typing"><span></span><span></span><span></span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div style="padding: 0 20px">
          <div class="quick-actions">
            <span class="quick-btn" @click="quickSend('如何申请退款？')">💰 退款申请</span>
            <span class="quick-btn" @click="quickSend('查询我的订单')">📦 订单查询</span>
            <span class="quick-btn" @click="quickSend('APP闪退怎么办')">🔧 技术支持</span>
            <span class="quick-btn" @click="quickSend('转人工客服')">👤 转人工</span>
          </div>
        </div>

        <!-- Input -->
        <div class="chat-input">
          <div class="input-row">
            <textarea
              v-model="inputText"
              placeholder="输入您的问题..."
              @keydown.enter.exact.prevent="handleSend"
              :disabled="chatStore.currentSession.status === 'transferred' || chatStore.isTyping || chatStore.isStreaming"
              rows="1"
              ref="inputArea"
            ></textarea>
            <button class="send-btn" @click="handleSend" :disabled="!inputText.trim() || chatStore.isTyping || chatStore.isStreaming">
              发送
            </button>
          </div>
        </div>
      </template>
      <div v-else class="empty-state">
        <div class="icon">💬</div>
        <p>选择一个对话或新建对话开始</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { formatTime, intentLabel, sourceLabel, statusLabel } from '@/utils/format'

const chatStore = useChatStore()
const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const inputArea = ref<HTMLTextAreaElement | null>(null)

onMounted(async () => {
  await chatStore.loadSessions()
})

watch(
  () => chatStore.currentMessages.length,
  () => nextTick(scrollToBottom),
)
watch(
  () => chatStore.streamingContent,
  () => nextTick(scrollToBottom),
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.isTyping || chatStore.isStreaming) return
  inputText.value = ''
  chatStore.sendMessage(text)
}

function quickSend(text: string) {
  inputText.value = text
  handleSend()
}

function renderContent(text: string): string {
  return text.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.chat-sidebar {
  width: 240px;
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  background: var(--card);
  flex-shrink: 0;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
