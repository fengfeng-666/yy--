<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast } from 'vant'
import { useRouter } from 'vue-router'

import { useOrderStore } from '@/stores/order'
import { useFamilyStore } from '@/stores/family'
import NoFamilyState from '@/components/NoFamilyState.vue'

const router = useRouter()
const orderStore = useOrderStore()
const familyStore = useFamilyStore()
const { historyOrders, historyLoading } = storeToRefs(orderStore)
const { hasFamily } = storeToRefs(familyStore)

onMounted(async () => {
  if (!hasFamily.value) {
    return
  }
  try {
    await orderStore.loadDiningHistory()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载用餐历史失败')
  }
})

function orderSummary(order: (typeof historyOrders.value)[number]) {
  return order.items.map((item) => `${item.dish.name} x${item.quantity}`).join('、')
}

async function goToDetail(orderId: number) {
  await router.push(`/orders/${orderId}`)
}
</script>

<template>
  <section class="yy-page space-y-5 pb-8 pt-5">
    <header class="yy-enter px-1">
      <p class="yy-kicker">Dining journal</p>
      <h1 class="yy-display mt-2 text-[32px] font-bold leading-tight text-[var(--yy-ink)]">回顾每一次<br />一起吃饭</h1>
    </header>

    <NoFamilyState
      v-if="!hasFamily"
      title="加入家庭后开始记录食记"
      description="一起完成的每顿饭都会留在这里。先加入或创建家庭，再慢慢积累你们的用餐回忆。"
    />

    <div
      v-else-if="historyLoading"
      class="yy-card p-8 text-center text-sm text-[var(--yy-muted)]"
    >
      正在加载用餐历史...
    </div>

    <div
      v-else-if="!historyOrders.length"
      class="yy-card p-8 text-center text-sm text-[var(--yy-muted)]"
    >
      还没有已完成的用餐记录，先去发起一次点菜吧。
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="order in historyOrders"
        :key="order.id"
        class="yy-card p-5 transition hover:-translate-y-0.5"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-[var(--yy-muted)]">{{ order.planned_date }}</p>
            <h2 class="mt-1 text-lg font-semibold text-[var(--yy-ink)]">
              {{ orderSummary(order) }}
            </h2>
          </div>
          <span
            class="rounded-full px-3 py-1 text-xs"
            :class="order.review ? 'bg-emerald-50 text-emerald-700' : 'bg-orange-50 text-orange-700'"
          >
            {{ order.review ? `${order.review.rating} 分评价` : '待评价' }}
          </span>
        </div>

        <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div class="rounded-2xl bg-[var(--yy-cream)] px-4 py-3">
            <p class="text-[var(--yy-muted)]">发起人</p>
            <p class="mt-1 font-medium text-[var(--yy-ink)]">{{ order.requester.nickname }}</p>
          </div>
          <div class="rounded-2xl bg-[var(--yy-cream)] px-4 py-3">
            <p class="text-[var(--yy-muted)]">下厨人</p>
            <p class="mt-1 font-medium text-[var(--yy-ink)]">{{ order.cook.nickname }}</p>
          </div>
        </div>

        <p v-if="order.review?.content" class="mt-4 text-sm leading-6 text-[var(--yy-muted)]">
          “{{ order.review.content }}”
        </p>

        <button
          type="button"
          class="mt-4 rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white"
          @click="goToDetail(order.id)"
        >
          查看详情
        </button>
      </article>
    </div>
  </section>
</template>
