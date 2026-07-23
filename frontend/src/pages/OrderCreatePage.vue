<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast, showSuccessToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import { fetchDishes } from '@/api/dish'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'
import { useOrderStore } from '@/stores/order'
import type { DishItem } from '@/types/dish'
import { resolveAssetUrl } from '@/utils/assets'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const familyStore = useFamilyStore()
const orderStore = useOrderStore()

const { currentUser } = storeToRefs(authStore)
const { members } = storeToRefs(familyStore)

const loading = ref(false)
const submitting = ref(false)
const dishes = ref<DishItem[]>([])
const selectedQuantities = reactive<Record<number, number>>({})
const form = reactive({
  cookId: 0,
  plannedDate: new Date().toISOString().split('T')[0],
  plannedTime: '19:00',
  note: '',
})

const cookOptions = computed(() =>
  members.value.filter((member) => member.user_id !== currentUser.value?.id),
)

const selectedItems = computed(() =>
  dishes.value.filter((dish) => (selectedQuantities[dish.id] ?? 0) > 0),
)

const totalQuantity = computed(() =>
  Object.values(selectedQuantities).reduce((total, quantity) => total + quantity, 0),
)

onMounted(async () => {
  loading.value = true
  try {
    dishes.value = (await fetchDishes()).filter((dish) => dish.is_available)
    const recommendedCook = cookOptions.value[0]
    form.cookId = recommendedCook?.user_id ?? 0

    const presetDishId = Number(route.query.dishId)
    if (presetDishId) {
      selectedQuantities[presetDishId] = 1
    }
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载点菜数据失败')
  } finally {
    loading.value = false
  }
})

async function goBack() {
  await router.push('/orders')
}

function setQuantity(dishId: number, nextQuantity: number) {
  if (nextQuantity <= 0) {
    delete selectedQuantities[dishId]
    return
  }
  selectedQuantities[dishId] = nextQuantity
}

function currentQuantity(dishId: number) {
  return selectedQuantities[dishId] ?? 0
}

function dishImage(url: string | null) {
  return resolveAssetUrl(url)
}

async function submitOrder() {
  if (!form.cookId) {
    showFailToast('请选择厨师')
    return
  }
  if (!selectedItems.value.length) {
    showFailToast('至少选择一道菜')
    return
  }

  submitting.value = true
  try {
    const order = await orderStore.createOrderItem({
      cook_id: form.cookId,
      planned_date: form.plannedDate,
      planned_time: form.plannedTime ? `${form.plannedTime}:00` : undefined,
      note: form.note.trim() || undefined,
      items: selectedItems.value.map((dish, index) => ({
        dish_id: dish.id,
        quantity: currentQuantity(dish.id),
        sort_order: index,
      })),
    })
    showSuccessToast('点菜创建成功')
    await router.replace(`/orders/${order.id}`)
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '点菜创建失败')
  } finally {
    submitting.value = false
  }
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
        <p class="text-sm text-[var(--yy-muted)]">发起点菜</p>
        <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">给对方安排今天想吃的菜</h1>
      </div>
    </header>

    <div v-if="loading" class="rounded-[28px] bg-white p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载可点菜品...
    </div>

    <div v-else class="space-y-4">
      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-sm text-[var(--yy-muted)]">基础信息</p>
        <div class="mt-4 space-y-3">
          <select
            v-model.number="form.cookId"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
          >
            <option :value="0" disabled>选择谁来做</option>
            <option v-for="member in cookOptions" :key="member.id" :value="member.user_id">
              {{ member.user.nickname }} (@{{ member.user.username }})
            </option>
          </select>

          <div class="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
            <label class="block min-w-0">
              <span class="mb-1.5 block px-1 text-xs text-[var(--yy-muted)]">日期</span>
              <input
                v-model="form.plannedDate"
                type="date"
                class="mobile-date-time-input rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
              />
            </label>
            <label class="block min-w-0">
              <span class="mb-1.5 block px-1 text-xs text-[var(--yy-muted)]">时间</span>
              <input
                v-model="form.plannedTime"
                type="time"
                class="mobile-date-time-input rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
              />
            </label>
          </div>

          <textarea
            v-model.trim="form.note"
            rows="3"
            placeholder="备注，例如少糖、不要香菜"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
          ></textarea>
        </div>
      </article>

      <article class="rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <p class="text-sm text-[var(--yy-muted)]">选择菜品</p>
          <span class="text-sm text-[var(--yy-muted)]">已选 {{ totalQuantity }} 份</span>
        </div>

        <div v-if="!dishes.length" class="mt-4 rounded-2xl bg-[var(--yy-cream)] px-4 py-5 text-center text-sm text-[var(--yy-muted)]">
          还没有可点菜品，请先去菜单里添加并上架菜品。
        </div>

        <div v-else class="mt-4 space-y-3">
          <div
            v-for="dish in dishes"
            :key="dish.id"
            class="rounded-[24px] bg-[var(--yy-cream)] p-4"
          >
            <div class="flex gap-3">
              <div
                class="h-20 w-20 shrink-0 overflow-hidden rounded-2xl bg-white"
              >
                <img
                  v-if="dish.image_url"
                  :src="dishImage(dish.image_url)"
                  :alt="dish.name"
                  class="h-full w-full object-cover"
                />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <h3 class="text-base font-medium text-[var(--yy-ink)]">{{ dish.name }}</h3>
                  </div>
                  <span class="text-sm font-medium text-[var(--yy-ink)]">¥ {{ dish.price.toFixed(2) }}</span>
                </div>
                <p class="mt-2 line-clamp-2 text-sm text-[var(--yy-muted)]">
                  {{ dish.description || '这道菜还没有补充描述。' }}
                </p>
                <div class="mt-3 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    class="h-8 w-8 rounded-full bg-white text-sm text-[var(--yy-ink)]"
                    @click="setQuantity(dish.id, currentQuantity(dish.id) - 1)"
                  >
                    -
                  </button>
                  <span class="min-w-6 text-center text-sm text-[var(--yy-ink)]">
                    {{ currentQuantity(dish.id) }}
                  </span>
                  <button
                    type="button"
                    class="h-8 w-8 rounded-full bg-[var(--yy-ink)] text-sm text-white"
                    @click="setQuantity(dish.id, currentQuantity(dish.id) + 1)"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </article>

      <button
        type="button"
        class="w-full rounded-full bg-[var(--yy-ink)] px-5 py-4 text-sm font-medium text-white disabled:opacity-60"
        :disabled="submitting || !dishes.length"
        @click="submitOrder"
      >
        {{ submitting ? '提交中...' : '提交点菜' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.mobile-date-time-input {
  display: block;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  appearance: none;
  -webkit-appearance: none;
}
</style>
