import type { Intent, Source, SessionStatus } from '@/types'

export function formatTime(ts: string | undefined): string {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  return isToday
    ? d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) +
        ' ' +
        d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const intentMap: Record<string, string> = {
  refund: '💰 退款',
  order: '📦 订单',
  tech: '🔧 技术',
  faq: '❓ 常见',
  human: '👤 转人工',
  unknown: '❔ 未知',
}

export function intentLabel(intent: Intent | string): string {
  return intentMap[intent] || intent
}

const sourceMap: Record<string, string> = {
  ai: '🤖 Agent',
  faq: '📚 知识库',
  human: '👤 人工客服',
  system: '🗄️ 系统查询',
}

export function sourceLabel(source: Source | string): string {
  return sourceMap[source] || source
}

const statusMap: Record<string, string> = {
  active: '在线',
  transferred: '已转人工',
  closed: '已结束',
}

export function statusLabel(status: SessionStatus | string): string {
  return statusMap[status] || status
}
