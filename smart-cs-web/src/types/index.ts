// === User & Auth ===

export interface User {
  id: string
  username: string
  displayName: string
  role: 'user' | 'admin'
  createdAt: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  password: string
  displayName: string
}

export interface TokenResponse {
  accessToken: string
  tokenType: string
  user: User
}

// === Sessions ===

export type SessionStatus = 'active' | 'transferred' | 'closed'

export interface Session {
  id: string
  title: string
  user_id: string
  status: SessionStatus
  summary: string
  created_at: string
  updated_at: string
}

// === Messages ===

export type MessageRole = 'user' | 'bot'
export type Intent = 'refund' | 'order' | 'tech' | 'faq' | 'human' | 'unknown'
export type Source = 'ai' | 'faq' | 'human' | 'system'

export interface TraceStep {
  type: 'reasoning' | 'tool_call' | 'tool_result'
  thought?: string
  tool?: string
  input?: Record<string, unknown>
  output?: unknown
  duration_ms?: number
}

export interface Message {
  id: string
  sessionId: string
  role: MessageRole
  content: string
  intent?: Intent
  source?: Source
  confidence?: number
  toolsCalled: string[]
  trace: TraceStep[]
  timestamp: string
  _rated?: boolean
  _ratedScore?: number
}

// === SSE Events ===

export type SSEEventType = 'token' | 'thinking' | 'tool_start' | 'tool_end' | 'done' | 'error'

export interface SSETokenEvent {
  type: 'token'
  content: string
}

export interface SSEThinkingEvent {
  type: 'thinking'
  content: string
}

export interface SSEToolStartEvent {
  type: 'tool_start'
  tool: string
  input: Record<string, unknown>
}

export interface SSEToolEndEvent {
  type: 'tool_end'
  tool: string
  output: unknown
  duration_ms: number
}

export interface SSEDoneEvent {
  type: 'done'
  intent: Intent
  source: Source
  confidence: number
  need_human: boolean
  tools_called: string[]
  trace: TraceStep[]
}

export interface SSEErrorEvent {
  type: 'error'
  content: string
}

export type SSEEvent =
  | SSETokenEvent
  | SSEThinkingEvent
  | SSEToolStartEvent
  | SSEToolEndEvent
  | SSEDoneEvent
  | SSEErrorEvent

// === Streaming State ===

export interface StreamingToolCall {
  tool: string
  done: boolean
}

// === Chat ===

export interface ChatRequest {
  sessionId: string
  message: string
}

// === Ratings ===

export interface RatingPayload {
  sessionId: string
  msgId: string
  score: number
}

// === Analytics ===

export interface AnalyticsData {
  totalSessions: number
  totalMessages: number
  intentCounts: Record<string, number>
  sourceCounts: Record<string, number>
  statusCounts: Record<string, number>
  avgRating: string
  ratingDist: Record<string, number>
  ratingCount: number
  intentResolution: Record<string, { total: number; resolved: number }>
  transferRate: string
  toolStats: Record<string, { count: number; total_ms: number; errors: number }>
  sessions: Session[]
  allMsgs: Record<string, Message[]>
}

// === User Profile ===

export interface UserProfile {
  id: string
  username: string
  displayName: string
  role: string
  createdAt: string
  profile?: {
    total_sessions: number
    transfer_count: number
    transfer_rate: number
    top_intents: Record<string, number>
    avg_rating: number | null
    last_active: string
  }
  memories?: Array<{
    id: number
    content: string
    category: string
    created_at: string
  }>
}
