<script setup lang="ts">
import type { AiRetrievalSource } from '@/types/aiChat'

defineProps<{
  sources: AiRetrievalSource[]
}>()
</script>

<template>
  <div class="space-y-2 rounded-[22px] bg-white px-4 py-3 shadow-sm">
    <p class="text-[11px] font-medium uppercase tracking-[0.16em] text-[var(--yy-muted)]">推荐依据</p>
    <div class="space-y-2">
      <article
        v-for="(source, index) in sources"
        :key="`${source.source_type}-${source.source_id ?? index}`"
        class="rounded-2xl bg-[var(--yy-cream)] px-3 py-2.5"
      >
        <p class="text-sm font-semibold text-[var(--yy-ink)]">{{ source.title }}</p>
        <p class="mt-1 text-xs leading-5 text-[var(--yy-muted)]">{{ source.snippet }}</p>
      </article>
    </div>
  </div>
</template>
