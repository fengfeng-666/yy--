<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '还没有加入家庭',
    description: '准备好后再创建家庭，或者输入家人分享的邀请码加入。',
  },
)

function openFamily(mode: 'create' | 'join') {
  uni.navigateTo({ url: `/pages/family/index?mode=${mode}` })
}
</script>

<template>
  <view class="no-family yy-card">
    <view class="icon">⌂</view>
    <text class="title">{{ title }}</text>
    <text class="description">{{ description }}</text>
    <view class="buttons">
      <button class="join" @tap="openFamily('join')">加入家庭</button>
      <button class="create" @tap="openFamily('create')">创建家庭</button>
    </view>
    <text class="hint">不想现在操作也没关系，之后可随时从“我的”进入。</text>
  </view>
</template>

<style scoped lang="scss">
.no-family { display: flex; flex-direction: column; align-items: center; margin-top: 40rpx; padding: 52rpx 36rpx; text-align: center; }
.icon { display: flex; width: 112rpx; height: 112rpx; align-items: center; justify-content: center; border-radius: 36rpx; color: #cf6447; background: rgba(233,154,92,.16); font-size: 50rpx; }
.title { margin-top: 30rpx; font-family: 'Songti SC', serif; font-size: 40rpx; font-weight: 700; }
.description { margin-top: 16rpx; color: #84746a; font-size: 24rpx; line-height: 1.7; }
.buttons { display: flex; width: 100%; margin-top: 36rpx; gap: 18rpx; }
.buttons button { flex: 1; height: 82rpx; margin: 0; border-radius: 28rpx; font-size: 25rpx; line-height: 82rpx; }
.join { color: #fff; background: #30251f; }
.create { color: #30251f; background: #f8f3eb; }
.hint { margin-top: 24rpx; color: #a29389; font-size: 20rpx; }
</style>
