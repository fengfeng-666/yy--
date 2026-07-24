<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { showFailToast } from 'vant'
import { ArrowLeft, ChefHat, CircleCheckBig, ClipboardList, Sparkles } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

import NoFamilyState from '@/components/NoFamilyState.vue'
import { fetchShoppingLists } from '@/api/shoppingList'
import { useFamilyStore } from '@/stores/family'
import type { ShoppingList, ShoppingListItem, ShoppingListSourceType, ShoppingListStatus } from '@/types/shoppingList'

const router = useRouter()
const familyStore = useFamilyStore()

const loading = ref(false)
const shoppingLists = ref<ShoppingList[]>([])

const hasFamily = computed(() => familyStore.hasFamily)

onMounted(async () => {
  if (!hasFamily.value) return
  await loadShoppingLists()
})

async function loadShoppingLists() {
  loading.value = true
  try {
    shoppingLists.value = await fetchShoppingLists()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载购物清单失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  void router.push('/profile')
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(value))
}

function sourceTypeText(sourceType: ShoppingListSourceType) {
  return sourceType === 'ai_agent' ? 'AI 生成' : '手动创建'
}

function statusText(status: ShoppingListStatus) {
  return status === 'completed' ? '已完成' : '进行中'
}

function formatItemQuantity(item: ShoppingListItem) {
  if (item.quantity == null) return ''
  return `${item.quantity}${item.unit ?? ''}`
}

function pendingCount(items: ShoppingListItem[]) {
  return items.filter((item) => !item.is_purchased).length
}
</script>

<template>
  <section class="yy-page space-y-5 pb-8 pt-5">
    <header class="yy-enter px-1">
      <button
        type="button"
        class="mb-4 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-ink)] shadow-sm"
        @click="goBack"
      >
        <ArrowLeft class="h-4 w-4" />
        返回我的
      </button>
      <p class="yy-kicker">Shopping lists</p>
      <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">购物清单</h1>
      <p class="mt-3 text-sm text-[var(--yy-muted)]">把要准备的食材集中放在一起，买菜时一眼就能看完。</p>
    </header>

    <NoFamilyState
      v-if="!hasFamily"
      title="加入家庭后才能查看购物清单"
      description="和家人共享同一个家庭空间后，AI 生成和手动创建的购物清单都会集中展示在这里。"
    />

    <template v-else>
      <div v-if="loading" class="yy-card p-8 text-center text-sm text-[var(--yy-muted)]">
        正在加载购物清单...
      </div>

      <div v-else-if="!shoppingLists.length" class="yy-card p-8 text-center">
        <span class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#fff0e3] text-[var(--yy-tomato)]">
          <ClipboardList class="h-6 w-6" />
        </span>
        <p class="yy-display mt-4 text-xl font-bold text-[var(--yy-ink)]">还没有购物清单</p>
        <p class="mt-2 text-sm leading-6 text-[var(--yy-muted)]">当你在 AI 对话里确认生成购物清单后，这里就会显示出来。</p>
      </div>

      <div v-else class="space-y-4">
        <article
          v-for="list in shoppingLists"
          :key="list.id"
          class="yy-card overflow-hidden"
        >
          <div class="flex items-start gap-4 border-b border-[var(--yy-line)] px-5 py-5">
            <span
              class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl"
              :class="list.source_type === 'ai_agent' ? 'bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]' : 'bg-[var(--yy-sage)]/15 text-[var(--yy-sage)]'"
            >
              <Sparkles v-if="list.source_type === 'ai_agent'" class="h-5 w-5" :stroke-width="2" />
              <ChefHat v-else class="h-5 w-5" :stroke-width="2" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-3">
                <h2 class="truncate text-lg font-semibold text-[var(--yy-ink)]">{{ list.name }}</h2>
                <span
                  class="shrink-0 rounded-full px-3 py-1 text-[11px] font-medium"
                  :class="list.status === 'completed' ? 'bg-[#edf2e9] text-[#627459]' : 'bg-[#fff0e3] text-[var(--yy-tomato)]'"
                >
                  {{ statusText(list.status) }}
                </span>
              </div>
              <div class="mt-2 flex flex-wrap items-center gap-2 text-xs text-[var(--yy-muted)]">
                <span class="rounded-full bg-[var(--yy-cream)] px-3 py-1">{{ sourceTypeText(list.source_type) }}</span>
                <span>{{ formatDateTime(list.updated_at) }}</span>
                <span>{{ pendingCount(list.items) }} 项待购买</span>
              </div>
            </div>
          </div>

          <div class="space-y-3 px-5 py-5">
            <div
              v-for="item in list.items"
              :key="item.id"
              class="flex items-start gap-3 rounded-2xl bg-[var(--yy-cream)] px-4 py-3"
            >
              <CircleCheckBig
                class="mt-0.5 h-4 w-4 shrink-0"
                :class="item.is_purchased ? 'text-[var(--yy-sage)]' : 'text-[var(--yy-muted)]'"
              />
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-3">
                  <p class="truncate text-sm font-medium text-[var(--yy-ink)]">{{ item.name }}</p>
                  <span v-if="formatItemQuantity(item)" class="shrink-0 text-xs text-[var(--yy-muted)]">
                    {{ formatItemQuantity(item) }}
                  </span>
                </div>
                <p v-if="item.source_dish_name || item.note" class="mt-1 text-xs leading-5 text-[var(--yy-muted)]">
                  {{ item.source_dish_name ? `来源：${item.source_dish_name}` : '' }}
                  {{ item.source_dish_name && item.note ? ' · ' : '' }}
                  {{ item.note || '' }}
                </p>
              </div>
            </div>
          </div>
        </article>
      </div>
    </template>
  </section>
</template>
