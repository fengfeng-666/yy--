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

    <div v-if="recommendation.matched_ingredients.length" class="mt-3">
      <p class="text-[11px] font-medium uppercase tracking-[0.16em] text-[var(--yy-muted)]">匹配食材</p>
      <div class="mt-2 flex flex-wrap gap-2">
        <span
          v-for="ingredient in recommendation.matched_ingredients"
          :key="ingredient"
          class="rounded-full bg-[var(--yy-apricot)]/20 px-3 py-1 text-xs text-[var(--yy-tomato)]"
        >
          {{ ingredient }}
        </span>
      </div>
    </div>

    <div v-if="recommendation.required_ingredients.length" class="mt-3">
      <p class="text-[11px] font-medium uppercase tracking-[0.16em] text-[var(--yy-muted)]">所需食材</p>
      <p class="mt-2 text-xs leading-5 text-[var(--yy-ink)]">
        {{ recommendation.required_ingredients.join('、') }}
      </p>
    </div>

    <div v-if="recommendation.steps.length" class="mt-3">
      <p class="text-[11px] font-medium uppercase tracking-[0.16em] text-[var(--yy-muted)]">做法</p>
      <ol class="mt-2 space-y-1.5 text-xs leading-5 text-[var(--yy-ink)]">
        <li v-for="(step, index) in recommendation.steps" :key="`${recommendation.dish_name}-${index}`">
          {{ index + 1 }}. {{ step }}
        </li>
      </ol>
    </div>
  </article>
</template>
