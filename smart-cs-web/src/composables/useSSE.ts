import { useChatStore } from '@/stores/chat'
import { parseSSEStream } from '@/utils/sse'
import * as api from '@/utils/api'

/**
 * Composable for SSE streaming integration with the chat store.
 */
export function useSSE() {
  const chatStore = useChatStore()
  let abortController: AbortController | null = null

  async function startStreaming(sessionId: string, message: string): Promise<void> {
    chatStore.isStreaming = true
    chatStore.streamingContent = ''
    chatStore.streamingToolCalls = []
    abortController = new AbortController()

    try {
      const response = await api.streamChatMessage(sessionId, message)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      await parseSSEStream(
        response,
        {
          onToken(content) {
            chatStore.streamingContent += content
          },
          onThinking(content) {
            // Could display thinking text in a separate area
          },
          onToolStart(tool, _input) {
            chatStore.streamingToolCalls.push({ tool, done: false })
          },
          onToolEnd(tool, _output, _durationMs) {
            const tc = chatStore.streamingToolCalls.find(t => t.tool === tool && !t.done)
            if (tc) tc.done = true
          },
          onDone(_event) {
            // Will refresh sessions + messages in the finally block
          },
          onError(content) {
            console.error('SSE error:', content)
          },
        },
        abortController.signal,
      )
    } catch (err) {
      // If it's an abort, just reset silently
      if (abortController.signal.aborted) return
      throw err // Re-throw for fallback handling
    } finally {
      chatStore.isStreaming = false
      chatStore.streamingContent = ''
      chatStore.streamingToolCalls = []
      abortController = null
    }
  }

  function cancelStreaming() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    chatStore.isStreaming = false
    chatStore.streamingContent = ''
    chatStore.streamingToolCalls = []
  }

  return { startStreaming, cancelStreaming }
}
