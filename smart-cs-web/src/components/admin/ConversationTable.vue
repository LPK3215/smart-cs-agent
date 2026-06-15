<template>
  <div class="chart-card" style="margin-bottom: 24px;">
    <h3>对话记录</h3>
    <div class="filter-bar">
      <select :value="filterIntent" @change="$emit('update:filterIntent', ($event.target as HTMLSelectElement).value)">
        <option value="">全部意图</option>
        <option value="refund">退款申请</option>
        <option value="order">订单查询</option>
        <option value="tech">技术支持</option>
        <option value="faq">常见问题</option>
        <option value="human">转人工</option>
        <option value="unknown">未识别</option>
      </select>
      <select :value="filterStatus" @change="$emit('update:filterStatus', ($event.target as HTMLSelectElement).value)">
        <option value="">全部状态</option>
        <option value="active">进行中</option>
        <option value="transferred">已转人工</option>
        <option value="closed">已结束</option>
      </select>
      <button class="refresh-btn" @click="$emit('refresh')">刷新数据</button>
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
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.session.id" @click="$emit('viewSession', row.session.id)" style="cursor:pointer;">
            <td>{{ row.session.title }}</td>
            <td style="font-size:12px;color:var(--text-muted);">{{ row.session.user_id }}</td>
            <td>
              <span v-for="intent in row.intents" :key="intent" class="intent-badge" :class="'intent-' + intent" style="margin-right:4px;">
                {{ intentLabel(intent) }}
              </span>
              <span v-if="row.intents.length === 0" style="font-size:12px;color:var(--text-muted);">-</span>
            </td>
            <td><span :class="'status-tag-' + row.session.status">{{ statusLabel(row.session.status) }}</span></td>
            <td>{{ row.msgCount }}</td>
            <td style="font-size:12px;">{{ formatTime(row.session.updated_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="rows.length === 0" style="text-align:center;padding:30px;color:var(--text-muted);">
        暂无匹配的对话记录
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'
import { formatTime, intentLabel, statusLabel } from '@/utils/format'

defineProps<{
  rows: Array<{ session: Session; intents: string[]; msgCount: number }>
  filterIntent: string
  filterStatus: string
}>()

defineEmits<{
  'update:filterIntent': [val: string]
  'update:filterStatus': [val: string]
  'refresh': []
  'viewSession': [sessionId: string]
}>()
</script>

<style scoped>
.refresh-btn {
  padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--card); cursor: pointer; font-size: 13px;
}
.refresh-btn:hover { border-color: var(--primary); color: var(--primary); }
.status-tag-active { color: #67c23a; font-size: 12px; }
.status-tag-transferred { color: #e6a23c; font-size: 12px; }
.status-tag-closed { color: #909399; font-size: 12px; }
</style>
