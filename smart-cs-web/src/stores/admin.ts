import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AnalyticsData } from '@/types'
import * as api from '@/utils/api'
import { intentLabel } from '@/utils/format'

export const useAdminStore = defineStore('admin', () => {
  const analytics = ref<AnalyticsData>({
    totalSessions: 0,
    totalMessages: 0,
    intentCounts: {},
    sourceCounts: {},
    statusCounts: {},
    avgRating: '0',
    ratingDist: {},
    ratingCount: 0,
    intentResolution: {},
    transferRate: '0',
    toolStats: {},
    sessions: [],
    allMsgs: {},
  })
  const isLoading = ref(false)
  const filterIntent = ref('')
  const filterStatus = ref('')

  async function loadAnalytics() {
    isLoading.value = true
    try {
      analytics.value = await api.fetchAnalytics()
    } catch (e) {
      console.error('Failed to load analytics:', e)
    } finally {
      isLoading.value = false
    }
  }

  const intentChartData = computed(() => {
    const counts = analytics.value.intentCounts
    return Object.entries(counts)
      .map(([k, v]) => ({ label: intentLabel(k), count: v }))
      .sort((a, b) => b.count - a.count)
  })

  const sourceLegend = computed(() => {
    const s = analytics.value.sourceCounts
    const total = (s.ai || 0) + (s.faq || 0) + (s.human || 0) + (s.system || 0)
    if (total === 0) return []
    return [
      { label: '🤖 Agent', count: s.ai || 0, pct: ((s.ai || 0) / total * 100).toFixed(0), color: '#409eff' },
      { label: '📚 知识库', count: s.faq || 0, pct: ((s.faq || 0) / total * 100).toFixed(0), color: '#67c23a' },
      { label: '🗄️ 系统查询', count: s.system || 0, pct: ((s.system || 0) / total * 100).toFixed(0), color: '#606266' },
      { label: '👤 人工客服', count: s.human || 0, pct: ((s.human || 0) / total * 100).toFixed(0), color: '#e6a23c' },
    ]
  })

  const donutSegments = computed(() => {
    const legend = sourceLegend.value
    const total = legend.reduce((s, l) => s + l.count, 0)
    if (total === 0) return []
    let offset = 25
    return legend.map(l => {
      const pct = (l.count / total) * 100
      const seg = { dashArray: `${pct} ${100 - pct}`, offset, color: l.color }
      offset -= pct
      return seg
    })
  })

  const resolutionData = computed(() => {
    const r = analytics.value.intentResolution
    const labels: Record<string, string> = { refund: '退款申请', order: '订单查询', tech: '技术支持', faq: '常见问题', human: '转人工' }
    return Object.entries(r).map(([k, v]) => ({
      label: labels[k] || k,
      rate: v.total ? ((v.resolved / v.total) * 100).toFixed(0) : '0',
    }))
  })

  const tableRows = computed(() => {
    return analytics.value.sessions.map(s => {
      const msgs = analytics.value.allMsgs[s.id] || []
      const intents = [...new Set(msgs.filter(m => m.intent).map(m => m.intent))]
      return { session: s, intents, msgCount: msgs.length }
    })
  })

  const filteredRows = computed(() => {
    let rows = tableRows.value
    if (filterIntent.value) rows = rows.filter(r => r.intents.includes(filterIntent.value))
    if (filterStatus.value) rows = rows.filter(r => r.session.status === filterStatus.value)
    return rows
  })

  return {
    analytics, isLoading, filterIntent, filterStatus,
    intentChartData, sourceLegend, donutSegments, resolutionData, tableRows, filteredRows,
    loadAnalytics,
  }
})
