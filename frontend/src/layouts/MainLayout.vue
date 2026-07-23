<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { ClipboardList, CookingPot, House, MessageCircle, UserRound } from 'lucide-vue-next'

import { useChatStore } from '@/stores/chat'
import { useFamilyStore } from '@/stores/family'

const UNREAD_POLL_INTERVAL_MS = 3000

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const familyStore = useFamilyStore()
const { unreadCount } = storeToRefs(chatStore)
const { hasFamily } = storeToRefs(familyStore)
let unreadTimer: number | undefined

const tabs = [
  { name: 'home', label: '首页', path: '/home', icon: House },
  { name: 'dishes', label: '菜单', path: '/dishes', icon: CookingPot },
  { name: 'orders', label: '点菜', path: '/orders', icon: ClipboardList },
  { name: 'messages', label: '消息', path: '/messages', icon: MessageCircle },
  { name: 'profile', label: '我的', path: '/profile', icon: UserRound },
]

const active = computed(() => (route.name === 'journal' ? 'profile' : (route.name as string)))
const unreadLabel = computed(() => (unreadCount.value > 99 ? '99+' : String(unreadCount.value)))

function navigate(path: string) {
  router.push(path)
}

async function refreshUnread() {
  if (!hasFamily.value || document.visibilityState !== 'visible') return
  try {
    await chatStore.refreshUnreadCount()
  } catch {
    // 导航角标静默重试，不影响当前页面操作。
  }
}

function stopUnreadPolling() {
  if (unreadTimer !== undefined) {
    window.clearInterval(unreadTimer)
    unreadTimer = undefined
  }
}

function startUnreadPolling() {
  stopUnreadPolling()
  if (!hasFamily.value || document.visibilityState !== 'visible') return
  void refreshUnread()
  unreadTimer = window.setInterval(() => void refreshUnread(), UNREAD_POLL_INTERVAL_MS)
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') startUnreadPolling()
  else stopUnreadPolling()
}

watch(hasFamily, (value) => {
  if (value) startUnreadPolling()
  else {
    stopUnreadPolling()
    chatStore.reset()
  }
})

onMounted(() => {
  document.addEventListener('visibilitychange', handleVisibilityChange)
  startUnreadPolling()
})

onBeforeUnmount(() => {
  stopUnreadPolling()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<template>
  <div class="yy-shell mx-auto flex min-h-screen w-full max-w-[480px] flex-col">
    <main class="flex-1 pb-[calc(6.75rem+env(safe-area-inset-bottom))]">
      <router-view />
    </main>

    <nav
      aria-label="主导航"
      class="fixed bottom-3 left-1/2 z-20 flex w-[calc(100%-1.5rem)] max-w-[456px] -translate-x-1/2 rounded-[26px] border border-white/70 bg-[rgba(48,37,31,0.94)] px-2 py-2 shadow-[0_18px_50px_rgba(48,37,31,0.28)] backdrop-blur-xl"
      :style="{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))' }"
    >
      <button
        v-for="tab in tabs"
        :key="tab.name"
        type="button"
        class="group relative flex min-h-14 flex-1 flex-col items-center justify-center gap-1 rounded-[20px] px-1 text-[11px] transition"
        :class="
          active === tab.name
            ? 'bg-white text-[var(--yy-ink)] shadow-[0_8px_24px_rgba(0,0,0,0.16)]'
            : 'text-white/55 hover:bg-white/8 hover:text-white'
        "
        :aria-current="active === tab.name ? 'page' : undefined"
        @click="navigate(tab.path)"
      >
        <component
          :is="tab.icon"
          class="h-[19px] w-[19px] transition-transform group-hover:-translate-y-0.5"
          :stroke-width="active === tab.name ? 2.3 : 1.8"
        />
        <span
          v-if="tab.name === 'messages' && unreadCount > 0"
          class="absolute right-[17%] top-1 flex min-w-[18px] items-center justify-center rounded-full bg-[var(--yy-tomato)] px-1 text-[10px] font-bold leading-[18px] text-white shadow-sm"
          :aria-label="`${unreadLabel} 条未读消息`"
        >
          {{ unreadLabel }}
        </span>
        <span class="font-medium">{{ tab.label }}</span>
      </button>
    </nav>
  </div>
</template>
