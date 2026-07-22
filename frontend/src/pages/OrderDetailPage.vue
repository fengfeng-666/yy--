<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast, showSuccessToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useOrderStore } from '@/stores/order'
import { resolveAssetUrl } from '@/utils/assets'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const orderStore = useOrderStore()

const { currentUser } = storeToRefs(authStore)
const { currentOrder, detailLoading } = storeToRefs(orderStore)

const canAccept = computed(
  () =>
    currentOrder.value?.status === 'pending' &&
    currentOrder.value.cook_id === currentUser.value?.id,
)

const sortedLogs = computed(() =>
  [...(currentOrder.value?.status_logs ?? [])].sort((a, b) => a.created_at.localeCompare(b.created_at)),
)

onMounted(async () => {
  const orderId = Number(route.params.id)
  if (!orderId) {
    showFailToast('点菜订单不存在')
    await router.replace('/orders')
    return
  }
  try {
    await orderStore.loadOrderDetail(orderId)
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载点菜详情失败')
    await router.replace('/orders')
  }
})

async function goBack() {
  await router.push('/orders')
}

async function handleAccept() {
  if (!currentOrder.value) {
    return
  }
  try {
    await orderStore.acceptOrderItem(currentOrder.value.id)
    await orderStore.loadOrderDetail(currentOrder.value.id)
    showSuccessToast('点菜已接受')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '接受点菜失败')
  }
}

function statusText(status: string) {
  return status === 'accepted' ? '已接受' : '待确认'
}

function statusClass(status: string) {
  return status === 'accepted' ? 'bg-sky-50 text-sky-700' : 'bg-orange-50 text-orange-700'
}

function assetUrl(url: string | null) {
  return resolveAssetUrl(url)
}
</script>

<template>
  <section class="min-h-screen space-y-4 bg-[var(--yy-cream)] px-5 pb-8 pt-6">
    <header class="flex items-center gap-3">
      <button
        type="button"
        class="rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-ink)] shadow-sm"
        @click="goBack"
      >
        返回
      </button>
      <div>
        <p class="text-sm text-[var(--yy-muted)]">点菜详情</p>
        <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">查看这次点菜的安排</h1>
      </div>
    </header>

    <div v-if="detailLoading" class="rounded-[28px] bg-white p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载点菜详情...
    </div>

    <div v-else-if="currentOrder" class="space-y-4">
      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-[var(--yy-muted)]">订单 #{{ currentOrder.id }}</p>
            <h2 class="mt-1 text-xl font-semibold text-[var(--yy-ink)]">
              {{ currentOrder.planned_date }} {{ currentOrder.planned_time?.slice(0, 5) || '' }}
            </h2>
          </div>
          <span class="rounded-full px-3 py-1 text-xs" :class="statusClass(currentOrder.status)">
            {{ statusText(currentOrder.status) }}
          </span>
        </div>

        <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div class="rounded-2xl bg-[var(--yy-cream)] px-4 py-3">
            <p class="text-[var(--yy-muted)]">发起人</p>
            <p class="mt-1 font-medium text-[var(--yy-ink)]">{{ currentOrder.requester.nickname }}</p>
          </div>
          <div class="rounded-2xl bg-[var(--yy-cream)] px-4 py-3">
            <p class="text-[var(--yy-muted)]">指定厨师</p>
            <p class="mt-1 font-medium text-[var(--yy-ink)]">{{ currentOrder.cook.nickname }}</p>
          </div>
        </div>

        <div v-if="currentOrder.note" class="mt-4 rounded-2xl bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)]">
          <p class="text-[var(--yy-muted)]">备注</p>
          <p class="mt-1">{{ currentOrder.note }}</p>
        </div>
      </article>

      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-sm text-[var(--yy-muted)]">点菜单</p>
        <div class="mt-4 space-y-3">
          <div
            v-for="item in currentOrder.items"
            :key="item.id"
            class="flex gap-3 rounded-[24px] bg-[var(--yy-cream)] p-4"
          >
            <div class="h-20 w-20 shrink-0 overflow-hidden rounded-2xl bg-white">
              <img
                v-if="item.dish.image_url"
                :src="assetUrl(item.dish.image_url)"
                :alt="item.dish.name"
                class="h-full w-full object-cover"
              />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-start justify-between gap-3">
                <h3 class="text-base font-medium text-[var(--yy-ink)]">{{ item.dish.name }}</h3>
                <span class="rounded-full bg-white px-3 py-1 text-xs text-[var(--yy-muted)]">
                  x{{ item.quantity }}
                </span>
              </div>
              <p v-if="item.note" class="mt-2 text-sm text-[var(--yy-muted)]">{{ item.note }}</p>
            </div>
          </div>
        </div>
      </article>

      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-sm text-[var(--yy-muted)]">状态时间线</p>
        <div class="mt-4 space-y-3">
          <div
            v-for="log in sortedLogs"
            :key="log.id"
            class="rounded-2xl bg-[var(--yy-cream)] px-4 py-3"
          >
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-medium text-[var(--yy-ink)]">
                {{ log.operator.nickname }} {{ statusText(log.to_status) }}
              </p>
              <span class="text-xs text-[var(--yy-muted)]">
                {{ log.created_at.replace('T', ' ').slice(0, 16) }}
              </span>
            </div>
            <p v-if="log.note" class="mt-1 text-sm text-[var(--yy-muted)]">{{ log.note }}</p>
          </div>
        </div>
      </article>

      <button
        v-if="canAccept"
        type="button"
        class="w-full rounded-full bg-[var(--yy-ink)] px-5 py-4 text-sm font-medium text-white"
        @click="handleAccept"
      >
        接受点菜
      </button>
    </div>
  </section>
</template>
