<script setup lang="ts">
defineProps<{ active: 'home' | 'dishes' | 'orders' | 'profile' }>()

const tabs = [
  { key: 'home', label: '首页', icon: '⌂', url: '/pages/home/index' },
  { key: 'dishes', label: '菜单', icon: '♨', url: '/pages/dishes/index' },
  { key: 'orders', label: '点菜', icon: '✦', url: '/pages/orders/index' },
  { key: 'profile', label: '我的', icon: '○', url: '/pages/profile/index' },
] as const

function navigate(url: string) {
  uni.reLaunch({ url })
}
</script>

<template>
  <view class="tab-shell">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item"
      :class="{ active: active === tab.key }"
      @tap="navigate(tab.url)"
    >
      <text class="tab-icon">{{ tab.icon }}</text>
      <text class="tab-label">{{ tab.label }}</text>
    </button>
  </view>
</template>

<style scoped lang="scss">
.tab-shell {
  position: fixed;
  right: 24rpx;
  bottom: calc(24rpx + env(safe-area-inset-bottom));
  left: 24rpx;
  z-index: 20;
  display: flex;
  padding: 12rpx;
  border-radius: 36rpx;
  background: rgba(48, 37, 31, 0.96);
  box-shadow: 0 18rpx 50rpx rgba(48, 37, 31, 0.26);
}

.tab-item {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  margin: 0;
  padding: 0;
  border-radius: 28rpx;
  color: rgba(255, 255, 255, 0.52);
  background: transparent;
  line-height: 1;
}

.tab-item.active {
  color: #30251f;
  background: #fffdf9;
}

.tab-icon {
  font-size: 30rpx;
}

.tab-label {
  margin-top: 8rpx;
  font-size: 20rpx;
}
</style>
