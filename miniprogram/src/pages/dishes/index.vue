<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { fetchDishes } from '@/api'
import YyTabBar from '@/components/YyTabBar.vue'
import type { DishItem } from '@/types/api'
import { resolveAssetUrl, showError } from '@/utils/request'

const dishes = ref<DishItem[]>([])
const keyword = ref('')
const filtered = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  return value
    ? dishes.value.filter((dish) => `${dish.name} ${dish.description || ''}`.toLowerCase().includes(value))
    : dishes.value
})

async function load() {
  try {
    dishes.value = await fetchDishes()
  } catch (error) {
    showError(error, '菜单加载失败')
  } finally {
    uni.stopPullDownRefresh()
  }
}

function goOrder(dishId: number) {
  uni.navigateTo({ url: `/pages/order-create/index?dishId=${dishId}` })
}

onShow(load)
onPullDownRefresh(load)
</script>

<template>
  <view class="yy-page dishes-page">
    <text class="yy-kicker">Family Menu</text>
    <text class="yy-title">今天想吃什么</text>
    <text class="subtitle yy-muted">把你们的拿手菜，慢慢攒成一本家庭菜单。</text>

    <view class="search yy-card">
      <text>⌕</text>
      <input v-model="keyword" placeholder="搜索菜名或描述" />
      <text class="count">{{ filtered.length }} 道</text>
    </view>

    <view v-if="filtered.length" class="dish-list">
      <view v-for="dish in filtered" :key="dish.id" class="dish yy-card">
        <image v-if="dish.image_url" class="dish-image" mode="aspectFill" :src="resolveAssetUrl(dish.image_url)" />
        <view v-else class="dish-image placeholder">♨</view>
        <view class="dish-info">
          <view class="dish-top">
            <text class="dish-name">{{ dish.name }}</text>
            <text class="status" :class="{ off: !dish.is_available }">{{ dish.is_available ? '可点' : '下架' }}</text>
          </view>
          <text class="price">¥ {{ dish.price.toFixed(2) }}</text>
          <text class="description">{{ dish.description || '这道菜还没有介绍。' }}</text>
          <button
            class="order-button"
            :disabled="!dish.is_available"
            @tap="goOrder(dish.id)"
          >
            点这道菜
          </button>
        </view>
      </view>
    </view>
    <view v-else class="empty yy-card">{{ keyword ? '没有找到这道菜' : '家庭菜单还是空的' }}</view>
    <YyTabBar active="dishes" />
  </view>
</template>

<style scoped lang="scss">
.dishes-page { padding-top: 56rpx; }
.subtitle { display: block; margin-top: 18rpx; font-size: 25rpx; }
.search { display: flex; height: 88rpx; align-items: center; margin-top: 38rpx; padding: 0 26rpx; gap: 18rpx; }
.search input { flex: 1; font-size: 26rpx; }
.count { padding: 8rpx 18rpx; border-radius: 20rpx; color: #84746a; background: #f8f3eb; font-size: 20rpx; }
.dish-list { margin-top: 24rpx; }
.dish { display: flex; margin-bottom: 22rpx; padding: 20rpx; }
.dish-image { display: flex; width: 196rpx; height: 196rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 30rpx; background: #f4cba8; font-size: 54rpx; }
.dish-info { display: flex; min-width: 0; flex: 1; flex-direction: column; padding: 4rpx 0 0 24rpx; }
.dish-top { display: flex; align-items: center; justify-content: space-between; }
.dish-name { overflow: hidden; font-size: 31rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.status { padding: 7rpx 14rpx; border-radius: 18rpx; color: #627459; background: #edf2e9; font-size: 19rpx; }
.status.off { color: #84746a; background: #eee; }
.price { margin-top: 10rpx; color: #cf6447; font-size: 28rpx; font-weight: 600; }
.description { display: -webkit-box; margin-top: 10rpx; overflow: hidden; color: #84746a; font-size: 22rpx; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.order-button { align-self: flex-start; height: 54rpx; margin: auto 0 0; padding: 0 22rpx; border-radius: 27rpx; color: #fff; background: #30251f; font-size: 21rpx; line-height: 54rpx; }
.empty { margin-top: 28rpx; padding: 80rpx 30rpx; color: #84746a; font-size: 26rpx; text-align: center; }
</style>
