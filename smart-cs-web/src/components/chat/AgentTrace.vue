<template>
  <div v-if="trace.length > 0" class="trace-panel">
    <div v-for="(step, idx) in trace" :key="idx" class="trace-step" :class="step.type">
      <div class="step-icon">
        <template v-if="step.type === 'reasoning'">💭</template>
        <template v-else-if="step.type === 'tool_call'">🔧</template>
        <template v-else-if="step.type === 'tool_result'">✅</template>
      </div>
      <div class="step-content">
        <div class="step-label">
          <template v-if="step.type === 'reasoning'">推理</template>
          <template v-else-if="step.type === 'tool_call'">调用 {{ step.tool }}</template>
          <template v-else-if="step.type === 'tool_result'">{{ step.tool }} 返回</template>
        </div>
        <div v-if="step.type === 'reasoning'" class="step-detail">{{ step.thought }}</div>
        <div v-if="step.input && Object.keys(step.input).length > 0" class="step-detail">
          输入: {{ JSON.stringify(step.input) }}
        </div>
        <div v-if="step.output" class="step-detail">
          {{ typeof step.output === 'string' ? step.output : JSON.stringify(step.output) }}
        </div>
        <div v-if="step.duration_ms" class="step-detail">耗时: {{ step.duration_ms }}ms</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TraceStep } from '@/types'

defineProps<{ trace: TraceStep[] }>()
</script>
