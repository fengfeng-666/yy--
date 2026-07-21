<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useAppStore } from '@/stores/app'
import { useFamilyStore } from '@/stores/family'

const appStore = useAppStore()
const familyStore = useFamilyStore()
const { welcomeText, userNickname, familyName } = storeToRefs(appStore)
const { members } = storeToRefs(familyStore)
</script>

<template>
  <section class="space-y-6 px-5 pb-8 pt-6">
    <div class="rounded-[28px] bg-[linear-gradient(135deg,_rgba(242,172,114,0.92),_rgba(232,122,85,0.88))] p-6 text-white shadow-[0_24px_60px_rgba(232,122,85,0.28)]">
      <p class="text-sm tracking-[0.24em] text-white/75">YY 私厨</p>
      <div class="mt-3 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold">{{ welcomeText }}</h1>
          <p class="mt-2 max-w-[240px] text-sm leading-6 text-white/85">
            {{ familyName }} · 把“点菜、做饭、评价”串成一个温暖的小闭环。
          </p>
        </div>
        <div class="rounded-full border border-white/30 bg-white/15 px-3 py-2 text-xs">
          {{ members.length }}/2 成员
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <article class="rounded-[24px] bg-white p-4 shadow-[0_16px_40px_rgba(87,64,46,0.08)]">
        <p class="text-xs text-[var(--yy-muted)]">待处理点菜</p>
        <p class="mt-3 text-3xl font-semibold text-[var(--yy-ink)]">2</p>
        <p class="mt-2 text-sm text-[var(--yy-muted)]">其中 1 个需要你确认</p>
      </article>
      <article class="rounded-[24px] bg-white p-4 shadow-[0_16px_40px_rgba(87,64,46,0.08)]">
        <p class="text-xs text-[var(--yy-muted)]">本月一起吃饭</p>
        <p class="mt-3 text-3xl font-semibold text-[var(--yy-ink)]">18</p>
        <p class="mt-2 text-sm text-[var(--yy-muted)]">最受欢迎：糖醋排骨</p>
      </article>
    </div>

    <article class="rounded-[28px] border border-[var(--yy-line)] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-[var(--yy-muted)]">今日菜单</p>
          <h2 class="mt-1 text-lg font-semibold text-[var(--yy-ink)]">糖醋排骨 + 清炒生菜</h2>
        </div>
        <span class="rounded-full bg-amber-50 px-3 py-1 text-xs text-amber-700">待确认</span>
      </div>
      <div class="mt-4 rounded-2xl bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-muted)]">
        负责人：{{ userNickname }} · 预计 19:00 上菜
      </div>
    </article>

    <article class="rounded-[28px] border border-[var(--yy-line)] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-[var(--yy-ink)]">快捷入口</h2>
        <span class="text-sm text-[var(--yy-muted)]">今天也好好吃饭</span>
      </div>
      <div class="mt-4 grid grid-cols-2 gap-3">
        <button type="button" class="rounded-2xl bg-[var(--yy-apricot)]/18 px-4 py-4 text-left text-sm font-medium text-[var(--yy-ink)]">
          发起点菜
        </button>
        <button type="button" class="rounded-2xl bg-[var(--yy-sage)]/16 px-4 py-4 text-left text-sm font-medium text-[var(--yy-ink)]">
          随机选菜
        </button>
        <button type="button" class="rounded-2xl bg-[var(--yy-tomato)]/10 px-4 py-4 text-left text-sm font-medium text-[var(--yy-ink)]">
          安排一周
        </button>
        <button type="button" class="rounded-2xl bg-[var(--yy-cream-deep)] px-4 py-4 text-left text-sm font-medium text-[var(--yy-ink)]">
          添加菜品
        </button>
      </div>
    </article>
  </section>
</template>
