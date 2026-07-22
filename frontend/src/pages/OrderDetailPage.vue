<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
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
const reviewForm = reactive({
  rating: 5,
  content: '',
})

const canAccept = computed(
  () =>
    currentOrder.value?.status === 'pending' &&
    currentOrder.value.cook_id === currentUser.value?.id,
)

const sortedLogs = computed(() =>
  [...(currentOrder.value?.status_logs ?? [])].sort((a, b) => a.created_at.localeCompare(b.created_at)),
)

const canReview = computed(() => {
  if (!currentOrder.value) {
    return false
  }
  return (
    currentOrder.value.status === 'accepted' &&
    currentOrder.value.requester_id === currentUser.value?.id &&
    !currentOrder.value.review
  )
})

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

async function handleReviewSubmit() {
  if (!currentOrder.value) {
    return
  }
  try {
    await orderStore.submitMealReview(currentOrder.value.id, {
      rating: reviewForm.rating,
      content: reviewForm.content.trim() || undefined,
    })
    await orderStore.loadOrderDetail(currentOrder.value.id)
    reviewForm.content = ''
    reviewForm.rating = 5
    showSuccessToast('评价已提交')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '提交评价失败')
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
  <section class="yy-shell mx-auto min-h-screen max-w-[480px] space-y-4 px-5 pb-8 pt-6">
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

      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-sm text-[var(--yy-muted)]">用餐评价</p>
            <h2 class="mt-1 text-lg font-semibold text-[var(--yy-ink)]">给这顿饭留一句反馈</h2>
          </div>
          <span
            class="rounded-full px-3 py-1 text-xs"
            :class="currentOrder.review ? 'bg-emerald-50 text-emerald-700' : 'bg-orange-50 text-orange-700'"
          >
            {{ currentOrder.review ? `${currentOrder.review.rating} 分` : '未评价' }}
          </span>
        </div>

        <div v-if="currentOrder.review" class="mt-4 rounded-2xl bg-[var(--yy-cream)] px-4 py-4">
          <p class="text-sm font-medium text-[var(--yy-ink)]">
            {{ currentOrder.review.reviewer.nickname }} 给出 {{ currentOrder.review.rating }} 分
          </p>
          <p v-if="currentOrder.review.content" class="mt-2 text-sm leading-6 text-[var(--yy-muted)]">
            {{ currentOrder.review.content }}
          </p>
          <p class="mt-2 text-xs text-[var(--yy-muted)]">
            {{ currentOrder.review.created_at.replace('T', ' ').slice(0, 16) }}
          </p>
        </div>

        <div v-else-if="canReview" class="mt-4 space-y-3">
          <select
            v-model.number="reviewForm.rating"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
          >
            <option :value="5">5 分，很满意</option>
            <option :value="4">4 分，好吃</option>
            <option :value="3">3 分，还不错</option>
            <option :value="2">2 分，可以改进</option>
            <option :value="1">1 分，这次不太合口味</option>
          </select>

          <textarea
            v-model.trim="reviewForm.content"
            rows="3"
            placeholder="写一句评价，比如清淡刚好、下次还想吃"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
          ></textarea>

          <button
            type="button"
            class="rounded-full bg-[var(--yy-ink)] px-5 py-3 text-sm font-medium text-white"
            @click="handleReviewSubmit"
          >
            提交评价
          </button>
        </div>

        <div v-else class="mt-4 rounded-2xl bg-[var(--yy-cream)] px-4 py-4 text-sm text-[var(--yy-muted)]">
          评价会在点菜被接受后开放，且仅限发起点菜的人提交一次。
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
