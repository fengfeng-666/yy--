<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast } from 'vant'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  CalendarDays,
  ChefHat,
  Clock3,
  CookingPot,
  Heart,
  History,
  MessageCircleHeart,
  Plus,
  Sparkles,
  UsersRound,
  UtensilsCrossed,
} from 'lucide-vue-next'

import { useAppStore } from '@/stores/app'
import { useFamilyStore } from '@/stores/family'
import NoFamilyState from '@/components/NoFamilyState.vue'

const router = useRouter()
const appStore = useAppStore()
const familyStore = useFamilyStore()
const { userNickname, familyName, homeSummary, homeLoading } = storeToRefs(appStore)
const { hasFamily, members } = storeToRefs(familyStore)

const todayOrder = computed(() => homeSummary.value?.today_order ?? null)
const recentHistory = computed(() => homeSummary.value?.recent_history ?? [])
const todayLabel = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date())
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 11) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

onMounted(async () => {
  if (!hasFamily.value) {
    return
  }
  try {
    await appStore.loadHomeSummary()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载首页数据失败')
  }
})

function formatTime(time: string | null | undefined) {
  return time ? time.slice(0, 5) : '待安排'
}

function orderSummary(order: { items: Array<{ dish: { name: string }; quantity: number }> }) {
  return order.items.map((item) => `${item.dish.name} × ${item.quantity}`).join('、')
}

function goToCreateOrder() {
  router.push('/orders/create')
}

function goToHistory() {
  router.push('/journal')
}

function goToDishes() {
  router.push('/dishes')
}

function goToOrderDetail(orderId: number) {
  router.push(`/orders/${orderId}`)
}
</script>

<template>
  <section class="yy-page space-y-7 pb-8 pt-5">
    <header class="yy-enter flex items-center justify-between gap-4 px-1">
      <div>
        <p class="yy-kicker">YY Private Kitchen</p>
        <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">
          {{ greeting }}，{{ userNickname }}
        </h1>
      </div>
      <div
        class="flex h-12 w-12 items-center justify-center rounded-full border border-[var(--yy-line)] bg-white/80 text-[var(--yy-tomato)] shadow-sm"
        aria-hidden="true"
      >
        <ChefHat class="h-6 w-6" :stroke-width="1.8" />
      </div>
    </header>

    <NoFamilyState
      v-if="!hasFamily"
      title="先从一张家庭餐桌开始"
      description="账号已经注册成功。加入家庭后，就能共享菜单、发起点菜和记录每一顿饭。"
    />

    <template v-else>
    <article
      class="yy-enter yy-enter-delay-1 relative isolate overflow-hidden rounded-[34px] bg-[var(--yy-ink)] p-6 text-white shadow-[0_28px_65px_rgba(48,37,31,0.26)]"
    >
      <div
        class="absolute -right-12 -top-16 h-52 w-52 rounded-full border-[38px] border-white/[0.035]"
        aria-hidden="true"
      ></div>
      <div
        class="absolute -bottom-20 -left-16 h-44 w-44 rounded-full bg-[var(--yy-tomato)]/20 blur-2xl"
        aria-hidden="true"
      ></div>

      <div class="relative z-10 flex items-center justify-between gap-3">
        <div class="inline-flex items-center gap-2 text-xs text-white/60">
          <CalendarDays class="h-4 w-4" />
          <span>{{ todayLabel }}</span>
        </div>
        <div class="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.07] px-3 py-1.5 text-xs text-white/70">
          <UsersRound class="h-3.5 w-3.5" />
          <span>{{ familyName }} · {{ members.length }} 人</span>
        </div>
      </div>

      <div class="relative z-10 mt-9 max-w-[300px]">
        <p class="text-xs font-medium tracking-[0.18em] text-[var(--yy-apricot-soft)]">TODAY'S TABLE</p>
        <h2 class="yy-display mt-3 text-[34px] font-bold leading-[1.18]">
          {{ todayOrder ? orderSummary(todayOrder) : '今天，想吃点什么？' }}
        </h2>
        <p class="mt-4 text-sm leading-6 text-white/58">
          <template v-if="todayOrder">
            {{ todayOrder.cook.nickname }} 掌勺，预计 {{ formatTime(todayOrder.planned_time) }} 开饭
          </template>
          <template v-else>
            一顿认真准备的饭，是平常日子里最小也最确定的期待。
          </template>
        </p>
      </div>

      <div class="relative z-10 mt-7 flex items-center gap-3">
        <button
          v-if="todayOrder"
          type="button"
          class="yy-primary-button inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-[var(--yy-ink)]"
          @click="goToOrderDetail(todayOrder.id)"
        >
          查看安排
          <ArrowRight class="h-4 w-4" />
        </button>
        <button
          v-else
          type="button"
          class="yy-primary-button inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-[var(--yy-ink)]"
          @click="goToCreateOrder"
        >
          <Plus class="h-4 w-4" />
          发起点菜
        </button>
        <span
          v-if="todayOrder"
          class="rounded-full border border-white/10 bg-white/[0.07] px-3 py-2 text-xs text-white/70"
        >
          {{ todayOrder.status === 'accepted' ? '已接单' : '等待确认' }}
        </span>
      </div>

      <CookingPot
        class="absolute bottom-7 right-5 h-20 w-20 text-white/[0.075]"
        :stroke-width="1.2"
        aria-hidden="true"
      />
    </article>

    <section class="yy-enter yy-enter-delay-2">
      <div class="mb-3 flex items-end justify-between px-1">
        <div>
          <p class="yy-kicker">At a glance</p>
          <h2 class="yy-display mt-1 text-[25px] font-bold text-[var(--yy-ink)]">家的用餐小记</h2>
        </div>
        <Sparkles class="mb-1 h-5 w-5 text-[var(--yy-apricot)]" aria-hidden="true" />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <article class="yy-card relative overflow-hidden p-5">
          <div class="flex items-center justify-between">
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-[#fff0e3] text-[var(--yy-tomato)]">
              <Clock3 class="h-[18px] w-[18px]" />
            </span>
            <span class="text-[11px] font-medium text-[var(--yy-muted)]">待处理</span>
          </div>
          <p class="yy-display mt-5 text-[38px] font-bold leading-none text-[var(--yy-ink)]">
            {{ homeSummary?.pending_orders_count ?? 0 }}
          </p>
          <p class="mt-2 text-xs leading-5 text-[var(--yy-muted)]">
            {{ homeSummary?.pending_to_me_count ?? 0 }} 份等你确认
          </p>
        </article>

        <article class="yy-card relative overflow-hidden p-5">
          <div class="flex items-center justify-between">
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-[#edf2e9] text-[var(--yy-sage)]">
              <Heart class="h-[18px] w-[18px]" />
            </span>
            <span class="text-[11px] font-medium text-[var(--yy-muted)]">本月</span>
          </div>
          <p class="yy-display mt-5 text-[38px] font-bold leading-none text-[var(--yy-ink)]">
            {{ homeSummary?.monthly_accepted_orders_count ?? 0 }}
          </p>
          <p class="mt-2 truncate text-xs leading-5 text-[var(--yy-muted)]">
            最爱 · {{ homeSummary?.monthly_top_dish_name ?? '等第一顿饭' }}
          </p>
        </article>
      </div>
    </section>

    <section>
      <div class="mb-3 flex items-end justify-between px-1">
        <div>
          <p class="yy-kicker">Quick actions</p>
          <h2 class="yy-display mt-1 text-[25px] font-bold text-[var(--yy-ink)]">今天做什么</h2>
        </div>
        <span class="text-xs text-[var(--yy-muted)]">好好吃饭，也好好生活</span>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <button
          type="button"
          class="group col-span-2 flex items-center justify-between rounded-[26px] bg-[var(--yy-tomato)] p-5 text-left text-white shadow-[0_16px_38px_rgba(207,100,71,0.22)] transition hover:-translate-y-0.5"
          @click="goToCreateOrder"
        >
          <span class="flex items-center gap-3">
            <span class="flex h-11 w-11 items-center justify-center rounded-full bg-white/15">
              <UtensilsCrossed class="h-5 w-5" />
            </span>
            <span>
              <span class="block text-base font-semibold">发起点菜</span>
              <span class="mt-0.5 block text-xs text-white/70">把想吃的告诉对方</span>
            </span>
          </span>
          <ArrowRight class="h-5 w-5 transition-transform group-hover:translate-x-1" />
        </button>

        <button
          type="button"
          class="yy-card yy-soft-button flex min-h-32 flex-col items-start justify-between p-5 text-left"
          @click="goToDishes"
        >
          <CookingPot class="h-6 w-6 text-[var(--yy-sage)]" />
          <span>
            <span class="block text-sm font-semibold text-[var(--yy-ink)]">家庭菜单</span>
            <span class="mt-1 block text-xs text-[var(--yy-muted)]">看看有哪些拿手菜</span>
          </span>
        </button>

        <button
          type="button"
          class="yy-card yy-soft-button flex min-h-32 flex-col items-start justify-between p-5 text-left"
          @click="goToHistory"
        >
          <History class="h-6 w-6 text-[var(--yy-apricot)]" />
          <span>
            <span class="block text-sm font-semibold text-[var(--yy-ink)]">用餐食记</span>
            <span class="mt-1 block text-xs text-[var(--yy-muted)]">收藏一起吃过的饭</span>
          </span>
        </button>
      </div>
    </section>

    <section>
      <div class="mb-3 flex items-end justify-between px-1">
        <div>
          <p class="yy-kicker">Recent memories</p>
          <h2 class="yy-display mt-1 text-[25px] font-bold text-[var(--yy-ink)]">最近一起吃过</h2>
        </div>
        <button
          type="button"
          class="text-xs font-medium text-[var(--yy-tomato)]"
          @click="goToHistory"
        >
          全部食记
        </button>
      </div>

      <div v-if="homeLoading" class="yy-card p-5 text-sm text-[var(--yy-muted)]">
        正在翻看最近的用餐记录…
      </div>

      <div v-else-if="recentHistory.length" class="yy-card overflow-hidden px-5">
        <button
          v-for="(order, index) in recentHistory"
          :key="order.id"
          type="button"
          class="group flex w-full items-center gap-4 py-4 text-left"
          :class="index ? 'border-t border-[var(--yy-line)]' : ''"
          @click="goToOrderDetail(order.id)"
        >
          <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-cream)] text-[var(--yy-tomato)]">
            <MessageCircleHeart v-if="order.review" class="h-5 w-5" />
            <UtensilsCrossed v-else class="h-5 w-5" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-semibold text-[var(--yy-ink)]">
              {{ orderSummary(order) }}
            </span>
            <span class="mt-1 block text-xs text-[var(--yy-muted)]">
              {{ order.planned_date }} · {{ order.requester.nickname }} 点给 {{ order.cook.nickname }}
            </span>
          </span>
          <span class="shrink-0 text-xs font-medium text-[var(--yy-muted)]">
            {{ order.review ? `${order.review.rating}.0` : '待评价' }}
          </span>
        </button>
      </div>

      <div v-else class="yy-card flex items-center gap-4 p-5">
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#fff0e3] text-[var(--yy-tomato)]">
          <UtensilsCrossed class="h-5 w-5" />
        </span>
        <div>
          <p class="text-sm font-semibold text-[var(--yy-ink)]">第一顿饭，值得被记住</p>
          <p class="mt-1 text-xs leading-5 text-[var(--yy-muted)]">完成一次点菜后，用餐记录会出现在这里。</p>
        </div>
      </div>
    </section>
    </template>
  </section>
</template>
