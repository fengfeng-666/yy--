<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { showFailToast, showSuccessToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import { useFamilyStore } from '@/stores/family'

const router = useRouter()
const route = useRoute()
const familyStore = useFamilyStore()

const mode = ref<'create' | 'join'>(route.query.mode === 'join' ? 'join' : 'create')
const submitting = ref(false)
const createForm = reactive({
  name: '',
  description: '',
})
const joinForm = reactive({
  inviteCode: '',
})

const title = computed(() => (mode.value === 'create' ? '创建你们的家庭空间' : '加入已有家庭空间'))
const description = computed(() =>
  mode.value === 'create'
    ? '创建后你会自动成为管理员，并获得一个可分享的邀请码。'
    : '向对方获取邀请码，输入后即可加入同一个家庭空间。',
)

async function submit() {
  submitting.value = true
  try {
    if (mode.value === 'create') {
      if (!createForm.name.trim()) {
        showFailToast('请输入家庭名称')
        return
      }
      await familyStore.createFamilySpace({
        name: createForm.name.trim(),
        description: createForm.description.trim() || undefined,
      })
      showSuccessToast('家庭创建成功')
    } else {
      if (!joinForm.inviteCode.trim()) {
        showFailToast('请输入邀请码')
        return
      }
      await familyStore.joinFamilySpace({
        invite_code: joinForm.inviteCode.trim().toUpperCase(),
      })
      showSuccessToast('已加入家庭')
    }

    await router.replace('/home')
  } catch (error) {
    const message = error instanceof Error ? error.message : mode.value === 'create' ? '创建失败' : '加入失败'
    showFailToast(message)
  } finally {
    submitting.value = false
  }
}

async function skipForNow() {
  await router.replace('/home')
}
</script>

<template>
  <section class="relative flex min-h-screen items-center justify-center overflow-hidden bg-[var(--yy-cream)] px-6 py-10">
    <div class="absolute -left-28 -top-28 h-72 w-72 rounded-full bg-[var(--yy-apricot)]/20 blur-3xl" aria-hidden="true"></div>
    <div class="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-[var(--yy-sage)]/20 blur-3xl" aria-hidden="true"></div>
    <div class="yy-enter relative w-full max-w-[420px] rounded-[38px] border border-white/80 bg-white/85 p-8 shadow-[0_30px_90px_rgba(77,53,38,0.14)] backdrop-blur-xl">
      <p class="yy-kicker">YY Family space</p>
      <h1 class="yy-display mt-4 text-[36px] font-bold leading-tight text-[var(--yy-ink)]">{{ title }}</h1>
      <p class="mt-3 text-sm leading-6 text-[var(--yy-muted)]">
        {{ description }}
      </p>

      <div class="mt-6 inline-flex rounded-full bg-[var(--yy-cream)] p-1 text-sm">
        <button
          type="button"
          class="rounded-full px-4 py-2 transition"
          :class="mode === 'create' ? 'bg-[var(--yy-ink)] text-white' : 'text-[var(--yy-muted)]'"
          @click="mode = 'create'"
        >
          创建家庭
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 transition"
          :class="mode === 'join' ? 'bg-[var(--yy-ink)] text-white' : 'text-[var(--yy-muted)]'"
          @click="mode = 'join'"
        >
          输入邀请码
        </button>
      </div>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <template v-if="mode === 'create'">
          <input
            v-model.trim="createForm.name"
            type="text"
            placeholder="家庭名称，例如：YY私厨"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
          />
          <textarea
            v-model.trim="createForm.description"
            rows="3"
            placeholder="家庭描述（可选）"
            class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
          />
        </template>

        <input
          v-else
          v-model.trim="joinForm.inviteCode"
          type="text"
          placeholder="输入对方分享的邀请码"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm uppercase tracking-[0.15em] text-[var(--yy-ink)] outline-none transition focus:border-[var(--yy-apricot)]"
        />

        <button
          type="submit"
          class="w-full rounded-full bg-[var(--yy-ink)] px-5 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="submitting"
        >
          {{ submitting ? '提交中...' : mode === 'create' ? '创建并进入' : '加入并进入' }}
        </button>
      </form>

      <button
        type="button"
        class="mt-4 w-full py-2 text-sm text-[var(--yy-muted)]"
        @click="skipForNow"
      >
        稍后再说，先进入应用
      </button>
    </div>
  </section>
</template>
