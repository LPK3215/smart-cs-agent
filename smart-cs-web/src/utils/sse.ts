import type { SSEEvent, SSEDoneEvent } from '@/types'

export interface SSECallbacks {
  onToken: (content: string) => void
  onThinking?: (content: string) => void
  onToolStart: (tool: string, input: Record<string, unknown>) => void
  onToolEnd: (tool: string, output: unknown, durationMs: number) => void
  onDone: (event: SSEDoneEvent) => void
  onError: (content: string) => void
}

/**
 * Parse an SSE stream from a fetch Response.
 * Reads the body as a ReadableStream, splits by newlines,
 * and dispatches parsed JSON events to the provided callbacks.
 */
export async function parseSSEStream(
  response: Response,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
): Promise<void> {
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
        const event: SSEEvent = JSON.parse(data)

        switch (event.type) {
          case 'token':
            callbacks.onToken(event.content)
            break
          case 'thinking':
            callbacks.onThinking?.(event.content)
            break
          case 'tool_start':
            callbacks.onToolStart(event.tool, event.input)
            break
          case 'tool_end':
            callbacks.onToolEnd(event.tool, event.output, event.duration_ms)
            break
          case 'done':
            callbacks.onDone(event)
            break
          case 'error':
            callbacks.onError(event.content)
            break
        }
      } catch {
        // Skip malformed JSON lines
      }
    }

    if (signal?.aborted) {
      reader.cancel()
      break
    }
  }
}
