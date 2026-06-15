<template>
  <div class="admin-page" v-loading="store.isLoading">
    <div class="admin-header">
      <h2>📊 管理后台</h2>
      <p>ReAct Agent × 工具调用审计 × 对话数据分析</p>
    </div>

    <StatCards
      :total-sessions="store.analytics.totalSessions"
      :total-messages="store.analytics.totalMessages"
      :avg-rating="store.analytics.avgRating"
      :rating-count="store.analytics.ratingCount"
      :transfer-rate="store.analytics.transferRate"
    />

    <div class="chart-grid">
      <IntentChart :data="store.intentChartData" />
      <SourceDonut :source-counts="store.analytics.sourceCounts" />
      <RatingChart :rating-dist="store.analytics.ratingDist" />
      <ResolutionBars :data="store.resolutionData" />
    </div>

    <ToolStatsTable :tool-stats="store.analytics.toolStats || {}" />

    <ConversationTable
      :rows="store.filteredRows"
      :filter-intent="store.filterIntent"
      :filter-status="store.filterStatus"
      @update:filter-intent="val => store.filterIntent = val"
      @update:filter-status="val => store.filterStatus = val"
      @refresh="store.loadAnalytics()"
      @view-session="openSessionDetail"
    />

    <SessionDetailModal v-model:visible="modalVisible" :session-id="modalSessionId" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import StatCards from '@/components/admin/StatCards.vue'
import IntentChart from '@/components/admin/IntentChart.vue'
import SourceDonut from '@/components/admin/SourceDonut.vue'
import RatingChart from '@/components/admin/RatingChart.vue'
import ResolutionBars from '@/components/admin/ResolutionBars.vue'
import ToolStatsTable from '@/components/admin/ToolStatsTable.vue'
import ConversationTable from '@/components/admin/ConversationTable.vue'
import SessionDetailModal from '@/components/chat/SessionDetailModal.vue'

const store = useAdminStore()
const modalVisible = ref(false)
const modalSessionId = ref<string | null>(null)

function openSessionDetail(sessionId: string) {
  modalSessionId.value = sessionId
  modalVisible.value = true
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
</style>
