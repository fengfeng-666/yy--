<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import { createOrder, fetchDishes, fetchFamilyMembers } from '@/api'
import { session } from '@/stores/session'
import type { DishItem, FamilyMember } from '@/types/api'
import { showError } from '@/utils/request'
import { requestSubscriptions } from '@/utils/subscriptions'

const dishes = ref<DishItem[]>([])
const members = ref<FamilyMember[]>([])
const quantities = reactive<Record<number, number>>({})
const submitting = ref(false)
const form = reactive({ cookId: 0, date: formatDate(new Date()), time: '19:00', note: '' })

const cooks = computed(() => members.value.filter((item) => item.user_id !== session.user?.id))
const cookNames = computed(() => cooks.value.map((item) => item.user.nickname))
const selectedCount = computed(() => Object.values(quantities).reduce((sum, value) => sum + value, 0))

function formatDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function changeQuantity(dishId: number, delta: number) {
  quantities[dishId] = Math.max(0, (quantities[dishId] || 0) + delta)
}

function onCookChange(event: { detail: { value: string } }) {
  const selected = cooks.value[Number(event.detail.value)]
  form.cookId = selected?.user_id || 0
}

async function submit() {
  if (!form.cookId) return uni.showToast({ title: '请选择谁来做饭', icon: 'none' })
  const items = dishes.value
    .filter((dish) => quantities[dish.id] > 0)
    .map((dish) => ({ dish_id: dish.id, quantity: quantities[dish.id] }))
  if (!items.length) return uni.showToast({ title: '至少选择一道菜', icon: 'none' })

  submitting.value = true
  try {
    try {
      await requestSubscriptions(['order_accepted'])
    } catch {
      // 消息授权失败不阻断点菜
    }
    await createOrder({
      cook_id: form.cookId,
      planned_date: form.date,
      planned_time: `${form.time}:00`,
      note: form.note.trim() || undefined,
      items,
    })
    uni.showToast({ title: '点菜已发出' })
    setTimeout(() => uni.reLaunch({ url: '/pages/orders/index' }), 500)
  } catch (error) {
    showError(error, '点菜失败')
  } finally {
    submitting.value = false
  }
}

onLoad(async (query) => {
  try {
    const [dishList, memberList] = await Promise.all([fetchDishes(), fetchFamilyMembers()])
    dishes.value = dishList.filter((dish) => dish.is_available)
    members.value = memberList
    form.cookId = cooks.value[0]?.user_id || 0
    const presetId = Number(query?.dishId)
    if (presetId) quantities[presetId] = 1
  } catch (error) {
    showError(error, '点菜信息加载失败')
  }
})
</script>

<template>
  <view class="create-page">
    <view class="form-section yy-card">
      <text class="section-label">谁来掌勺</text>
      <picker :range="cookNames" @change="onCookChange">
        <view class="field">{{ cooks.find((item) => item.user_id === form.cookId)?.user.nickname || '请选择' }} <text>⌄</text></view>
      </picker>
      <view class="row">
        <picker mode="date" :value="form.date" @change="form.date = $event.detail.value"><view class="field">{{ form.date }}</view></picker>
        <picker mode="time" :value="form.time" @change="form.time = $event.detail.value"><view class="field">{{ form.time }}</view></picker>
      </view>
      <textarea v-model="form.note" class="field note" placeholder="备注，例如少糖、不要香菜" />
    </view>

    <view class="section-title-row"><text>选择菜品</text><text class="yy-muted">已选 {{ selectedCount }} 份</text></view>
    <view class="dish-list yy-card">
      <view v-for="dish in dishes" :key="dish.id" class="dish-row">
        <view class="dish-copy"><text class="dish-name">{{ dish.name }}</text><text class="dish-price">¥ {{ dish.price.toFixed(2) }}</text></view>
        <view class="stepper">
          <button @tap="changeQuantity(dish.id, -1)">−</button>
          <text>{{ quantities[dish.id] || 0 }}</text>
          <button class="plus" @tap="changeQuantity(dish.id, 1)">＋</button>
        </view>
      </view>
    </view>

    <button class="yy-primary submit" :loading="submitting" :disabled="submitting" @tap="submit">提交点菜</button>
  </view>
</template>

<style scoped lang="scss">
.create-page { min-height: 100vh; padding: 28rpx 30rpx 60rpx; }
.form-section { padding: 32rpx; }
.section-label { display: block; margin: 8rpx 0 14rpx; color: #84746a; font-size: 23rpx; }
.field { display: flex; height: 84rpx; align-items: center; justify-content: space-between; margin-bottom: 18rpx; padding: 0 26rpx; border-radius: 26rpx; background: #f8f3eb; font-size: 26rpx; }
.row { display: flex; gap: 16rpx; }
.row picker { flex: 1; }
.note { width: 100%; height: 150rpx; padding-top: 24rpx; }
.section-title-row { display: flex; align-items: center; justify-content: space-between; margin: 40rpx 8rpx 18rpx; font-size: 30rpx; font-weight: 600; }
.section-title-row .yy-muted { font-size: 23rpx; font-weight: 400; }
.dish-list { padding: 8rpx 28rpx; }
.dish-row { display: flex; min-height: 116rpx; align-items: center; justify-content: space-between; border-bottom: 1rpx solid #e7dbcf; }
.dish-row:last-child { border-bottom: none; }
.dish-copy { display: flex; flex-direction: column; }
.dish-name { font-size: 28rpx; font-weight: 600; }
.dish-price { margin-top: 8rpx; color: #cf6447; font-size: 23rpx; }
.stepper { display: flex; align-items: center; gap: 20rpx; }
.stepper button { width: 56rpx; height: 56rpx; margin: 0; padding: 0; border-radius: 28rpx; color: #30251f; background: #f8f3eb; font-size: 28rpx; line-height: 56rpx; }
.stepper button.plus { color: #fff; background: #30251f; }
.stepper text { min-width: 26rpx; font-size: 25rpx; text-align: center; }
.submit { margin-top: 36rpx; }
</style>
