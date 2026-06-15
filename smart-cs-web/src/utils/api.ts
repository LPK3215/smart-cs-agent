import type { Session, Message, RatingPayload, AnalyticsData, TokenResponse, LoginPayload, RegisterPayload, UserProfile } from '@/types'

const API_BASE = '/api'

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers as Record<string, string> || {}),
  }

  const res = await fetch(url, { ...options, headers })

  if (res.status === 401) {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    window.location.href = '/login'
    throw new Error('未授权，请重新登录')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '请求失败')
  }

  return res.json()
}

// === Auth ===

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function register(payload: RegisterPayload): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getMe(): Promise<UserProfile> {
  return request<UserProfile>('/auth/me')
}

// === Sessions ===

export async function fetchSessions(): Promise<Session[]> {
  return request<Session[]>('/sessions')
}

export async function createSession(userId?: string): Promise<Session> {
  return request<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ userId }),
  })
}

export async function fetchSession(sessionId: string): Promise<Session> {
  return request<Session>(`/sessions/${sessionId}`)
}

export async function closeSession(sessionId: string): Promise<void> {
  await request(`/sessions/${sessionId}/close`, { method: 'POST' })
}

// === Chat ===

export async function sendChatMessage(sessionId: string, message: string): Promise<{ userMessage: Message; botMessage: Message }> {
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify({ sessionId, message }),
  })
}

export function streamChatMessage(sessionId: string, message: string): Promise<Response> {
  return fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ sessionId, message }),
  })
}

// === Messages ===

export async function fetchMessages(sessionId: string): Promise<Message[]> {
  return request<Message[]>(`/sessions/${sessionId}/messages`)
}

// === Ratings ===

export async function submitRating(payload: RatingPayload): Promise<void> {
  await request('/ratings', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// === Analytics ===

export async function fetchAnalytics(): Promise<AnalyticsData> {
  return request<AnalyticsData>('/analytics')
}

// === Tool Audit ===

export async function fetchToolAudit(sessionId?: string, limit: number = 50): Promise<any[]> {
  const params = new URLSearchParams()
  if (sessionId) params.set('session_id', sessionId)
  params.set('limit', String(limit))
  return request(`/tool-audit?${params}`)
}
