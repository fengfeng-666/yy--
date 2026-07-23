<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import { fetchCurrentFamily, wechatLogin } from '@/api'
import { applyAuth, session } from '@/stores/session'
import { ApiRequestError, showError } from '@/utils/request'

const loading = ref(false)

onLoad(async () => {
  if (session.token) {
    await routeAuthenticatedUser()
  }
})

async function routeAuthenticatedUser() {
  try {
    session.family = await fetchCurrentFamily()
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) return
    if (error instanceof ApiRequestError && error.statusCode !== 404) throw error
    session.family = null
  }
  uni.reLaunch({ url: '/pages/home/index' })
}

async function login() {
  loading.value = true
  try {
    const result = await uni.login({ provider: 'weixin' })
    if (!result.code) throw new Error('未获取到微信登录凭证')
    applyAuth(await wechatLogin(result.code))

    await routeAuthenticatedUser()
  } catch (error) {
    showError(error, '微信登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="login-page">
    <view class="glow glow-top" />
    <view class="glow glow-bottom" />
    <view class="brand-card">
      <view class="brand-mark">YY</view>
      <text class="yy-kicker">Private Kitchen</text>
      <text class="login-title">今天也要<br />好好吃饭</text>
      <text class="login-copy">两个人的家庭菜单、点菜提醒和每一顿饭的温暖记录。</text>

      <button class="wechat-button" :loading="loading" :disabled="loading" @tap="login">
        <text class="wechat-dot">●</text>
        <text>{{ loading ? '正在登录…' : '微信快捷登录' }}</text>
      </button>
      <text class="agreement">登录即表示你同意仅将微信身份用于家庭空间识别</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.login-page {
  position: relative;
  display: flex;
  min-height: 100vh;
  align-items: center;
  padding: 48rpx;
  overflow: hidden;
}

.glow {
  position: absolute;
  width: 520rpx;
  height: 520rpx;
  border-radius: 50%;
  filter: blur(80rpx);
}

.glow-top {
  top: -220rpx;
  left: -180rpx;
  background: rgba(233, 154, 92, 0.24);
}

.glow-bottom {
  right: -220rpx;
  bottom: -200rpx;
  background: rgba(131, 151, 121, 0.2);
}

.brand-card {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  flex-direction: column;
  padding: 64rpx 48rpx 48rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  border-radius: 56rpx;
  background: rgba(255, 253, 249, 0.9);
  box-shadow: 0 40rpx 100rpx rgba(77, 53, 38, 0.14);
}

.brand-mark {
  display: flex;
  width: 88rpx;
  height: 88rpx;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
  border-radius: 28rpx;
  color: #fff;
  background: #30251f;
  font-family: Georgia, serif;
  font-size: 30rpx;
  font-weight: 700;
}

.login-title {
  margin-top: 24rpx;
  font-family: 'Songti SC', serif;
  font-size: 72rpx;
  font-weight: 700;
  line-height: 1.18;
}

.login-copy {
  margin-top: 28rpx;
  color: #84746a;
  font-size: 27rpx;
  line-height: 1.8;
}

.wechat-button {
  display: flex;
  height: 96rpx;
  align-items: center;
  justify-content: center;
  margin-top: 64rpx;
  border-radius: 48rpx;
  color: #fff;
  background: #07c160;
  font-size: 30rpx;
  font-weight: 600;
}

.wechat-dot {
  margin-right: 16rpx;
  font-size: 22rpx;
}

.agreement {
  margin-top: 24rpx;
  color: #a29389;
  font-size: 20rpx;
  line-height: 1.6;
  text-align: center;
}
</style>
