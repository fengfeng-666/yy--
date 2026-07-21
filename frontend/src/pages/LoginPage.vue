<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { showFailToast, showSuccessToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

const authStore = useAuthStore()
const familyStore = useFamilyStore()
const route = useRoute()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const submitting = ref(false)
const form = reactive({
  username: '',
  nickname: '',
  password: '',
})

const pageTitle = computed(() => (mode.value === 'login' ? '欢迎回来' : '创建你的私厨账号'))
const pageDescription = computed(() =>
  mode.value === 'login'
    ? '使用用户名和密码登录，继续记录今天吃什么、谁来做、吃得怎么样。'
    : '先注册一个账号，后续再继续接入家庭空间与双人协作。 ',
)
const submitText = computed(() => (mode.value === 'login' ? '进入 YY 私厨' : '注册并进入'))

function toggleMode(nextMode: 'login' | 'register') {
  mode.value = nextMode
}

async function submitForm() {
  if (!form.username.trim()) {
    showFailToast('请输入用户名')
    return
  }
  if (!form.password.trim()) {
    showFailToast('请输入密码')
    return
  }
  if (mode.value === 'register' && form.password.trim().length < 6) {
    showFailToast('密码至少需要 6 位')
    return
  }

  submitting.value = true
  try {
    if (mode.value === 'login') {
      await authStore.loginWithPassword({
        username: form.username.trim(),
        password: form.password,
      })
      await familyStore.loadCurrentFamily()
      showSuccessToast('登录成功')
    } else {
      await authStore.registerWithPassword({
        username: form.username.trim(),
        nickname: form.nickname.trim() || undefined,
        password: form.password,
      })
      familyStore.clearFamily()
      showSuccessToast('注册成功')
    }

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const fallback = familyStore.hasFamily ? '/home' : '/family/onboarding'
    await router.replace(redirect || fallback)
  } catch (error) {
    const message =
      error instanceof Error ? error.message : mode.value === 'login' ? '登录失败' : '注册失败'
    showFailToast(message)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(242,172,114,0.18),_transparent_42%),_var(--yy-cream)] px-6 py-10">
    <div class="w-full max-w-[380px] rounded-[32px] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(87,64,46,0.12)] backdrop-blur">
      <p class="text-sm font-medium tracking-[0.3em] text-[var(--yy-muted)]">YY KITCHEN</p>
      <h1 class="mt-4 text-3xl font-semibold text-[var(--yy-ink)]">{{ pageTitle }}</h1>
      <p class="mt-3 text-sm leading-6 text-[var(--yy-muted)]">
        {{ pageDescription }}
      </p>

      <div class="mt-6 inline-flex rounded-full bg-[var(--yy-cream)] p-1 text-sm">
        <button
          type="button"
          class="rounded-full px-4 py-2 transition"
          :class="mode === 'login' ? 'bg-[var(--yy-ink)] text-white' : 'text-[var(--yy-muted)]'"
          @click="toggleMode('login')"
        >
          登录
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 transition"
          :class="mode === 'register' ? 'bg-[var(--yy-ink)] text-white' : 'text-[var(--yy-muted)]'"
          @click="toggleMode('register')"
        >
          注册
        </button>
      </div>

      <form class="mt-8 space-y-4" @submit.prevent="submitForm">
        <input
          v-model.trim="form.username"
          type="text"
          autocomplete="username"
          placeholder="用户名"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
        />
        <input
          v-if="mode === 'register'"
          v-model.trim="form.nickname"
          type="text"
          autocomplete="nickname"
          placeholder="昵称（可选）"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
        />
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          placeholder="密码"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
        />

        <button
          type="submit"
          class="w-full rounded-full bg-[var(--yy-ink)] px-5 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="submitting"
        >
          {{ submitting ? '提交中...' : submitText }}
        </button>
      </form>

      <div class="mt-5 flex items-center justify-between text-sm text-[var(--yy-muted)]">
        <span>{{ mode === 'login' ? '还没有账号？去注册' : '已有账号？去登录' }}</span>
        <button
          type="button"
          class="text-[var(--yy-ink)]"
          @click="toggleMode(mode === 'login' ? 'register' : 'login')"
        >
          {{ mode === 'login' ? '切换注册' : '切换登录' }}
        </button>
      </div>
    </div>
  </section>
</template>
