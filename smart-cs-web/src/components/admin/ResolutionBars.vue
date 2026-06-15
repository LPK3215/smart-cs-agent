<template>
  <div class="chart-card">
    <h3>各意图解决率</h3>
    <div style="padding-top: 10px;">
      <div v-for="(item, idx) in data" :key="idx" style="margin-bottom: 12px;">
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
          <span>{{ item.label }}</span>
          <span style="color:#67c23a;font-weight:600;">{{ item.rate }}%</span>
        </div>
        <div style="height:8px;background:#f0f0f0;border-radius:4px;overflow:hidden;">
          <div :style="{ width: item.rate + '%', height: '100%', background: '#67c23a', borderRadius: '4px', transition: 'width 0.5s' }"></div>
        </div>
      </div>
      <div v-if="data.length === 0" style="text-align:center;padding:20px;color:var(--text-muted);">暂无数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ data: Array<{ label: string; rate: string }> }>()
</script>
