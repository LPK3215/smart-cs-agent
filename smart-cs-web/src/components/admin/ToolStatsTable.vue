<template>
  <div class="chart-card" style="margin-bottom: 24px;" v-if="Object.keys(toolStats).length > 0">
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
          <tr v-for="(stat, name) in toolStats" :key="name">
            <td><strong>{{ name }}</strong></td>
            <td>{{ stat.count }}</td>
            <td>{{ stat.count > 0 ? (stat.total_ms / stat.count).toFixed(0) : 0 }}ms</td>
            <td :style="{ color: stat.errors > 0 ? '#f56c6c' : '' }">{{ stat.errors }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  toolStats: Record<string, { count: number; total_ms: number; errors: number }>
}>()
</script>
