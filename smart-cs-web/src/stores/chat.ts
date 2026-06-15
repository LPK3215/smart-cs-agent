import { defineStore } from 'pinia'
import { ref, computed, nextTick } from 'vue'
import type { Session, Message, StreamingToolCall } from '@/types'
import * as api from '@/utils/api'

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
    } catch (e) {
      console.error('Failed to create session:', e)
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

      const reader = response.body!.getReader()
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
              await nextTick()
            } else if (event.type === 'tool_start') {
              streamingToolCalls.value.push({ tool: event.tool, done: false })
            } else if (event.type === 'tool_end') {
              const tc = streamingToolCalls.value.find(t => t.tool === event.tool && !t.done)
              if (tc) tc.done = true
            } else if (event.type === 'done') {
              // Refresh from server
              sessions.value = await api.fetchSessions()
              await loadMessages(sessionId)
            } else if (event.type === 'error') {
              console.error('Stream error:', event.content)
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch (streamErr) {
      // Fallback to non-streaming
      console.warn('SSE failed, falling back:', streamErr)
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
    } catch (e) {
      console.error('Rating failed:', e)
    }
  }

  async function closeCurrentSession() {
    if (!currentSessionId.value) return
    try {
      await api.closeSession(currentSessionId.value)
      sessions.value = await api.fetchSessions()
    } catch (e) {
      console.error('Failed to close session:', e)
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
