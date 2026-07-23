<script setup lang="ts">
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { fetchCurrentFamily, joinFamily } from '@/api'
import YyTabBar from '@/components/YyTabBar.vue'
import { clearSession, session } from '@/stores/session'
import { showError } from '@/utils/request'

const joining = ref(false)
const joinForm = reactive({ inviteCode: '' })

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

async function submitJoin() {
  const inviteCode = joinForm.inviteCode.trim().toUpperCase()
  if (!inviteCode) {
    uni.showToast({ title: '请输入家庭邀请码', icon: 'none' })
    return
  }

  joining.value = true
  try {
    const result = await joinFamily(inviteCode)
    session.family = result.family
    joinForm.inviteCode = ''
    uni.showToast({ title: '已加入家庭', icon: 'success' })
  } catch (error) {
    showError(error, '加入家庭失败')
  } finally {
    joining.value = false
  }
}

function logout() {
  clearSession()
  uni.reLaunch({ url: '/pages/login/index' })
}

function goCreateFamily() {
  uni.navigateTo({ url: '/pages/family/index?mode=create' })
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
      <view class="family-heading">
        <view>
          <text class="label">我的家庭</text>
          <text class="family-name">{{ session.family.name }}</text>
        </view>
        <text class="member-count">{{ session.family.members.length }} 位成员</text>
      </view>
      <text class="label invite-label">家庭邀请码</text>
      <view class="invite-row">
        <text class="invite-code">{{ session.family.invite_code }}</text>
        <button @tap="copyInviteCode">复制</button>
      </view>
      <text class="hint">把邀请码发给对方，即可加入同一个家庭空间。</text>
    </view>

    <view v-else class="join-card yy-card">
      <text class="join-title">加入家庭</text>
      <text class="join-copy">输入家人分享给你的邀请码，加入同一个家庭空间。</text>
      <input
        v-model="joinForm.inviteCode"
        class="join-input"
        maxlength="20"
        placeholder="请输入家庭邀请码"
      />
      <button class="join-button" :loading="joining" :disabled="joining" @tap="submitJoin">
        {{ joining ? '正在加入…' : '加入家庭' }}
      </button>
      <button class="create-button" @tap="goCreateFamily">创建一个新家庭</button>
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
.family-heading { display: flex; align-items: flex-start; justify-content: space-between; padding-bottom: 28rpx; border-bottom: 1rpx solid #eadfd4; }
.family-name { display: block; margin-top: 10rpx; font-size: 32rpx; font-weight: 600; }
.member-count { color: #84746a; font-size: 22rpx; }
.invite-label { display: block; margin-top: 28rpx; }
.invite-row { display: flex; align-items: center; justify-content: space-between; margin-top: 20rpx; }
.invite-code { font-family: Georgia, serif; font-size: 40rpx; font-weight: 700; letter-spacing: 5rpx; }
.invite-row button { height: 60rpx; margin: 0; padding: 0 24rpx; border-radius: 30rpx; color: #fff; background: #30251f; font-size: 22rpx; line-height: 60rpx; }
.hint { display: block; margin-top: 22rpx; color: #84746a; font-size: 22rpx; line-height: 1.6; }
.join-card { margin-top: 26rpx; padding: 36rpx; }
.join-title { display: block; font-size: 32rpx; font-weight: 600; }
.join-copy { display: block; margin-top: 12rpx; color: #84746a; font-size: 23rpx; line-height: 1.65; }
.join-input { width: 100%; height: 88rpx; margin-top: 28rpx; padding: 0 28rpx; border-radius: 26rpx; background: #f8f3eb; font-size: 28rpx; letter-spacing: 5rpx; text-transform: uppercase; }
.join-button { height: 84rpx; margin-top: 20rpx; border-radius: 30rpx; color: #fff; background: #30251f; font-size: 26rpx; line-height: 84rpx; }
.create-button { height: 78rpx; margin-top: 16rpx; border-radius: 28rpx; color: #30251f; background: #f8f3eb; font-size: 24rpx; line-height: 78rpx; }
.logout { height: 84rpx; margin-top: 28rpx; border-radius: 30rpx; color: #cf6447; background: #fffdf9; font-size: 26rpx; line-height: 84rpx; }
</style>
