<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useFamilyStore } from '@/stores/family'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()
const familyStore = useFamilyStore()
const { currentUser } = storeToRefs(authStore)
const { familyName } = storeToRefs(appStore)
const { currentFamily, inviteCode, members } = storeToRefs(familyStore)

async function logout() {
  familyStore.clearFamily()
  authStore.clearAuth()
  showSuccessToast('已退出登录')
  await router.replace('/login')
}
</script>

<template>
  <section class="space-y-4 px-5 pb-8 pt-6">
    <header>
      <p class="text-sm text-[var(--yy-muted)]">我的</p>
      <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">家庭与个人设置</h1>
    </header>

    <article class="rounded-[28px] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <p class="text-sm text-[var(--yy-muted)]">当前家庭</p>
      <h2 class="mt-1 text-lg font-semibold text-[var(--yy-ink)]">{{ familyName }}</h2>
      <p class="mt-2 text-sm text-[var(--yy-muted)]">
        {{ currentFamily?.description ?? '只属于我们的两人食堂' }}
      </p>
      <p class="mt-3 text-xs tracking-[0.18em] text-[var(--yy-muted)]">
        邀请码：{{ inviteCode || '暂未生成' }}
      </p>
    </article>

    <article class="rounded-[28px] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <p class="text-sm text-[var(--yy-muted)]">当前账号</p>
      <h2 class="mt-1 text-lg font-semibold text-[var(--yy-ink)]">{{ currentUser?.nickname ?? '未登录' }}</h2>
      <p class="mt-2 text-sm text-[var(--yy-muted)]">@{{ currentUser?.username ?? '-' }}</p>
    </article>

    <article class="rounded-[28px] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <div class="flex items-center justify-between">
        <p class="text-sm text-[var(--yy-muted)]">家庭成员</p>
        <span class="text-sm text-[var(--yy-muted)]">{{ members.length }}/2</span>
      </div>
      <div class="mt-4 space-y-3">
        <div
          v-for="member in members"
          :key="member.id"
          class="flex items-center justify-between rounded-2xl bg-[var(--yy-cream)] px-4 py-3 text-sm"
        >
          <div>
            <p class="font-medium text-[var(--yy-ink)]">{{ member.user.nickname }}</p>
            <p class="mt-1 text-[var(--yy-muted)]">@{{ member.user.username }}</p>
          </div>
          <span class="rounded-full bg-white px-3 py-1 text-xs text-[var(--yy-muted)]">
            {{ member.role === 'owner' ? '管理员' : '成员' }}
          </span>
        </div>
      </div>
    </article>

    <div class="space-y-3">
      <div class="rounded-2xl bg-white px-4 py-4 text-sm text-[var(--yy-ink)] shadow-sm">个人资料</div>
      <div class="rounded-2xl bg-white px-4 py-4 text-sm text-[var(--yy-ink)] shadow-sm">家庭信息</div>
      <div class="rounded-2xl bg-white px-4 py-4 text-sm text-[var(--yy-ink)] shadow-sm">菜品管理</div>
      <div class="rounded-2xl bg-white px-4 py-4 text-sm text-[var(--yy-ink)] shadow-sm">通知设置</div>
    </div>

    <button
      type="button"
      class="w-full rounded-2xl bg-[var(--yy-ink)] px-4 py-4 text-sm font-medium text-white"
      @click="logout"
    >
      退出登录
    </button>
  </section>
</template>
