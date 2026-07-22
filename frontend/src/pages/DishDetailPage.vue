<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { showFailToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import { fetchDishDetail } from '@/api/dish'
import type { DishItem } from '@/types/dish'
import { resolveAssetUrl } from '@/utils/assets'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const dish = ref<DishItem | null>(null)

const dishImage = computed(() => resolveAssetUrl(dish.value?.image_url))

onMounted(async () => {
  const dishId = Number(route.params.id)
  if (!dishId) {
    showFailToast('菜品不存在')
    await router.replace('/dishes')
    return
  }

  loading.value = true
  try {
    dish.value = await fetchDishDetail(dishId)
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载菜品失败')
    await router.replace('/dishes')
  } finally {
    loading.value = false
  }
})

async function goBack() {
  await router.push('/dishes')
}

async function startOrder() {
  if (!dish.value) {
    return
  }
  await router.push({ path: '/orders/create', query: { dishId: String(dish.value.id) } })
}

function formatPrice(price: number) {
  return `¥ ${price.toFixed(2)}`
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
        <p class="text-sm text-[var(--yy-muted)]">菜品详情</p>
        <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">看看今天想点哪一道</h1>
      </div>
    </header>

    <div v-if="loading" class="rounded-[28px] bg-white p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载菜品详情...
    </div>

    <div v-else-if="dish" class="space-y-4">
      <article class="overflow-hidden rounded-[28px] bg-white shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
        <div
          v-if="dish.image_url"
          class="aspect-[4/3] overflow-hidden bg-[var(--yy-cream)]"
        >
          <img :src="dishImage" :alt="dish.name" class="h-full w-full object-cover" />
        </div>
        <div
          v-else
          class="aspect-[4/3] bg-[linear-gradient(135deg,_rgba(242,172,114,0.4),_rgba(232,122,85,0.28))]"
        ></div>

        <div class="space-y-3 p-5">
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-2xl font-semibold text-[var(--yy-ink)]">{{ dish.name }}</h2>
            <span
              class="rounded-full px-3 py-1 text-xs"
              :class="
                dish.is_available ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
              "
            >
              {{ dish.is_available ? '可点菜' : '暂不可点' }}
            </span>
          </div>

          <p class="text-xl font-medium text-[var(--yy-ink)]">{{ formatPrice(dish.price) }}</p>
          <p class="text-sm leading-6 text-[var(--yy-muted)]">
            {{ dish.description || '这道菜还没有更多介绍，可以先试着点一次。' }}
          </p>
        </div>
      </article>

      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-sm text-[var(--yy-muted)]">适合场景</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <span class="rounded-full bg-[var(--yy-cream)] px-3 py-2 text-sm text-[var(--yy-ink)]">
            家常晚餐
          </span>
          <span class="rounded-full bg-[var(--yy-cream)] px-3 py-2 text-sm text-[var(--yy-ink)]">
            双人份
          </span>
          <span class="rounded-full bg-[var(--yy-cream)] px-3 py-2 text-sm text-[var(--yy-ink)]">
            可加入点菜单
          </span>
        </div>
      </article>

      <button
        type="button"
        class="w-full rounded-full bg-[var(--yy-ink)] px-5 py-4 text-sm font-medium text-white disabled:opacity-50"
        :disabled="!dish.is_available"
        @click="startOrder"
      >
        {{ dish.is_available ? '发起点菜' : '当前不可点' }}
      </button>
    </div>
  </section>
</template>
