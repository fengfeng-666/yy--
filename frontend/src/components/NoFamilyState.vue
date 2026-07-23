<script setup lang="ts">
import { HousePlus, KeyRound } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '还没有加入家庭',
    description: '你可以先逛逛，准备好后再创建家庭，或者输入家人分享的邀请码加入。',
  },
)

const router = useRouter()

function openFamilyOnboarding(mode: 'create' | 'join') {
  router.push({ name: 'family-onboarding', query: { mode } })
}
</script>

<template>
  <article class="yy-card overflow-hidden p-6 text-center">
    <span class="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]">
      <HousePlus class="h-7 w-7" :stroke-width="1.8" />
    </span>
    <h2 class="yy-display mt-5 text-2xl font-bold text-[var(--yy-ink)]">{{ title }}</h2>
    <p class="mx-auto mt-2 max-w-[320px] text-sm leading-6 text-[var(--yy-muted)]">{{ description }}</p>

    <div class="mt-6 grid grid-cols-2 gap-3">
      <button
        type="button"
        class="yy-primary-button rounded-2xl bg-[var(--yy-ink)] px-4 py-3.5 text-sm font-medium text-white"
        @click="openFamilyOnboarding('join')"
      >
        <KeyRound class="mr-1.5 inline h-4 w-4" />
        加入家庭
      </button>
      <button
        type="button"
        class="yy-soft-button rounded-2xl bg-[var(--yy-cream)] px-4 py-3.5 text-sm font-medium text-[var(--yy-ink)]"
        @click="openFamilyOnboarding('create')"
      >
        创建家庭
      </button>
    </div>
    <p class="mt-4 text-xs text-[var(--yy-muted)]">不想现在操作也没关系，之后可随时从“我的”进入。</p>
  </article>
</template>
