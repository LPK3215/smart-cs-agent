<template>
  <div class="stat-cards">
    <div class="stat-card">
      <div class="label">总会话数</div>
      <div class="value">{{ totalSessions }}</div>
    </div>
    <div class="stat-card">
      <div class="label">总消息数</div>
      <div class="value">{{ totalMessages }}</div>
    </div>
    <div class="stat-card">
      <div class="label">平均满意度</div>
      <div class="value" style="color: #e6a23c;">
        {{ avgRating || '-' }} <span style="font-size:14px;">⭐</span>
      </div>
      <div class="change" :class="avgRating >= 4 ? 'up' : 'down'">
        {{ ratingCount }} 次评价
      </div>
    </div>
    <div class="stat-card">
      <div class="label">转人工率</div>
      <div class="value" style="color: #f56c6c;">{{ transferRate }}%</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  totalSessions: number
  totalMessages: number
  avgRating: number
  ratingCount: number
  transferRate: number
}>()
</script>
