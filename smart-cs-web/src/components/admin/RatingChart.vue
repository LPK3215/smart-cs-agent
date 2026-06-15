<template>
  <div class="chart-card">
    <h3>评分分布</h3>
    <div class="bar-chart">
      <div v-for="n in 5" :key="n" class="bar-group">
        <div class="bar-value">{{ ratingDist[String(n)] || 0 }}</div>
        <div class="bar" :style="{ height: barHeight(n) + 'px', background: '#e6a23c' }"></div>
        <div class="bar-label">{{ n }}⭐</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ ratingDist: Record<string, number> }>()

function barHeight(n: number): number {
  const dist = props.ratingDist || {}
  const max = Math.max(...Object.values(dist), 1)
  return Math.max(((dist[String(n)] || 0) / max) * 150, 4)
}
</script>
