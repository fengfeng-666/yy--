<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { fetchCurrentFamily, fetchHomeSummary } from '@/api'
import YyTabBar from '@/components/YyTabBar.vue'
import { session } from '@/stores/session'
import type { HomeSummary, MealOrder } from '@/types/api'
import { showError } from '@/utils/request'
import { requestSubscriptions } from '@/utils/subscriptions'

const loading = ref(false)
const summary = ref<HomeSummary | null>(null)
const todayOrder = computed(() => summary.value?.today_order ?? null)

function orderText(order: MealOrder) {
  return order.items.map((item) => `${item.dish.name} × ${item.quantity}`).join('、')
}

async function load() {
  loading.value = true
  try {
    const [family, home] = await Promise.all([fetchCurrentFamily(), fetchHomeSummary()])
    session.family = family
    summary.value = home
  } catch (error) {
    showError(error, '首页加载失败')
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

async function enableReminder() {
  try {
    const accepted = await requestSubscriptions(['new_order'])
    uni.showToast({ title: accepted.length ? '点菜提醒已开启' : '你暂未允许提醒', icon: 'none' })
  } catch (error) {
    showError(error, '开启提醒失败')
  }
}

function goCreateOrder() {
  uni.navigateTo({ url: '/pages/order-create/index' })
}

function goDishes() {
  uni.reLaunch({ url: '/pages/dishes/index' })
}

onShow(load)
onPullDownRefresh(load)
</script>

<template>
  <view class="yy-page">
    <view class="header">
      <view>
        <text class="yy-kicker">YY Private Kitchen</text>
        <text class="greeting">你好，{{ session.user?.nickname || '微信用户' }}</text>
      </view>
      <button class="bell" @tap="enableReminder">🔔</button>
    </view>

    <view class="hero">
      <text class="hero-label">TODAY'S TABLE</text>
      <text class="hero-title">{{ todayOrder ? orderText(todayOrder) : '今天，想吃点什么？' }}</text>
      <text class="hero-copy">
        {{ todayOrder ? `${todayOrder.cook.nickname} 掌勺 · ${todayOrder.status === 'accepted' ? '已接单' : '等待确认'}` : '把想吃的告诉对方，让一顿饭成为今天的小期待。' }}
      </text>
      <button class="hero-button" @tap="goCreateOrder">＋ 发起点菜</button>
    </view>

    <view class="section-head">
      <text class="section-title">家的用餐小记</text>
      <text class="yy-muted">{{ session.family?.name || '' }}</text>
    </view>
    <view class="stats">
      <view class="stat yy-card">
        <text class="stat-number">{{ summary?.pending_to_me_count ?? 0 }}</text>
        <text class="stat-label">份等你确认</text>
      </view>
      <view class="stat yy-card">
        <text class="stat-number">{{ summary?.monthly_accepted_orders_count ?? 0 }}</text>
        <text class="stat-label">本月一起吃饭</text>
      </view>
    </view>

    <view class="actions">
      <button class="action tomato" @tap="goCreateOrder">发起点菜 <text>→</text></button>
      <button class="action light" @tap="goDishes">看看菜单 <text>→</text></button>
    </view>

    <view v-if="loading" class="loading yy-muted">正在准备今天的餐桌…</view>
    <YyTabBar active="home" />
  </view>
</template>

<style scoped lang="scss">
.header { display: flex; align-items: center; justify-content: space-between; padding-top: 12rpx; }
.greeting { display: block; margin-top: 14rpx; font-family: 'Songti SC', serif; font-size: 46rpx; font-weight: 700; }
.bell { width: 80rpx; height: 80rpx; margin: 0; padding: 0; border-radius: 40rpx; background: #fffdf9; font-size: 30rpx; line-height: 80rpx; }
.hero { position: relative; display: flex; flex-direction: column; margin-top: 40rpx; padding: 48rpx; overflow: hidden; border-radius: 52rpx; color: #fff; background: #30251f; box-shadow: 0 36rpx 80rpx rgba(48,37,31,.24); }
.hero-label { color: #f4cba8; font-size: 20rpx; font-weight: 700; letter-spacing: 4rpx; }
.hero-title { margin-top: 28rpx; font-family: 'Songti SC', serif; font-size: 54rpx; font-weight: 700; line-height: 1.3; }
.hero-copy { margin-top: 24rpx; color: rgba(255,255,255,.62); font-size: 25rpx; line-height: 1.7; }
.hero-button { align-self: flex-start; height: 76rpx; margin: 44rpx 0 0; padding: 0 30rpx; border-radius: 38rpx; color: #30251f; background: #fff; font-size: 26rpx; line-height: 76rpx; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; margin: 52rpx 6rpx 20rpx; }
.section-title { font-family: 'Songti SC', serif; font-size: 38rpx; font-weight: 700; }
.stats { display: flex; gap: 20rpx; }
.stat { display: flex; flex: 1; flex-direction: column; padding: 34rpx; }
.stat-number { font-family: Georgia, serif; font-size: 64rpx; font-weight: 700; }
.stat-label { margin-top: 12rpx; color: #84746a; font-size: 23rpx; }
.actions { display: flex; gap: 20rpx; margin-top: 22rpx; }
.action { display: flex; flex: 1; height: 104rpx; align-items: center; justify-content: space-between; margin: 0; padding: 0 28rpx; border-radius: 32rpx; font-size: 27rpx; }
.tomato { color: #fff; background: #cf6447; }
.light { color: #30251f; background: #ede1d2; }
.loading { margin-top: 30rpx; text-align: center; font-size: 24rpx; }
</style>
