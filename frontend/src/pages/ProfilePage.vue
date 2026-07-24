<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'
import { BookHeart, ChevronRight, Copy, HousePlus, UsersRound } from 'lucide-vue-next'

import { useAiChatStore } from '@/stores/aiChat'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useFamilyStore } from '@/stores/family'

const router = useRouter()
const aiChatStore = useAiChatStore()
const authStore = useAuthStore()
const chatStore = useChatStore()
const familyStore = useFamilyStore()
const { currentUser } = storeToRefs(authStore)
const { currentFamily, hasFamily, inviteCode, members } = storeToRefs(familyStore)

const form = reactive({
  nickname: currentUser.value?.nickname ?? '',
})
const joinForm = reactive({
  inviteCode: '',
})
const saving = ref(false)
const joining = ref(false)
const memberCountText = computed(() => `${members.value.length}/${currentFamily.value?.max_members ?? 2} 位成员`)

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

async function copyInviteCode() {
  if (!inviteCode.value) {
    return
  }

  try {
    await navigator.clipboard.writeText(inviteCode.value)
    showSuccessToast('邀请码已复制')
  } catch {
    showFailToast('复制失败，请长按邀请码复制')
  }
}

async function joinFamily() {
  const code = joinForm.inviteCode.trim().toUpperCase()
  if (!code) {
    showFailToast('请输入家庭邀请码')
    return
  }

  try {
    joining.value = true
    await familyStore.joinFamilySpace({ invite_code: code })
    joinForm.inviteCode = ''
    showSuccessToast('已加入家庭')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加入家庭失败')
  } finally {
    joining.value = false
  }
}

async function logout() {
  aiChatStore.reset()
  chatStore.reset()
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

    <button
      type="button"
      class="yy-card yy-soft-button flex w-full items-center gap-4 p-5 text-left"
      @click="router.push('/journal')"
    >
      <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]">
        <BookHeart class="h-5 w-5" :stroke-width="2" />
      </span>
      <span class="min-w-0 flex-1">
        <span class="block text-xs font-medium tracking-[0.16em] text-[var(--yy-muted)]">DINING JOURNAL</span>
        <span class="mt-1 block text-lg font-semibold text-[var(--yy-ink)]">用餐食记</span>
        <span class="mt-1 block text-sm text-[var(--yy-muted)]">回顾一起认真吃过的每一顿饭</span>
      </span>
      <ChevronRight class="h-5 w-5 shrink-0 text-[var(--yy-muted)]" />
    </button>

    <article v-if="hasFamily" class="yy-card overflow-hidden">
      <div class="flex items-start gap-3 border-b border-[var(--yy-line)] px-5 py-5">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-sage)]/15 text-[var(--yy-sage)]">
          <UsersRound class="h-5 w-5" :stroke-width="2" />
        </span>
        <div class="min-w-0 flex-1">
          <p class="text-xs font-medium tracking-[0.16em] text-[var(--yy-muted)]">MY FAMILY</p>
          <div class="mt-1 flex items-center justify-between gap-3">
            <h2 class="truncate text-lg font-semibold text-[var(--yy-ink)]">{{ currentFamily?.name }}</h2>
            <span class="shrink-0 text-xs text-[var(--yy-muted)]">{{ memberCountText }}</span>
          </div>
          <p v-if="currentFamily?.description" class="mt-1 line-clamp-2 text-sm leading-6 text-[var(--yy-muted)]">
            {{ currentFamily.description }}
          </p>
        </div>
      </div>

      <div class="px-5 py-5">
        <p class="text-sm text-[var(--yy-muted)]">家庭邀请码</p>
        <div class="mt-3 flex items-center gap-3">
          <button
            type="button"
            class="flex min-w-0 flex-1 items-center justify-between rounded-2xl bg-[var(--yy-cream)] px-4 py-3 text-left"
            aria-label="复制家庭邀请码"
            @click="copyInviteCode"
          >
            <span class="truncate font-mono text-xl font-bold tracking-[0.18em] text-[var(--yy-ink)]">{{ inviteCode }}</span>
            <Copy class="ml-3 h-4 w-4 shrink-0 text-[var(--yy-muted)]" :stroke-width="2" />
          </button>
        </div>
        <p class="mt-3 text-xs leading-5 text-[var(--yy-muted)]">把邀请码发给家人，对方即可加入同一个家庭空间。</p>
      </div>
    </article>

    <article v-else class="yy-card p-5">
      <div class="flex items-start gap-3">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]">
          <HousePlus class="h-5 w-5" :stroke-width="2" />
        </span>
        <div>
          <h2 class="text-lg font-semibold text-[var(--yy-ink)]">加入家庭</h2>
          <p class="mt-1 text-sm leading-6 text-[var(--yy-muted)]">输入家人分享给你的邀请码，立即加入同一个家庭空间。</p>
        </div>
      </div>

      <form class="mt-5 space-y-3" @submit.prevent="joinFamily">
        <label class="sr-only" for="profile-invite-code">家庭邀请码</label>
        <input
          id="profile-invite-code"
          v-model.trim="joinForm.inviteCode"
          type="text"
          maxlength="20"
          autocomplete="off"
          placeholder="请输入家庭邀请码"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm uppercase tracking-[0.15em] text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
        />
        <button
          type="submit"
          class="w-full rounded-2xl bg-[var(--yy-ink)] px-4 py-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="joining"
        >
          {{ joining ? '正在加入…' : '加入家庭' }}
        </button>
        <button
          type="button"
          class="w-full rounded-2xl bg-[var(--yy-cream)] px-4 py-3.5 text-sm font-medium text-[var(--yy-ink)]"
          @click="router.push({ name: 'family-onboarding', query: { mode: 'create' } })"
        >
          创建一个新家庭
        </button>
      </form>
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
