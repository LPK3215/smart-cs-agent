// API client for smart-cs-server backend

const API_BASE = '/api'

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// Sessions
export async function fetchSessions() {
  return request('/sessions')
}

export async function createSession(userId) {
  return request('/sessions', {
    method: 'POST',
    body: JSON.stringify({ userId }),
  })
}

export async function fetchSession(sessionId) {
  return request(`/sessions/${sessionId}`)
}

export async function closeSession(sessionId) {
  return request(`/sessions/${sessionId}/close`, { method: 'POST' })
}

// Chat (non-streaming)
export async function sendChatMessage(sessionId, message) {
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify({ sessionId, message }),
  })
}

// Chat (SSE streaming)
export function streamChatMessage(sessionId, message) {
  return fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, message }),
  })
}

// Messages
export async function fetchMessages(sessionId) {
  return request(`/sessions/${sessionId}/messages`)
}

// Ratings
export async function submitRating(sessionId, msgId, score) {
  return request('/ratings', {
    method: 'POST',
    body: JSON.stringify({ sessionId, msgId, score }),
  })
}

export async function fetchRatings(sessionId) {
  return request(`/ratings?session_id=${sessionId}`)
}

// Analytics
export async function fetchAnalytics() {
  return request('/analytics')
}

// Tool Audit
export async function fetchToolAudit(sessionId, limit = 50) {
  const params = new URLSearchParams()
  if (sessionId) params.set('session_id', sessionId)
  params.set('limit', limit)
  return request(`/tool-audit?${params}`)
}
