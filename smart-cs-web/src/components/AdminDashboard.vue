<template>
  <div class="admin-container">
    <div class="admin-header">
      <h2>📊 管理后台</h2>
      <p>ReAct Agent × 工具调用审计 × 对话数据分析</p>
    </div>

    <!-- Stat Cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="label">总会话数</div>
        <div class="value">{{ stats.totalSessions }}</div>
      </div>
      <div class="stat-card">
        <div class="label">总消息数</div>
        <div class="value">{{ stats.totalMessages }}</div>
      </div>
      <div class="stat-card">
        <div class="label">平均满意度</div>
        <div class="value" style="color: #e6a23c;">{{ stats.avgRating || '-' }} <span style="font-size:14px;">⭐</span></div>
        <div class="change" :class="parseFloat(stats.avgRating) >= 4 ? 'up' : 'down'">
          {{ stats.ratingCount }} 次评价
        </div>
      </div>
      <div class="stat-card">
        <div class="label">转人工率</div>
        <div class="value" style="color: #f56c6c;">{{ stats.transferRate }}%</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="chart-grid">
      <div class="chart-card">
        <h3>意图类型分布</h3>
        <div class="bar-chart">
          <div v-for="(item, idx) in intentChartData" :key="idx" class="bar-group">
            <div class="bar-value">{{ item.count }}</div>
            <div class="bar" :style="{ height: barHeight(item.count) + 'px', background: barColors[idx % barColors.length] }"></div>
            <div class="bar-label">{{ item.label }}</div>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>响应来源分布</h3>
        <div class="donut-chart">
          <svg class="donut-svg" viewBox="0 0 42 42">
            <circle v-for="(seg, idx) in donutSegments" :key="idx"
                    cx="21" cy="21" r="15.91549430918954"
                    fill="transparent" stroke="#e9ecef" stroke-width="3"
                    :stroke-dasharray="seg.dashArray" :stroke-dashoffset="seg.offset"
                    :stroke="seg.color" stroke-linecap="round" />
          </svg>
          <div class="donut-legend">
            <div class="donut-legend-item" v-for="(item, idx) in sourceLegend" :key="idx">
              <span class="dot" :style="{ background: item.color }"></span>
              <span>{{ item.label }}：{{ item.count }} ({{ item.pct }}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>评分分布</h3>
        <div class="bar-chart">
          <div v-for="n in 5" :key="n" class="bar-group">
            <div class="bar-value">{{ stats.ratingDist[String(n)] || 0 }}</div>
            <div class="bar" :style="{ height: ratingBarHeight(n) + 'px', background: '#e6a23c' }"></div>
            <div class="bar-label">{{ n }}⭐</div>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>各意图解决率</h3>
        <div style="padding-top: 10px;">
          <div v-for="(item, idx) in resolutionData" :key="idx" style="margin-bottom: 12px;">
            <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
              <span>{{ item.label }}</span>
              <span style="color:#67c23a;font-weight:600;">{{ item.rate }}%</span>
            </div>
            <div style="height:8px;background:#f0f0f0;border-radius:4px;overflow:hidden;">
              <div :style="{ width: item.rate + '%', height: '100%', background: '#67c23a', borderRadius: '4px', transition: 'width 0.5s' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tool Stats -->
    <div class="chart-card" style="margin-bottom: 24px;" v-if="Object.keys(stats.toolStats || {}).length > 0">
      <h3>🔧 工具调用统计</h3>
      <div class="conv-table">
        <table>
          <thead>
            <tr>
              <th>工具名称</th>
              <th>调用次数</th>
              <th>平均耗时</th>
              <th>错误次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(stat, name) in stats.toolStats" :key="name">
              <td><strong>{{ name }}</strong></td>
              <td>{{ stat.count }}</td>
              <td>{{ stat.count > 0 ? (stat.total_ms / stat.count).toFixed(0) : 0 }}ms</td>
              <td :style="{ color: stat.errors > 0 ? '#f56c6c' : '' }">{{ stat.errors }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Conversation History -->
    <div class="chart-card" style="margin-bottom: 24px;">
      <h3>对话记录</h3>
      <div class="filter-bar">
        <select v-model="filterIntent">
          <option value="">全部意图</option>
          <option value="refund">退款申请</option>
          <option value="order">订单查询</option>
          <option value="tech">技术支持</option>
          <option value="faq">常见问题</option>
          <option value="human">转人工</option>
          <option value="unknown">未识别</option>
        </select>
        <select v-model="filterStatus">
          <option value="">全部状态</option>
          <option value="active">进行中</option>
          <option value="transferred">已转人工</option>
          <option value="closed">已结束</option>
        </select>
        <button style="padding:6px 14px;border:1px solid var(--border);border-radius:6px;background:var(--card);cursor:pointer;font-size:13px;" @click="loadAnalytics">刷新数据</button>
      </div>
      <div class="conv-table">
        <table>
          <thead>
            <tr>
              <th>会话</th>
              <th>用户</th>
              <th>意图</th>
              <th>状态</th>
              <th>消息数</th>
              <th>最后更新</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.session.id">
              <td>{{ row.session.title }}</td>
              <td style="font-size:12px;color:var(--text-muted);">{{ row.session.user_id }}</td>
              <td>
                <span v-for="intent in row.intents" :key="intent" class="intent-badge" :class="'intent-' + intent" style="margin-right:4px;">
                  {{ intentLabel(intent) }}
                </span>
                <span v-if="row.intents.length === 0" style="font-size:12px;color:var(--text-muted);">-</span>
              </td>
              <td>
                <span :class="'status-tag-' + row.session.status">{{ statusLabel(row.session.status) }}</span>
              </td>
              <td>{{ row.msgCount }}</td>
              <td style="font-size:12px;">{{ formatTime(row.session.updated_at) }}</td>
              <td><span class="expand-btn" @click="showDetail(row.session.id)">查看详情</span></td>
            </tr>
          </tbody>
        </table>
        <div v-if="filteredRows.length === 0" style="text-align:center;padding:30px;color:var(--text-muted);">
          暂无匹配的对话记录
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { fetchAnalytics, fetchMessages } from '../utils/api.js'

export default {
  name: 'AdminDashboard',
  setup() {
    const stats = ref({
      totalSessions: 0, totalMessages: 0, intentCounts: {}, sourceCounts: {},
      statusCounts: {}, avgRating: '0', ratingDist: {}, ratingCount: 0,
      intentResolution: {}, transferRate: '0', toolStats: {}, sessions: [], allMsgs: {}
    })
    const filterIntent = ref('')
    const filterStatus = ref('')

    onMounted(() => { loadAnalytics() })

    async function loadAnalytics() {
      try { stats.value = await fetchAnalytics() }
      catch (e) { console.error('Failed to load analytics:', e) }
    }

    const intentChartData = computed(() => {
      const counts = stats.value.intentCounts
      const labels = { refund: '退款', order: '订单', tech: '技术', faq: '常见', human: '转人工', unknown: '未知' }
      return Object.entries(counts).map(([k, v]) => ({ label: labels[k] || k, count: v })).sort((a, b) => b.count - a.count)
    })

    const barColors = ['#4f6ef7', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#409eff']
    function barHeight(count) {
      const max = Math.max(...intentChartData.value.map(d => d.count), 1)
      return Math.max((count / max) * 150, 8)
    }

    const sourceLegend = computed(() => {
      const s = stats.value.sourceCounts
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
        const pct = l.count / total * 100
        const seg = { dashArray: `${pct} ${100 - pct}`, offset, color: l.color }
        offset -= pct
        return seg
      })
    })

    function ratingBarHeight(n) {
      const dist = stats.value.ratingDist || {}
      const max = Math.max(...Object.values(dist), 1)
      return Math.max(((dist[String(n)] || 0) / max) * 150, 4)
    }

    const resolutionData = computed(() => {
      const r = stats.value.intentResolution
      const labels = { refund: '退款申请', order: '订单查询', tech: '技术支持', faq: '常见问题', human: '转人工' }
      return Object.entries(r).map(([k, v]) => ({ label: labels[k] || k, rate: v.total ? (v.resolved / v.total * 100).toFixed(0) : 0 }))
    })

    const tableRows = computed(() => {
      return stats.value.sessions.map(s => {
        const msgs = stats.value.allMsgs[s.id] || []
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

    function intentLabel(intent) {
      const map = { refund: '💰 退款', order: '📦 订单', tech: '🔧 技术', faq: '❓ 常见', human: '👤 转人工', unknown: '❔ 未知' }
      return map[intent] || intent
    }
    function statusLabel(status) {
      const map = { active: '进行中', transferred: '已转人工', closed: '已结束' }
      return map[status] || status
    }
    function formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    function showDetail(sessionId) {
      window.dispatchEvent(new CustomEvent('show-detail', { detail: sessionId }))
    }

    return {
      stats, intentChartData, barColors, barHeight, sourceLegend, donutSegments,
      ratingBarHeight, resolutionData, tableRows, filteredRows,
      filterIntent, filterStatus,
      intentLabel, statusLabel, formatTime, showDetail, loadAnalytics
    }
  }
}
</script>

<style scoped>
.status-tag-active { color: #67c23a; font-size: 12px; }
.status-tag-transferred { color: #e6a23c; font-size: 12px; }
.status-tag-closed { color: #909399; font-size: 12px; }
</style>
