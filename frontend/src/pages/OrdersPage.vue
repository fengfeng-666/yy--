<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'
import { CalendarClock, CheckCircle2, ChevronRight, Clock3, Plus, Utensils } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useOrderStore } from '@/stores/order'
import type { MealOrder, MealOrderRole, MealOrderStatus } from '@/types/order'

const router = useRouter()
const authStore = useAuthStore()
const orderStore = useOrderStore()

const { currentUser } = storeToRefs(authStore)
const { orders, loading } = storeToRefs(orderStore)

const activeRole = ref<MealOrderRole>('to_me')
const activeStatus = ref<MealOrderStatus>('pending')

onMounted(async () => {
  await loadOrders()
})

watch([activeRole, activeStatus], async () => {
  await loadOrders()
})

async function loadOrders() {
  try {
    await orderStore.loadOrders({
      role: activeRole.value,
      status: activeStatus.value,
    })
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载点菜列表失败')
  }
}

function statusText(status: MealOrderStatus) {
  return status === 'accepted' ? '已接受' : '待确认'
}

function statusClass(status: MealOrderStatus) {
  return status === 'accepted' ? 'bg-sky-50 text-sky-700' : 'bg-orange-50 text-orange-700'
}

function orderSummary(order: MealOrder) {
  return order.items.map((item) => `${item.dish.name} x${item.quantity}`).join('、')
}

async function goToCreateOrder() {
  await router.push('/orders/create')
}

async function goToOrderDetail(orderId: number) {
  await router.push(`/orders/${orderId}`)
}

async function acceptCurrentOrder(orderId: number) {
  try {
    await orderStore.acceptOrderItem(orderId)
    showSuccessToast('点菜已接受')
    await loadOrders()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '接受点菜失败')
  }
}

function canAccept(order: MealOrder) {
  return order.status === 'pending' && order.cook_id === currentUser.value?.id
}
</script>

<template>
  <section class="yy-page space-y-5 pb-8 pt-5">
    <header class="yy-enter flex items-end justify-between gap-4 px-1">
      <div>
        <p class="yy-kicker">Meal requests</p>
        <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">今天吃什么</h1>
        <p class="mt-3 text-sm text-[var(--yy-muted)]">每一份点菜，都是一句具体的“想和你吃饭”。</p>
      </div>
      <button
        type="button"
        class="yy-primary-button flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[var(--yy-ink)] text-white shadow-[0_12px_25px_rgba(48,37,31,0.2)]"
        aria-label="发起点菜"
        @click="goToCreateOrder"
      >
        <Plus class="h-5 w-5" />
      </button>
    </header>

    <div class="yy-card yy-enter yy-enter-delay-1 grid grid-cols-2 gap-1 p-1.5">
      <button
        type="button"
        class="rounded-[18px] px-4 py-2.5 text-sm font-medium transition"
        :class="
          activeRole === 'to_me'
            ? 'bg-[var(--yy-ink)] text-white'
            : 'text-[var(--yy-muted)] hover:bg-[var(--yy-cream)]'
        "
        @click="activeRole = 'to_me'"
      >
        点给我的
      </button>
      <button
        type="button"
        class="rounded-[18px] px-4 py-2.5 text-sm font-medium transition"
        :class="
          activeRole === 'my_requested'
            ? 'bg-[var(--yy-ink)] text-white'
            : 'text-[var(--yy-muted)] hover:bg-[var(--yy-cream)]'
        "
        @click="activeRole = 'my_requested'"
      >
        我发起的
      </button>
    </div>

    <div class="flex items-center gap-2 px-1">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm transition"
        :class="
          activeStatus === 'pending'
            ? 'bg-[#fff0e3] font-medium text-[var(--yy-tomato)]'
            : 'text-[var(--yy-muted)] hover:bg-white/70'
        "
        @click="activeStatus = 'pending'"
      >
        <Clock3 class="h-4 w-4" /> 待确认
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm transition"
        :class="
          activeStatus === 'accepted'
            ? 'bg-[#edf2e9] font-medium text-[#627459]'
            : 'text-[var(--yy-muted)] hover:bg-white/70'
        "
        @click="activeStatus = 'accepted'"
      >
        <CheckCircle2 class="h-4 w-4" /> 已接受
      </button>
    </div>

    <div v-if="loading" class="yy-card p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载点菜列表...
    </div>

    <div v-else-if="!orders.length" class="yy-card p-8 text-center">
      <span class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#fff0e3] text-[var(--yy-tomato)]">
        <Utensils class="h-6 w-6" />
      </span>
      <p class="yy-display mt-4 text-xl font-bold text-[var(--yy-ink)]">暂时没有相关点菜</p>
      <p class="mt-2 text-sm leading-6 text-[var(--yy-muted)]">切换筛选看看，或者先发起一份新的点菜。</p>
      <button
        type="button"
        class="mt-5 rounded-full bg-[var(--yy-ink)] px-5 py-2 text-sm text-white"
        @click="goToCreateOrder"
      >
        现在发起
      </button>
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="order in orders"
        :key="order.id"
        class="yy-card group cursor-pointer p-5 transition hover:-translate-y-0.5 hover:shadow-[0_22px_55px_rgba(77,53,38,0.13)]"
        @click="goToOrderDetail(order.id)"
      >
        <div class="flex items-start gap-4">
          <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-cream)] text-[var(--yy-tomato)]">
            <CalendarClock class="h-5 w-5" />
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-base font-semibold text-[var(--yy-ink)]">
              {{ order.planned_date }} {{ order.planned_time?.slice(0, 5) || '' }}
              </h2>
              <span class="rounded-full px-3 py-1 text-[10px] font-medium" :class="statusClass(order.status)">
                {{ statusText(order.status) }}
              </span>
            </div>
            <p class="mt-1 text-sm text-[var(--yy-muted)]">
              {{ order.requester.nickname }} 点给 {{ order.cook.nickname }}
            </p>
          </div>
        </div>

        <p class="mt-4 rounded-2xl bg-[var(--yy-cream)] px-4 py-3 text-sm font-medium leading-6 text-[var(--yy-ink)]">
          {{ orderSummary(order) }}
        </p>

        <p v-if="order.note" class="mt-2 text-sm text-[var(--yy-muted)]">
          备注：{{ order.note }}
        </p>

        <div class="mt-4 flex items-center gap-3">
          <button
            v-if="canAccept(order)"
            type="button"
            class="yy-primary-button rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white"
            @click.stop="acceptCurrentOrder(order.id)"
          >
            接受
          </button>
          <button
            type="button"
            class="ml-auto inline-flex items-center gap-1 text-xs font-medium text-[var(--yy-muted)]"
            @click.stop="goToOrderDetail(order.id)"
          >
            查看详情 <ChevronRight class="h-3.5 w-3.5" />
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
