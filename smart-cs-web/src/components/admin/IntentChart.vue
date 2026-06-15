<template>
  <div class="chart-card">
    <h3>意图类型分布</h3>
    <div class="bar-chart">
      <div v-for="(item, idx) in data" :key="idx" class="bar-group">
        <div class="bar-value">{{ item.count }}</div>
        <div class="bar" :style="{ height: barHeight(item.count) + 'px', background: colors[idx % colors.length] }"></div>
        <div class="bar-label">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  data: Array<{ label: string; count: number }>
}>()

const colors = ['#4f6ef7', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#409eff']

function barHeight(count: number): number {
  const max = Math.max(...props.data.map(d => d.count), 1)
  return Math.max((count / max) * 150, 8)
}
</script>
