<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'

import { fetchCurrentFamily } from '@/api'
import YyTabBar from '@/components/YyTabBar.vue'
import { clearSession, session } from '@/stores/session'

onShow(async () => {
  try {
    session.family = await fetchCurrentFamily()
  } catch {
    session.family = null
  }
})

function copyInviteCode() {
  if (!session.family?.invite_code) return
  uni.setClipboardData({ data: session.family.invite_code })
}

function logout() {
  clearSession()
  uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<template>
  <view class="yy-page profile-page">
    <text class="yy-kicker">My Kitchen</text>
    <text class="yy-title">我的</text>

    <view class="profile-card">
      <text class="avatar">{{ session.user?.nickname?.slice(0, 1) || 'Y' }}</text>
      <text class="nickname">{{ session.user?.nickname || '微信用户' }}</text>
      <text class="username">{{ session.family?.name || '尚未加入家庭' }}</text>
    </view>

    <view v-if="session.family" class="family-card yy-card">
      <text class="label">家庭邀请码</text>
      <view class="invite-row">
        <text class="invite-code">{{ session.family.invite_code }}</text>
        <button @tap="copyInviteCode">复制</button>
      </view>
      <text class="hint">把邀请码发给对方，即可加入同一个家庭空间。</text>
    </view>

    <button class="logout" @tap="logout">退出登录</button>
    <YyTabBar active="profile" />
  </view>
</template>

<style scoped lang="scss">
.profile-page { padding-top: 56rpx; }
.profile-card { display: flex; flex-direction: column; align-items: center; margin-top: 40rpx; padding: 56rpx; border-radius: 48rpx; color: #fff; background: #30251f; }
.avatar { display: flex; width: 104rpx; height: 104rpx; align-items: center; justify-content: center; border-radius: 52rpx; color: #30251f; background: #f4cba8; font-family: 'Songti SC', serif; font-size: 44rpx; font-weight: 700; }
.nickname { margin-top: 24rpx; font-size: 38rpx; font-weight: 600; }
.username { margin-top: 12rpx; color: rgba(255,255,255,.6); font-size: 24rpx; }
.family-card { margin-top: 26rpx; padding: 36rpx; }
.label { color: #84746a; font-size: 23rpx; }
.invite-row { display: flex; align-items: center; justify-content: space-between; margin-top: 20rpx; }
.invite-code { font-family: Georgia, serif; font-size: 40rpx; font-weight: 700; letter-spacing: 5rpx; }
.invite-row button { height: 60rpx; margin: 0; padding: 0 24rpx; border-radius: 30rpx; color: #fff; background: #30251f; font-size: 22rpx; line-height: 60rpx; }
.hint { display: block; margin-top: 22rpx; color: #84746a; font-size: 22rpx; line-height: 1.6; }
.logout { height: 84rpx; margin-top: 28rpx; border-radius: 30rpx; color: #cf6447; background: #fffdf9; font-size: 26rpx; line-height: 84rpx; }
</style>
