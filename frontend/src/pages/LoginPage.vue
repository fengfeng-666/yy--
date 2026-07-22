<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { showFailToast, showSuccessToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, ChefHat, Sparkles } from 'lucide-vue-next'

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
  <section class="relative flex min-h-screen items-center justify-center overflow-hidden bg-[var(--yy-cream)] px-6 py-10">
    <div class="absolute -left-28 -top-28 h-72 w-72 rounded-full bg-[var(--yy-apricot)]/20 blur-3xl" aria-hidden="true"></div>
    <div class="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-[var(--yy-sage)]/20 blur-3xl" aria-hidden="true"></div>

    <div class="yy-enter relative w-full max-w-[410px] overflow-hidden rounded-[38px] border border-white/80 bg-white/85 p-8 shadow-[0_30px_90px_rgba(77,53,38,0.14)] backdrop-blur-xl">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--yy-ink)] text-white">
            <ChefHat class="h-5 w-5" />
          </span>
          <div>
            <p class="yy-kicker">YY Private Kitchen</p>
            <p class="mt-0.5 text-xs text-[var(--yy-muted)]">两个人的家庭餐桌</p>
          </div>
        </div>
        <Sparkles class="h-5 w-5 text-[var(--yy-apricot)]" aria-hidden="true" />
      </div>

      <h1 class="yy-display mt-9 text-[36px] font-bold leading-tight text-[var(--yy-ink)]">{{ pageTitle }}</h1>
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
          aria-label="用户名"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3.5 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)] focus:bg-white"
        />
        <input
          v-if="mode === 'register'"
          v-model.trim="form.nickname"
          type="text"
          autocomplete="nickname"
          placeholder="昵称（可选）"
          aria-label="昵称"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3.5 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)] focus:bg-white"
        />
        <input
          v-model="form.password"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          placeholder="密码"
          aria-label="密码"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3.5 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)] focus:bg-white"
        />

        <button
          type="submit"
          class="yy-primary-button flex w-full items-center justify-center gap-2 rounded-full bg-[var(--yy-ink)] px-5 py-3.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="submitting"
        >
          {{ submitting ? '提交中...' : submitText }}
          <ArrowRight v-if="!submitting" class="h-4 w-4" />
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
