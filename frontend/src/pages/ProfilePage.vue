<script setup lang="ts">
import { reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

const router = useRouter()
const authStore = useAuthStore()
const familyStore = useFamilyStore()
const { currentUser } = storeToRefs(authStore)

const form = reactive({
  nickname: currentUser.value?.nickname ?? '',
})
const saving = ref(false)

function formatDate(value?: string | null) {
  if (!value) {
    return '暂无记录'
  }
  return value.replace('T', ' ').slice(0, 10)
}

async function submitProfile() {
  const nickname = form.nickname.trim()
  if (!nickname) {
    showFailToast('请输入昵称')
    return
  }
  try {
    saving.value = true
    await authStore.updateCurrentProfile({ nickname })
    form.nickname = nickname
    showSuccessToast('个人资料已保存')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '保存个人资料失败')
  } finally {
    saving.value = false
  }
}

async function logout() {
  familyStore.clearFamily()
  authStore.clearAuth()
  showSuccessToast('已退出登录')
  await router.replace('/login')
}
</script>

<template>
  <section class="yy-page space-y-5 pb-8 pt-5">
    <header class="yy-enter px-1">
      <p class="yy-kicker">My kitchen</p>
      <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">个人资料</h1>
    </header>

    <article
      class="relative overflow-hidden rounded-[32px] bg-[var(--yy-ink)] p-6 text-white shadow-[0_24px_60px_rgba(48,37,31,0.24)]"
    >
      <p class="text-sm tracking-[0.24em] text-white/70">PROFILE</p>
      <h2 class="mt-3 text-2xl font-semibold">{{ currentUser?.nickname ?? '未登录' }}</h2>
      <p class="mt-2 text-sm text-white/80">@{{ currentUser?.username ?? '-' }}</p>
      <div class="mt-5 rounded-2xl bg-white/10 px-4 py-3 text-sm">
        <p class="text-white/65">注册时间</p>
        <p class="mt-1 font-medium text-white">{{ formatDate(currentUser?.created_at) }}</p>
      </div>
    </article>

    <article class="yy-card p-5">
      <p class="text-sm text-[var(--yy-muted)]">资料编辑</p>
      <div class="mt-4 space-y-4">
        <div>
          <label class="mb-2 block text-sm text-[var(--yy-muted)]">用户名</label>
          <input
            :value="currentUser?.username ?? ''"
            type="text"
            disabled
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-muted)] outline-none"
          />
        </div>
        <div>
          <label class="mb-2 block text-sm text-[var(--yy-muted)]">昵称</label>
          <input
            v-model.trim="form.nickname"
            type="text"
            maxlength="32"
            placeholder="请输入昵称"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)] outline-none"
          />
        </div>
      </div>

      <button
        type="button"
        class="mt-5 w-full rounded-2xl bg-[var(--yy-ink)] px-4 py-4 text-sm font-medium text-white"
        :disabled="saving"
        @click="submitProfile"
      >
        保存资料
      </button>
    </article>

    <button
      type="button"
      class="w-full rounded-2xl bg-white px-4 py-4 text-sm font-medium text-[var(--yy-ink)] shadow-sm"
      @click="logout"
    >
      退出登录
    </button>
  </section>
</template>
