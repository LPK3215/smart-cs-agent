<template>
  <div class="app-container">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>🤖 智能客服</h2>
        <p>ReAct Agent + SSE 流式</p>
      </div>
      <div class="sidebar-nav">
        <div class="nav-item" :class="{ active: view === 'chat' }" @click="view = 'chat'">
          <span class="icon">💬</span><span>对话</span>
          <span v-if="activeSessions" class="nav-badge">{{ activeSessions }}</span>
        </div>
        <div class="nav-item" :class="{ active: view === 'admin' }" @click="view = 'admin'">
          <span class="icon">📊</span><span>管理后台</span>
        </div>
      </div>

      <template v-if="view === 'chat'">
        <div class="new-session-btn" @click="newSession" :class="{ disabled: loading }">
          <span>＋</span> 新建对话
        </div>
        <div class="session-list">
          <div v-for="s in sessions" :key="s.id"
               class="session-item" :class="{ active: currentSessionId === s.id }"
               @click="switchSession(s.id)">
            <div class="title">{{ s.title }}</div>
            <div class="meta">
              <span>{{ formatTime(s.updated_at) }}</span>
              <span :class="'status-' + s.status">{{ statusLabel(s.status) }}</span>
            </div>
          </div>
        </div>
      </template>

      <div class="sidebar-footer">
        LangChain ReAct Agent<br>DeepSeek + SSE Streaming
      </div>
    </div>

    <!-- Main Area -->
    <div class="main-area">
      <!-- Chat View -->
      <template v-if="view === 'chat'">
        <template v-if="currentSession">
          <div class="chat-header">
            <div class="title">{{ currentSession.title }}</div>
            <div class="status">
              <span class="dot" :style="{ background: currentSession.status === 'transferred' ? '#e6a23c' : currentSession.status === 'closed' ? '#909399' : '#67c23a' }"></span>
              {{ statusLabel(currentSession.status) }}
            </div>
          </div>

          <div v-if="currentSession.status === 'transferred'" class="transfer-banner" style="margin: 12px 20px 0;">
            ⚠️ 该对话已转接人工客服，AI 自动回复已暂停
          </div>

          <div class="chat-messages" ref="messagesContainer">
            <div v-if="currentMessages.length === 0 && !isTyping && !isStreaming" class="empty-state">
              <div class="icon">👋</div>
              <p>您好！我是智能客服Agent「小智」，可以自主调用工具为您服务。有什么可以帮您的？</p>
            </div>
            <div v-for="msg in currentMessages" :key="msg.id" class="msg" :class="msg.role">
              <div class="msg-avatar">{{ msg.role === 'bot' ? '🤖' : '👤' }}</div>
              <div class="msg-body">
                <div class="msg-bubble" v-html="renderContent(msg.content)"></div>
                <div class="msg-meta">
                  <span>{{ formatTime(msg.timestamp) }}</span>
                  <span v-if="msg.intent" class="intent-badge" :class="'intent-' + msg.intent">{{ intentLabel(msg.intent) }}</span>
                  <span v-if="msg.source" class="source-tag" :class="'source-' + msg.source">{{ sourceLabel(msg.source) }}</span>
                  <span v-if="msg.confidence" style="font-size:10px;color:#c0c4cc;">{{ (msg.confidence * 100).toFixed(0) }}%</span>
                  <span v-if="msg.toolsCalled && msg.toolsCalled.length > 0" class="trace-toggle" @click="toggleTrace(msg.id)">
                    🔧 {{ msg.toolsCalled.length }} 次工具调用 ▾
                  </span>
                </div>
                <!-- Agent Trace Panel -->
                <div v-if="expandedTraces[msg.id] && msg.trace && msg.trace.length > 0" class="trace-panel">
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
                      <div v-if="step.input && Object.keys(step.input).length > 0" class="step-detail">输入: {{ JSON.stringify(step.input) }}</div>
                      <div v-if="step.output" class="step-detail">{{ typeof step.output === 'string' ? step.output : JSON.stringify(step.output) }}</div>
                      <div v-if="step.duration_ms" class="step-detail">耗时: {{ step.duration_ms }}ms</div>
                    </div>
                  </div>
                </div>
                <!-- Satisfaction rating -->
                <div v-if="msg.role === 'bot' && !isTyping && !isStreaming && msg.source" class="satisfaction">
                  <template v-if="!msg._rated">
                    <span v-for="n in 5" :key="n" class="sat-star" @click="rateMessage(msg.id, n)">☆</span>
                  </template>
                  <template v-else>
                    <span style="font-size:12px;color:#e6a23c;">{{ '★'.repeat(msg._ratedScore) }}{{ '☆'.repeat(5 - msg._ratedScore) }}</span>
                    <span style="font-size:11px;color:#909399;">已评价</span>
                  </template>
                </div>
              </div>
            </div>

            <!-- Streaming message (in-progress) -->
            <div v-if="isStreaming" class="msg bot">
              <div class="msg-avatar">🤖</div>
              <div class="msg-body">
                <div class="msg-bubble">
                  <span v-html="renderContent(streamingContent)"></span>
                  <span class="streaming-cursor"></span>
                </div>
                <!-- Tool call status during streaming -->
                <div v-for="tc in streamingToolCalls" :key="tc.tool" class="tool-status">
                  <span :class="tc.done ? '' : 'spinner'" :style="tc.done ? 'width:12px;text-align:center;' : ''">{{ tc.done ? '✅' : '' }}</span>
                  <span>{{ tc.tool }}{{ tc.done ? ' 完成' : ' 执行中...' }}</span>
                </div>
              </div>
            </div>

            <!-- Typing indicator (non-streaming fallback) -->
            <div v-if="isTyping && !isStreaming" class="msg bot">
              <div class="msg-avatar">🤖</div>
              <div class="msg-body">
                <div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div style="padding: 0 20px;">
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
              <textarea v-model="inputText" placeholder="输入您的问题..." @keydown.enter.exact.prevent="sendMessage"
                        :disabled="currentSession.status === 'transferred' || isTyping || isStreaming" rows="1" ref="inputArea"></textarea>
              <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || isTyping || isStreaming">发送</button>
            </div>
          </div>
        </template>
        <div v-else class="empty-state">
          <div class="icon">💬</div>
          <p>选择一个对话或新建对话开始</p>
        </div>
      </template>

      <!-- Admin View -->
      <template v-if="view === 'admin'">
        <AdminDashboard />
      </template>
    </div>

    <!-- Detail Modal -->
    <div v-if="detailModal" class="modal-overlay" @click.self="detailModal = null">
      <div class="modal">
        <div class="modal-header">
          <h3>对话详情</h3>
          <button class="modal-close" @click="detailModal = null">✕</button>
        </div>
        <div class="modal-body">
          <div v-for="msg in detailMessages" :key="msg.id" class="msg-preview">
            <strong>{{ msg.role === 'user' ? '👤 用户' : '🤖 客服' }}</strong>
            <span v-if="msg.intent" class="intent-badge" :class="'intent-' + msg.intent" style="margin-left:8px;">{{ intentLabel(msg.intent) }}</span>
            <span v-if="msg.source" class="source-tag" :class="'source-' + msg.source" style="margin-left:4px;">{{ sourceLabel(msg.source) }}</span>
            <p style="margin-top:4px;font-size:13px;white-space:pre-wrap;">{{ msg.content }}</p>
            <div style="font-size:11px;color:#909399;margin-top:2px;">{{ formatTime(msg.timestamp) }}</div>
            <div v-if="msg.toolsCalled && msg.toolsCalled.length > 0" style="font-size:11px;color:#409eff;margin-top:2px;">
              🔧 工具调用: {{ msg.toolsCalled.join(', ') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick, onMounted } from 'vue'
import { fetchSessions, createSession, fetchMessages, sendChatMessage, streamChatMessage, submitRating } from './utils/api.js'
import AdminDashboard from './components/AdminDashboard.vue'

export default {
  name: 'App',
  components: { AdminDashboard },
  setup() {
    const view = ref('chat')
    const sessions = ref([])
    const currentSessionId = ref(null)
    const currentMessages = ref([])
    const currentSession = ref(null)
    const inputText = ref('')
    const isTyping = ref(false)
    const isStreaming = ref(false)
    const streamingContent = ref('')
    const streamingToolCalls = ref([])
    const loading = ref(false)
    const messagesContainer = ref(null)
    const inputArea = ref(null)
    const detailModal = ref(null)
    const detailMessages = ref([])
    const expandedTraces = ref({})

    const activeSessions = computed(() => sessions.value.filter(s => s.status === 'active').length)

    onMounted(async () => {
      await loadSessions()
      window.addEventListener('show-detail', (e) => {
        showDetail(e.detail)
      })
    })

    async function loadSessions() {
      try {
        sessions.value = await fetchSessions()
        if (sessions.value.length > 0 && !currentSessionId.value) {
          await switchSession(sessions.value[0].id)
        }
      } catch (e) { console.error('Failed to load sessions:', e) }
    }

    async function switchSession(id) {
      currentSessionId.value = id
      currentSession.value = sessions.value.find(s => s.id === id) || null
      try {
        currentMessages.value = await fetchMessages(id)
      } catch (e) { currentMessages.value = [] }
      nextTick(scrollToBottom)
    }

    async function newSession() {
      if (loading.value) return
      loading.value = true
      try {
        const s = await createSession()
        sessions.value = await fetchSessions()
        await switchSession(s.id)
        inputArea.value?.focus()
      } catch (e) { console.error('Failed to create session:', e) }
      finally { loading.value = false }
    }

    async function sendMessage() {
      const text = inputText.value.trim()
      if (!text || isTyping.value || isStreaming.value) return

      const tempUserMsg = {
        id: 'temp_' + Date.now(), sessionId: currentSessionId.value,
        role: 'user', content: text, timestamp: new Date().toISOString(),
      }
      currentMessages.value.push(tempUserMsg)
      inputText.value = ''
      nextTick(scrollToBottom)

      // Try SSE streaming first
      isStreaming.value = true
      streamingContent.value = ''
      streamingToolCalls.value = []

      try {
        const response = await streamChatMessage(currentSessionId.value, text)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6).trim()
            if (!data) continue

            try {
              const event = JSON.parse(data)

              if (event.type === 'token') {
                streamingContent.value += event.content
                nextTick(scrollToBottom)
              } else if (event.type === 'tool_start') {
                streamingToolCalls.value.push({ tool: event.tool, done: false })
                nextTick(scrollToBottom)
              } else if (event.type === 'tool_end') {
                const tc = streamingToolCalls.value.find(t => t.tool === event.tool && !t.done)
                if (tc) tc.done = true
              } else if (event.type === 'done') {
                // Replace temp user msg with real one, add bot msg
                const idx = currentMessages.value.findIndex(m => m.id === tempUserMsg.id)
                if (idx >= 0) currentMessages.value.splice(idx, 1)

                // Refresh from server to get the actual saved messages
                sessions.value = await fetchSessions()
                currentSession.value = sessions.value.find(s => s.id === currentSessionId.value) || currentSession.value
                currentMessages.value = await fetchMessages(currentSessionId.value)
              } else if (event.type === 'error') {
                console.error('Stream error:', event.content)
              }
            } catch (parseErr) {
              // Skip malformed JSON
            }
          }
        }
      } catch (streamErr) {
        // Fallback to non-streaming
        console.warn('SSE failed, falling back to non-streaming:', streamErr)
        isStreaming.value = false
        isTyping.value = true

        try {
          const result = await sendChatMessage(currentSessionId.value, text)
          const idx = currentMessages.value.findIndex(m => m.id === tempUserMsg.id)
          if (idx >= 0) currentMessages.value.splice(idx, 1, result.userMessage)
          currentMessages.value.push(result.botMessage)
          sessions.value = await fetchSessions()
          currentSession.value = sessions.value.find(s => s.id === currentSessionId.value) || currentSession.value
        } catch (e) {
          console.error('Chat failed:', e)
          const idx = currentMessages.value.findIndex(m => m.id === tempUserMsg.id)
          if (idx >= 0) currentMessages.value.splice(idx, 1)
          inputText.value = text
        } finally {
          isTyping.value = false
        }
      } finally {
        isStreaming.value = false
        streamingContent.value = ''
        streamingToolCalls.value = []
        nextTick(scrollToBottom)
      }
    }

    function quickSend(text) {
      inputText.value = text
      sendMessage()
    }

    async function rateMessage(msgId, score) {
      try {
        await submitRating(currentSessionId.value, msgId, score)
        const msg = currentMessages.value.find(m => m.id === msgId)
        if (msg) { msg._rated = true; msg._ratedScore = score }
      } catch (e) { console.error('Rating failed:', e) }
    }

    function toggleTrace(msgId) {
      expandedTraces.value[msgId] = !expandedTraces.value[msgId]
    }

    function scrollToBottom() {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    function formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      const now = new Date()
      const isToday = d.toDateString() === now.toDateString()
      return isToday
        ? d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        : d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }

    function intentLabel(intent) {
      const map = { refund: '💰 退款', order: '📦 订单', tech: '🔧 技术', faq: '❓ 常见', human: '👤 转人工', unknown: '❔ 未知' }
      return map[intent] || intent
    }

    function sourceLabel(source) {
      const map = { ai: '🤖 Agent', faq: '📚 知识库', human: '👤 人工客服', system: '🗄️ 系统查询' }
      return map[source] || source
    }

    function statusLabel(status) {
      const map = { active: '在线', transferred: '已转人工', closed: '已结束' }
      return map[status] || status
    }

    function renderContent(text) {
      return text.replace(/\n/g, '<br>')
    }

    function showDetail(sessionId) {
      fetchMessages(sessionId).then(msgs => {
        detailMessages.value = msgs
        detailModal.value = sessionId
      })
    }

    return {
      view, sessions, currentSessionId, currentMessages, currentSession,
      inputText, isTyping, isStreaming, streamingContent, streamingToolCalls,
      loading, messagesContainer, inputArea, detailModal, detailMessages,
      expandedTraces, activeSessions,
      switchSession, newSession, sendMessage, quickSend, rateMessage,
      toggleTrace, formatTime, intentLabel, sourceLabel, statusLabel,
      renderContent, showDetail
    }
  }
}
</script>
