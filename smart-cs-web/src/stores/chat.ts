import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { Session, Message, StreamingToolCall } from '@/types'
import * as api from '@/utils/api'
import { parseSSEStream } from '@/utils/sse'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string | null>(null)
  const messages = ref<Record<string, Message[]>>({})
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const isTyping = ref(false)
  const streamingContent = ref('')
  const streamingToolCalls = ref<StreamingToolCall[]>([])
  const expandedTraces = ref<Record<string, boolean>>({})

  const currentSession = computed(() => sessions.value.find(s => s.id === currentSessionId.value) || null)
  const currentMessages = computed(() => messages.value[currentSessionId.value || ''] || [])
  const activeSessionCount = computed(() => sessions.value.filter(s => s.status === 'active').length)

  async function loadSessions() {
    try {
      sessions.value = await api.fetchSessions()
      if (sessions.value.length > 0 && !currentSessionId.value) {
        await switchSession(sessions.value[0].id)
      }
    } catch (e) {
      console.error('Failed to load sessions:', e)
    }
  }

  async function switchSession(id: string) {
    currentSessionId.value = id
    if (!messages.value[id]) {
      await loadMessages(id)
    }
  }

  async function loadMessages(sessionId: string) {
    try {
      messages.value[sessionId] = await api.fetchMessages(sessionId)
    } catch {
      messages.value[sessionId] = []
    }
  }

  async function createSession() {
    if (isLoading.value) return
    isLoading.value = true
    try {
      const s = await api.createSession()
      sessions.value = await api.fetchSessions()
      await switchSession(s.id)
      ElMessage.success('新对话已创建')
    } catch (e) {
      console.error('Failed to create session:', e)
      ElMessage.error('创建对话失败，请重试')
    } finally {
      isLoading.value = false
    }
  }

  async function sendMessage(text: string) {
    if (!text || isTyping.value || isStreaming.value || !currentSessionId.value) return

    const sessionId = currentSessionId.value
    const tempUserMsg: Message = {
      id: 'temp_' + Date.now(),
      sessionId,
      role: 'user',
      content: text,
      toolsCalled: [],
      trace: [],
      timestamp: new Date().toISOString(),
    }

    if (!messages.value[sessionId]) messages.value[sessionId] = []
    messages.value[sessionId].push(tempUserMsg)

    // Try SSE streaming first
    isStreaming.value = true
    streamingContent.value = ''
    streamingToolCalls.value = []

    try {
      const response = await api.streamChatMessage(sessionId, text)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      await parseSSEStream(response, {
        onToken(content) {
          streamingContent.value += content
        },
        onToolStart(tool) {
          streamingToolCalls.value.push({ tool, done: false })
        },
        onToolEnd(tool) {
          const tc = streamingToolCalls.value.find(t => t.tool === tool && !t.done)
          if (tc) tc.done = true
        },
        onDone() {
          // Will refresh in finally block
        },
        onError(content) {
          console.error('Stream error:', content)
        },
      })

      // Refresh from server after stream completes
      sessions.value = await api.fetchSessions()
      await loadMessages(sessionId)
    } catch (streamErr) {
      // Fallback to non-streaming
      console.warn('SSE failed, falling back:', streamErr)
      ElMessage.warning('流式连接中断，正在重试...')
      isStreaming.value = false
      isTyping.value = true

      try {
        const result = await api.sendChatMessage(sessionId, text)
        const idx = messages.value[sessionId].findIndex(m => m.id === tempUserMsg.id)
        if (idx >= 0) messages.value[sessionId].splice(idx, 1, result.userMessage)
        messages.value[sessionId].push(result.botMessage)
        sessions.value = await api.fetchSessions()
      } catch (e) {
        console.error('Chat failed:', e)
        ElMessage.error('发送消息失败，请重试')
        const idx = messages.value[sessionId].findIndex(m => m.id === tempUserMsg.id)
        if (idx >= 0) messages.value[sessionId].splice(idx, 1)
      } finally {
        isTyping.value = false
      }
    } finally {
      isStreaming.value = false
      streamingContent.value = ''
      streamingToolCalls.value = []
    }
  }

  async function rateMessage(msgId: string, score: number) {
    if (!currentSessionId.value) return
    try {
      await api.submitRating({ sessionId: currentSessionId.value, msgId, score })
      const msg = messages.value[currentSessionId.value]?.find(m => m.id === msgId)
      if (msg) {
        msg._rated = true
        msg._ratedScore = score
      }
      ElMessage.success('感谢评价！')
    } catch (e) {
      console.error('Rating failed:', e)
      ElMessage.error('评价提交失败')
    }
  }

  async function closeCurrentSession() {
    if (!currentSessionId.value) return
    try {
      await api.closeSession(currentSessionId.value)
      sessions.value = await api.fetchSessions()
      ElMessage.success('对话已关闭，记忆已提取')
    } catch (e) {
      console.error('Failed to close session:', e)
      ElMessage.error('关闭对话失败')
    }
  }

  function toggleTrace(msgId: string) {
    expandedTraces.value[msgId] = !expandedTraces.value[msgId]
  }

  return {
    sessions, currentSessionId, messages, isLoading, isStreaming, isTyping,
    streamingContent, streamingToolCalls, expandedTraces,
    currentSession, currentMessages, activeSessionCount,
    loadSessions, switchSession, createSession, sendMessage,
    rateMessage, closeCurrentSession, loadMessages, toggleTrace,
  }
})
