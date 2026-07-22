<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'

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
  <section class="space-y-4 px-5 pb-8 pt-6">
    <header class="flex items-start justify-between gap-4">
      <div>
        <p class="text-sm text-[var(--yy-muted)]">点菜中心</p>
        <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">正在流转的菜单</h1>
      </div>
      <button
        type="button"
        class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white"
        @click="goToCreateOrder"
      >
        发起点菜
      </button>
    </header>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm"
        :class="
          activeRole === 'to_me'
            ? 'bg-[var(--yy-ink)] text-white'
            : 'bg-white text-[var(--yy-muted)] shadow-sm'
        "
        @click="activeRole = 'to_me'"
      >
        对方点给我
      </button>
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm"
        :class="
          activeRole === 'my_requested'
            ? 'bg-[var(--yy-ink)] text-white'
            : 'bg-white text-[var(--yy-muted)] shadow-sm'
        "
        @click="activeRole = 'my_requested'"
      >
        我发起的
      </button>
    </div>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm"
        :class="
          activeStatus === 'pending'
            ? 'bg-[var(--yy-ink)] text-white'
            : 'bg-white text-[var(--yy-muted)] shadow-sm'
        "
        @click="activeStatus = 'pending'"
      >
        待确认
      </button>
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm"
        :class="
          activeStatus === 'accepted'
            ? 'bg-[var(--yy-ink)] text-white'
            : 'bg-white text-[var(--yy-muted)] shadow-sm'
        "
        @click="activeStatus = 'accepted'"
      >
        已接受
      </button>
    </div>

    <div v-if="loading" class="rounded-[28px] bg-white p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载点菜列表...
    </div>

    <div v-else-if="!orders.length" class="rounded-[28px] bg-white p-8 text-center shadow-sm">
      <p class="text-lg font-medium text-[var(--yy-ink)]">暂时没有相关点菜</p>
      <p class="mt-2 text-sm text-[var(--yy-muted)]">切换筛选看看，或者先发起一次新的点菜。</p>
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
        class="rounded-[28px] border border-[var(--yy-line)] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]"
        @click="goToOrderDetail(order.id)"
      >
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-[var(--yy-ink)]">
              {{ order.planned_date }} {{ order.planned_time?.slice(0, 5) || '' }}
            </h2>
            <p class="mt-1 text-sm text-[var(--yy-muted)]">
              {{ order.requester.nickname }} -> {{ order.cook.nickname }}
            </p>
          </div>
          <span class="rounded-full px-3 py-1 text-xs" :class="statusClass(order.status)">
            {{ statusText(order.status) }}
          </span>
        </div>

        <p class="mt-3 text-sm leading-6 text-[var(--yy-muted)]">
          {{ orderSummary(order) }}
        </p>

        <p v-if="order.note" class="mt-2 text-sm text-[var(--yy-muted)]">
          备注：{{ order.note }}
        </p>

        <div class="mt-4 flex gap-3">
          <button
            v-if="canAccept(order)"
            type="button"
            class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white"
            @click.stop="acceptCurrentOrder(order.id)"
          >
            接受
          </button>
          <button
            type="button"
            class="rounded-full bg-[var(--yy-cream)] px-4 py-2 text-sm text-[var(--yy-ink)]"
            @click.stop="goToOrderDetail(order.id)"
          >
            查看详情
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
