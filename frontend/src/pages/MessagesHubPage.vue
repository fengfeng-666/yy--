<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { Bot, ChevronRight, MessageCircle } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

import { useChatStore } from '@/stores/chat'
import { useFamilyStore } from '@/stores/family'

const router = useRouter()
const chatStore = useChatStore()
const familyStore = useFamilyStore()
const { unreadCount } = storeToRefs(chatStore)
const { currentFamily, hasFamily } = storeToRefs(familyStore)

const unreadLabel = () => (unreadCount.value > 99 ? '99+' : String(unreadCount.value))

function openChat(path: '/messages/family' | '/messages/ai') {
  if (!hasFamily.value) return
  void router.push(path)
}
</script>

<template>
  <section class="yy-page space-y-5 pb-8 pt-5">
    <header class="yy-enter flex items-start justify-between gap-4 px-1">
      <div>
        <p class="yy-kicker">Family messages</p>
        <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">消息</h1>
        <p class="mt-3 text-sm text-[var(--yy-muted)]">
          {{ hasFamily ? `${currentFamily?.name}的聊天空间` : '加入家庭后即可开始聊天' }}
        </p>
      </div>
      <span
        class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[var(--yy-tomato)] text-white shadow-[0_12px_28px_rgba(207,100,71,0.24)]"
      >
        <MessageCircle class="h-6 w-6" :stroke-width="1.8" />
      </span>
    </header>

    <div class="grid gap-4">
      <button
        type="button"
        class="yy-card yy-enter yy-enter-delay-1 group relative flex min-h-36 w-full items-center gap-4 p-5 text-left transition disabled:cursor-not-allowed disabled:opacity-55"
        :disabled="!hasFamily"
        @click="openChat('/messages/family')"
      >
        <span
          class="flex h-14 w-14 shrink-0 items-center justify-center rounded-[22px] bg-[var(--yy-ink)] text-white shadow-sm"
        >
          <MessageCircle class="h-6 w-6" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="flex items-center gap-2">
            <span class="text-lg font-semibold text-[var(--yy-ink)]">家庭聊天</span>
            <span
              v-if="hasFamily && unreadCount > 0"
              class="flex min-w-[20px] items-center justify-center rounded-full bg-[var(--yy-tomato)] px-1.5 text-[10px] font-bold leading-5 text-white"
              :aria-label="`${unreadLabel()} 条未读消息`"
            >
              {{ unreadLabel() }}
            </span>
          </span>
          <span class="mt-1.5 block text-sm leading-6 text-[var(--yy-muted)]">
            {{ hasFamily ? '和家人聊聊今天吃什么、需要准备什么。' : '加入家庭后可用' }}
          </span>
        </span>
        <ChevronRight
          class="h-5 w-5 shrink-0 text-[var(--yy-muted)] transition-transform group-enabled:group-hover:translate-x-1"
        />
      </button>

      <button
        type="button"
        class="yy-card yy-enter yy-enter-delay-2 group relative flex min-h-36 w-full items-center gap-4 p-5 text-left transition disabled:cursor-not-allowed disabled:opacity-55"
        :disabled="!hasFamily"
        @click="openChat('/messages/ai')"
      >
        <span
          class="flex h-14 w-14 shrink-0 items-center justify-center rounded-[22px] bg-[var(--yy-tomato)] text-white shadow-sm"
        >
          <Bot class="h-6 w-6" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="text-lg font-semibold text-[var(--yy-ink)]">AI聊天</span>
          <span class="mt-1.5 block text-sm leading-6 text-[var(--yy-muted)]">
            {{ hasFamily ? '让 AI 小厨根据菜品和冰箱食材帮你出主意。' : '加入家庭后可用' }}
          </span>
        </span>
        <ChevronRight
          class="h-5 w-5 shrink-0 text-[var(--yy-muted)] transition-transform group-enabled:group-hover:translate-x-1"
        />
      </button>
    </div>
  </section>
</template>
