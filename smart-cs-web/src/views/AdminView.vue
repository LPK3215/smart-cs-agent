<template>
  <div class="admin-page">
    <div class="admin-header">
      <h2>📊 管理后台</h2>
      <p>ReAct Agent × 工具调用审计 × 对话数据分析</p>
    </div>

    <!-- Stat Cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="label">总会话数</div>
        <div class="value">{{ store.analytics.totalSessions }}</div>
      </div>
      <div class="stat-card">
        <div class="label">总消息数</div>
        <div class="value">{{ store.analytics.totalMessages }}</div>
      </div>
      <div class="stat-card">
        <div class="label">平均满意度</div>
        <div class="value" style="color: #e6a23c">
          {{ store.analytics.avgRating || '-' }} <span style="font-size: 14px">⭐</span>
        </div>
        <div class="change" :class="parseFloat(store.analytics.avgRating) >= 4 ? 'up' : 'down'">
          {{ store.analytics.ratingCount }} 次评价
        </div>
      </div>
      <div class="stat-card">
        <div class="label">转人工率</div>
        <div class="value" style="color: #f56c6c">{{ store.analytics.transferRate }}%</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="chart-grid">
      <div class="chart-card">
        <h3>意图类型分布</h3>
        <div class="bar-chart">
          <div v-for="(item, idx) in store.intentChartData" :key="idx" class="bar-group">
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
            <circle
              v-for="(seg, idx) in store.donutSegments"
              :key="idx"
              cx="21" cy="21" r="15.91549430918954"
              fill="transparent" stroke="#e9ecef" stroke-width="3"
              :stroke-dasharray="seg.dashArray" :stroke-dashoffset="seg.offset"
              :stroke="seg.color" stroke-linecap="round"
            />
          </svg>
          <div class="donut-legend">
            <div class="donut-legend-item" v-for="(item, idx) in store.sourceLegend" :key="idx">
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
            <div class="bar-value">{{ store.analytics.ratingDist[String(n)] || 0 }}</div>
            <div class="bar" :style="{ height: ratingBarHeight(n) + 'px', background: '#e6a23c' }"></div>
            <div class="bar-label">{{ n }}⭐</div>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>各意图解决率</h3>
        <div style="padding-top: 10px">
          <div v-for="(item, idx) in store.resolutionData" :key="idx" style="margin-bottom: 12px">
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px">
              <span>{{ item.label }}</span>
              <span style="color: #67c23a; font-weight: 600">{{ item.rate }}%</span>
            </div>
            <div style="height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden">
              <div :style="{ width: item.rate + '%', height: '100%', background: '#67c23a', borderRadius: '4px', transition: 'width 0.5s' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tool Stats -->
    <div class="chart-card" style="margin-bottom: 24px" v-if="Object.keys(store.analytics.toolStats || {}).length > 0">
      <h3>🔧 工具调用统计</h3>
      <div class="conv-table">
        <table>
          <thead>
            <tr><th>工具名称</th><th>调用次数</th><th>平均耗时</th><th>错误次数</th></tr>
          </thead>
          <tbody>
            <tr v-for="(stat, name) in store.analytics.toolStats" :key="name">
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
    <div class="chart-card" style="margin-bottom: 24px">
      <h3>对话记录</h3>
      <div class="filter-bar">
        <select v-model="store.filterIntent">
          <option value="">全部意图</option>
          <option value="refund">退款申请</option>
          <option value="order">订单查询</option>
          <option value="tech">技术支持</option>
          <option value="faq">常见问题</option>
          <option value="human">转人工</option>
          <option value="unknown">未识别</option>
        </select>
        <select v-model="store.filterStatus">
          <option value="">全部状态</option>
          <option value="active">进行中</option>
          <option value="transferred">已转人工</option>
          <option value="closed">已结束</option>
        </select>
        <button class="refresh-btn" @click="store.loadAnalytics()">刷新数据</button>
      </div>
      <div class="conv-table">
        <table>
          <thead>
            <tr><th>会话</th><th>用户</th><th>意图</th><th>状态</th><th>消息数</th><th>最后更新</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in store.filteredRows" :key="row.session.id">
              <td>{{ row.session.title }}</td>
              <td style="font-size: 12px; color: var(--text-muted)">{{ row.session.user_id }}</td>
              <td>
                <span v-for="intent in row.intents" :key="intent" class="intent-badge" :class="'intent-' + intent" style="margin-right: 4px">
                  {{ intentLabel(intent) }}
                </span>
                <span v-if="row.intents.length === 0" style="font-size: 12px; color: var(--text-muted)">-</span>
              </td>
              <td><span :class="'status-tag-' + row.session.status">{{ statusLabel(row.session.status) }}</span></td>
              <td>{{ row.msgCount }}</td>
              <td style="font-size: 12px">{{ formatTime(row.session.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="store.filteredRows.length === 0" style="text-align: center; padding: 30px; color: var(--text-muted)">暂无匹配的对话记录</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { formatTime, intentLabel, sourceLabel, statusLabel } from '@/utils/format'

const store = useAdminStore()

const barColors = ['#4f6ef7', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#409eff']

function barHeight(count: number): number {
  const max = Math.max(...store.intentChartData.map(d => d.count), 1)
  return Math.max((count / max) * 150, 8)
}

function ratingBarHeight(n: number): number {
  const dist = store.analytics.ratingDist || {}
  const max = Math.max(...Object.values(dist), 1)
  return Math.max(((dist[String(n)] || 0) / max) * 150, 4)
}

onMounted(() => {
  store.loadAnalytics()
})
</script>

<style scoped>
.admin-page {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.admin-header { margin-bottom: 20px; }
.admin-header h2 { font-size: 20px; font-weight: 600; }
.admin-header p { color: var(--text-muted); font-size: 13px; margin-top: 4px; }

.refresh-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--card);
  cursor: pointer;
  font-size: 13px;
}
.refresh-btn:hover { border-color: var(--primary); color: var(--primary); }

.status-tag-active { color: #67c23a; font-size: 12px; }
.status-tag-transferred { color: #e6a23c; font-size: 12px; }
.status-tag-closed { color: #909399; font-size: 12px; }
</style>
