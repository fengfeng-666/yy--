<script setup lang="ts">
import { reactive, ref } from 'vue'

import { createFamily, joinFamily } from '@/api'
import { session } from '@/stores/session'
import { showError } from '@/utils/request'

const mode = ref<'create' | 'join'>('create')
const loading = ref(false)
const form = reactive({ name: '', description: '', inviteCode: '' })

async function submit() {
  loading.value = true
  try {
    const result =
      mode.value === 'create'
        ? await createFamily(form.name.trim(), form.description.trim() || undefined)
        : await joinFamily(form.inviteCode.trim().toUpperCase())
    session.family = result.family
    uni.reLaunch({ url: '/pages/home/index' })
  } catch (error) {
    showError(error, mode.value === 'create' ? '创建家庭失败' : '加入家庭失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="yy-page family-page">
    <text class="yy-kicker">Family Space</text>
    <text class="yy-title">建立你们的<br />家庭餐桌</text>
    <text class="intro yy-muted">创建一个新家庭，或者输入对方分享的邀请码加入。</text>

    <view class="mode-tabs yy-card">
      <button :class="{ active: mode === 'create' }" @tap="mode = 'create'">创建家庭</button>
      <button :class="{ active: mode === 'join' }" @tap="mode = 'join'">输入邀请码</button>
    </view>

    <view class="form-card yy-card">
      <template v-if="mode === 'create'">
        <text class="field-label">家庭名称</text>
        <input v-model="form.name" class="field" maxlength="100" placeholder="例如：YY私厨" />
        <text class="field-label">一句介绍（可选）</text>
        <textarea v-model="form.description" class="field textarea" maxlength="255" placeholder="属于两个人的小餐桌" />
      </template>
      <template v-else>
        <text class="field-label">家庭邀请码</text>
        <input v-model="form.inviteCode" class="field invite" maxlength="20" placeholder="请输入邀请码" />
      </template>
      <button class="yy-primary submit" :loading="loading" :disabled="loading" @tap="submit">
        {{ mode === 'create' ? '创建并进入' : '加入并进入' }}
      </button>
    </view>
  </view>
</template>

<style scoped lang="scss">
.family-page { padding-top: 72rpx; }
.intro { display: block; margin-top: 24rpx; font-size: 26rpx; line-height: 1.7; }
.mode-tabs { display: flex; margin-top: 48rpx; padding: 10rpx; }
.mode-tabs button { flex: 1; height: 72rpx; margin: 0; border-radius: 28rpx; color: #84746a; background: transparent; font-size: 26rpx; }
.mode-tabs button.active { color: #fff; background: #30251f; }
.form-card { margin-top: 24rpx; padding: 36rpx; }
.field-label { display: block; margin: 20rpx 0 14rpx; color: #84746a; font-size: 24rpx; }
.field { width: 100%; height: 88rpx; padding: 0 28rpx; border-radius: 26rpx; background: #f8f3eb; font-size: 28rpx; }
.textarea { height: 180rpx; padding-top: 24rpx; }
.invite { letter-spacing: 6rpx; text-transform: uppercase; }
.submit { margin-top: 44rpx; }
</style>
