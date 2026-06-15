<template>
  <div class="chart-card">
    <h3>响应来源分布</h3>
    <div class="donut-chart" v-if="legend.length > 0">
      <svg class="donut-svg" viewBox="0 0 42 42">
        <circle
          v-for="(seg, idx) in segments"
          :key="idx"
          cx="21" cy="21" r="15.91549430918954"
          fill="transparent" stroke="#e9ecef" stroke-width="3"
          :stroke-dasharray="seg.dashArray" :stroke-dashoffset="seg.offset"
          :stroke="seg.color" stroke-linecap="round"
        />
      </svg>
      <div class="donut-legend">
        <div class="donut-legend-item" v-for="(item, idx) in legend" :key="idx">
          <span class="dot" :style="{ background: item.color }"></span>
          <span>{{ item.label }}：{{ item.count }} ({{ item.pct }}%)</span>
        </div>
      </div>
    </div>
    <div v-else style="text-align:center;padding:40px;color:var(--text-muted);">暂无数据</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  sourceCounts: Record<string, number>
}>()

const legend = computed(() => {
  const s = props.sourceCounts
  const total = (s.ai || 0) + (s.faq || 0) + (s.human || 0) + (s.system || 0)
  if (total === 0) return []
  return [
    { label: '🤖 Agent', count: s.ai || 0, pct: ((s.ai || 0) / total * 100).toFixed(0), color: '#409eff' },
    { label: '📚 知识库', count: s.faq || 0, pct: ((s.faq || 0) / total * 100).toFixed(0), color: '#67c23a' },
    { label: '🗄️ 系统查询', count: s.system || 0, pct: ((s.system || 0) / total * 100).toFixed(0), color: '#606266' },
    { label: '👤 人工客服', count: s.human || 0, pct: ((s.human || 0) / total * 100).toFixed(0), color: '#e6a23c' },
  ]
})

const segments = computed(() => {
  const total = legend.value.reduce((s, l) => s + l.count, 0)
  if (total === 0) return []
  let offset = 25
  return legend.value.map(l => {
    const pct = (l.count / total) * 100
    const seg = { dashArray: `${pct} ${100 - pct}`, offset, color: l.color }
    offset -= pct
    return seg
  })
})
</script>
