<script setup lang="ts">
import type { AiToolCallTrace } from '@/types/aiChat'

defineProps<{
  traces: AiToolCallTrace[]
}>()
</script>

<template>
  <div class="space-y-2 rounded-[22px] bg-white px-4 py-3 shadow-sm">
    <p class="text-[11px] font-medium uppercase tracking-[0.16em] text-[var(--yy-muted)]">Agent 工具</p>
    <div class="space-y-2">
      <div
        v-for="trace in traces"
        :key="trace.tool_name"
        class="rounded-2xl border border-[var(--yy-line)] px-3 py-2.5"
      >
        <p class="text-sm font-semibold text-[var(--yy-ink)]">{{ trace.tool_name }}</p>
        <p class="mt-1 text-xs leading-5 text-[var(--yy-muted)]">{{ trace.summary }}</p>
      </div>
    </div>
  </div>
</template>
