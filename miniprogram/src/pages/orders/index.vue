<script setup lang="ts">
import { ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { acceptOrder, fetchCurrentFamily, fetchOrders } from '@/api'
import NoFamilyState from '@/components/NoFamilyState.vue'
import YyTabBar from '@/components/YyTabBar.vue'
import { session } from '@/stores/session'
import type { MealOrder } from '@/types/api'
import { ApiRequestError, showError } from '@/utils/request'
import { requestSubscriptions } from '@/utils/subscriptions'

const role = ref<'to_me' | 'my_requested'>('to_me')
const status = ref<'pending' | 'accepted'>('pending')
const orders = ref<MealOrder[]>([])
const loading = ref(false)

function orderText(order: MealOrder) {
  return order.items.map((item) => `${item.dish.name} × ${item.quantity}`).join('、')
}

async function load() {
  loading.value = true
  try {
    try {
      session.family = await fetchCurrentFamily()
    } catch (error) {
      if (error instanceof ApiRequestError && error.statusCode === 404) {
        session.family = null
        orders.value = []
        return
      }
      throw error
    }
    orders.value = await fetchOrders(role.value, status.value)
  } catch (error) {
    showError(error, '点菜列表加载失败')
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

async function changeRole(value: 'to_me' | 'my_requested') {
  role.value = value
  await load()
}

async function changeStatus(value: 'pending' | 'accepted') {
  status.value = value
  await load()
}

async function accept(order: MealOrder) {
  try {
    try {
      await requestSubscriptions(['new_order'])
    } catch {
      // 消息授权失败不阻断接单
    }
    await acceptOrder(order.id)
    uni.showToast({ title: '已接受点菜' })
    await load()
  } catch (error) {
    showError(error, '接受点菜失败')
  }
}

function goCreateOrder() {
  uni.navigateTo({ url: '/pages/order-create/index' })
}

onShow(load)
onPullDownRefresh(load)
</script>

<template>
  <view class="yy-page orders-page">
    <NoFamilyState
      v-if="!session.family"
      title="加入家庭后才能点菜"
      description="加入家人的餐桌后，你们就能互相点菜、接单并记录用餐安排。"
    />

    <template v-else>
    <view class="role-tabs yy-card">
      <button :class="{ active: role === 'to_me' }" @tap="changeRole('to_me')">点给我的</button>
      <button :class="{ active: role === 'my_requested' }" @tap="changeRole('my_requested')">我发起的</button>
    </view>
    <view class="status-tabs">
      <button :class="{ active: status === 'pending' }" @tap="changeStatus('pending')">待确认</button>
      <button :class="{ active: status === 'accepted' }" @tap="changeStatus('accepted')">已接受</button>
    </view>

    <view v-if="orders.length" class="order-list">
      <view v-for="order in orders" :key="order.id" class="order-card yy-card">
        <view class="order-head">
          <view>
            <text class="date">{{ order.planned_date }} {{ order.planned_time?.slice(0, 5) || '' }}</text>
            <text class="people">{{ order.requester.nickname }} 点给 {{ order.cook.nickname }}</text>
          </view>
          <text class="badge" :class="order.status">{{ order.status === 'accepted' ? '已接受' : '待确认' }}</text>
        </view>
        <text class="menu">{{ orderText(order) }}</text>
        <text v-if="order.note" class="note">备注：{{ order.note }}</text>
        <button v-if="role === 'to_me' && order.status === 'pending'" class="accept" @tap="accept(order)">接受点菜</button>
      </view>
    </view>
    <view v-else-if="!loading" class="empty yy-card">暂时没有相关点菜</view>
    <view v-else class="loading yy-muted">正在加载…</view>

    <button class="floating" @tap="goCreateOrder">＋</button>
    </template>
    <YyTabBar active="orders" />
  </view>
</template>

<style scoped lang="scss">
.orders-page { padding-top: 30rpx; }
.role-tabs { display: flex; padding: 10rpx; }
.role-tabs button { flex: 1; height: 72rpx; margin: 0; border-radius: 28rpx; color: #84746a; background: transparent; font-size: 26rpx; }
.role-tabs button.active { color: #fff; background: #30251f; }
.status-tabs { display: flex; margin: 24rpx 6rpx; gap: 14rpx; }
.status-tabs button { height: 64rpx; margin: 0; padding: 0 28rpx; border-radius: 32rpx; color: #84746a; background: transparent; font-size: 23rpx; line-height: 64rpx; }
.status-tabs button.active { color: #cf6447; background: #fff0e3; }
.order-card { margin-bottom: 22rpx; padding: 32rpx; }
.order-head { display: flex; align-items: flex-start; justify-content: space-between; }
.date { display: block; font-size: 29rpx; font-weight: 600; }
.people { display: block; margin-top: 10rpx; color: #84746a; font-size: 23rpx; }
.badge { padding: 8rpx 16rpx; border-radius: 20rpx; color: #b6662f; background: #fff0e3; font-size: 20rpx; }
.badge.accepted { color: #627459; background: #edf2e9; }
.menu { display: block; margin-top: 28rpx; padding: 24rpx; border-radius: 26rpx; background: #f8f3eb; font-size: 26rpx; line-height: 1.6; }
.note { display: block; margin-top: 18rpx; color: #84746a; font-size: 23rpx; }
.accept { height: 68rpx; margin: 26rpx 0 0; padding: 0 28rpx; border-radius: 34rpx; color: #fff; background: #30251f; font-size: 24rpx; line-height: 68rpx; }
.empty { margin-top: 40rpx; padding: 80rpx 20rpx; color: #84746a; text-align: center; }
.loading { margin-top: 60rpx; text-align: center; }
.floating { position: fixed; right: 42rpx; bottom: 180rpx; z-index: 10; width: 88rpx; height: 88rpx; margin: 0; padding: 0; border-radius: 44rpx; color: #fff; background: #cf6447; box-shadow: 0 18rpx 38rpx rgba(207,100,71,.28); font-size: 44rpx; line-height: 88rpx; }
</style>
