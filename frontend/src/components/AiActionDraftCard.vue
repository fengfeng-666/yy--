<script setup lang="ts">
import { computed } from 'vue'

import type { AiActionDraft } from '@/types/aiChat'

const props = defineProps<{
  draft: AiActionDraft
  loading?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const statusText = computed(() => {
  if (props.draft.status === 'confirmed') return '已生成购物清单'
  if (props.draft.status === 'cancelled') return '已取消'
  return '待确认'
})
</script>

<template>
  <div class="space-y-3 rounded-[22px] bg-[var(--yy-apricot)]/10 px-4 py-4 shadow-sm">
    <div class="flex items-center justify-between gap-3">
      <div>
        <p class="text-sm font-semibold text-[var(--yy-ink)]">{{ draft.title }}</p>
        <p class="mt-1 text-xs text-[var(--yy-muted)]">{{ draft.summary || '确认后将生成购物清单。' }}</p>
      </div>
      <span class="rounded-full bg-white px-3 py-1 text-[11px] text-[var(--yy-tomato)]">{{ statusText }}</span>
    </div>

    <div class="space-y-2">
      <div
        v-for="item in draft.items"
        :key="`${item.name}-${item.source_dish_name ?? ''}`"
        class="rounded-2xl bg-white px-3 py-2"
      >
        <p class="text-sm font-medium text-[var(--yy-ink)]">{{ item.name }}</p>
        <p v-if="item.source_dish_name || item.note" class="mt-1 text-xs text-[var(--yy-muted)]">
          {{ item.source_dish_name ? `来源：${item.source_dish_name}` : '' }}
          {{ item.source_dish_name && item.note ? ' · ' : '' }}
          {{ item.note || '' }}
        </p>
      </div>
    </div>

    <div v-if="draft.status === 'pending'" class="flex gap-2">
      <button
        type="button"
        class="flex-1 rounded-full bg-[var(--yy-tomato)] px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
        :disabled="loading"
        @click="emit('confirm')"
      >
        {{ loading ? '处理中...' : '确认生成购物清单' }}
      </button>
      <button
        type="button"
        class="rounded-full bg-white px-4 py-2.5 text-sm text-[var(--yy-muted)]"
        :disabled="loading"
        @click="emit('cancel')"
      >
        取消
      </button>
    </div>
  </div>
</template>
