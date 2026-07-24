<script setup lang="ts">
import { computed } from 'vue'

import type { AiRecommendationItem } from '@/types/aiChat'

const props = defineProps<{
  recommendation: AiRecommendationItem
}>()

const ratingText = computed(
  () => `${'★'.repeat(props.recommendation.rating)}${'☆'.repeat(5 - props.recommendation.rating)}`,
)
</script>

<template>
  <article class="rounded-[24px] border border-[var(--yy-line)] bg-[var(--yy-cream)]/70 p-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="text-sm font-semibold text-[var(--yy-ink)]">{{ recommendation.dish_name }}</h3>
        <p class="mt-1 text-xs tracking-[0.12em] text-[var(--yy-tomato)]">{{ ratingText }}</p>
      </div>
      <span class="rounded-full bg-white px-3 py-1 text-[11px] text-[var(--yy-muted)]">AI 推荐</span>
    </div>

    <p v-if="recommendation.reason" class="mt-3 text-xs leading-5 text-[var(--yy-muted)]">
      {{ recommendation.reason }}
    </p>

    <div v-if="recommendation.required_ingredients.length" class="mt-3">
      <p class="mt-2 text-xs leading-5 text-[var(--yy-ink)]">
        需要：{{ recommendation.required_ingredients.slice(0, 6).join('、') }}
      </p>
    </div>
  </article>
</template>
