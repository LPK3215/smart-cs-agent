<template>
  <div class="chat-input">
    <div class="input-row">
      <textarea
        v-model="inputText"
        :placeholder="placeholder"
        @keydown.enter.exact.prevent="handleSend"
        :disabled="disabled"
        rows="1"
        ref="textareaRef"
      ></textarea>
      <button class="send-btn" @click="handleSend" :disabled="!inputText.trim() || disabled">发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'

const props = defineProps<{
  disabled: boolean
  sessionStatus?: string
}>()

const emit = defineEmits<{ send: [text: string] }>()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const placeholder = computed(() => {
  if (props.sessionStatus === 'transferred') return '对话已转人工...'
  if (props.sessionStatus === 'closed') return '对话已结束'
  return '输入您的问题...'
})

function handleSend() {
  const text = inputText.value.trim()
  if (!text || props.disabled) return
  inputText.value = ''
  emit('send', text)
  nextTick(() => textareaRef.value?.focus())
}

function focus() {
  textareaRef.value?.focus()
}

defineExpose({ focus })
</script>
