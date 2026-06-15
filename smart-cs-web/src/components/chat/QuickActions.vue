<template>
  <div class="quick-actions">
    <span class="quick-btn" @click="$emit('quick-send', '如何申请退款？')">💰 退款申请</span>
    <span class="quick-btn" @click="$emit('quick-send', '查询我的订单')">📦 订单查询</span>
    <span class="quick-btn" @click="$emit('quick-send', 'APP闪退怎么办')">🔧 技术支持</span>
    <span class="quick-btn" @click="$emit('quick-send', '转人工客服')">👤 转人工</span>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ 'quick-send': [text: string] }>()
</script>
