<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { showFailToast } from 'vant'
import { ArrowDown, MessageCircle, SendHorizontal, WifiOff } from 'lucide-vue-next'

import NoFamilyState from '@/components/NoFamilyState.vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useFamilyStore } from '@/stores/family'

const POLL_INTERVAL_MS = 3000
const BOTTOM_THRESHOLD_PX = 80

const authStore = useAuthStore()
const chatStore = useChatStore()
const familyStore = useFamilyStore()
const { currentUser } = storeToRefs(authStore)
const {
  connectionError,
  hasMore,
  initialLoading,
  messages,
  olderLoading,
  sending,
} = storeToRefs(chatStore)
const { currentFamily, hasFamily } = storeToRefs(familyStore)

const draft = ref('')
const messageList = ref<HTMLElement | null>(null)
const composing = ref(false)
const hasNewMessages = ref(false)
let pollTimer: number | undefined

const canSend = computed(() => Boolean(draft.value.trim()) && !sending.value)

function isNearBottom() {
  const element = messageList.value
  if (!element) return true
  return element.scrollHeight - element.scrollTop - element.clientHeight <= BOTTOM_THRESHOLD_PX
}

async function scrollToBottom(behavior: 'auto' | 'smooth' = 'auto') {
  await nextTick()
  const element = messageList.value
  element?.scrollTo({ top: element.scrollHeight, behavior })
}

async function markVisibleMessagesRead() {
  try {
    await chatStore.markLatestRead()
  } catch {
    // 下一次轮询或进入页面时会再次同步，不打断聊天。
  }
}

async function pollMessages() {
  if (!hasFamily.value || document.visibilityState !== 'visible') return
  const shouldFollow = isNearBottom()
  try {
    const added = await chatStore.pollNewMessages()
    if (!added) return
    if (shouldFollow) {
      await scrollToBottom('smooth')
      await markVisibleMessagesRead()
    } else {
      hasNewMessages.value = true
    }
  } catch {
    // 状态栏负责提示连接问题，避免每三秒重复弹出 toast。
  }
}

function startPolling() {
  stopPolling()
  if (!hasFamily.value || document.visibilityState !== 'visible') return
  pollTimer = window.setInterval(() => void pollMessages(), POLL_INTERVAL_MS)
}

function stopPolling() {
  if (pollTimer !== undefined) {
    window.clearInterval(pollTimer)
    pollTimer = undefined
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    void pollMessages()
    startPolling()
  } else {
    stopPolling()
  }
}

async function loadOlder() {
  const element = messageList.value
  const previousHeight = element?.scrollHeight ?? 0
  try {
    await chatStore.loadOlderMessages()
    await nextTick()
    if (element) element.scrollTop += element.scrollHeight - previousHeight
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载更早消息失败')
  }
}

async function revealNewMessages() {
  hasNewMessages.value = false
  await scrollToBottom('smooth')
  await markVisibleMessagesRead()
}

function handleScroll() {
  if (hasNewMessages.value && isNearBottom()) {
    hasNewMessages.value = false
    void markVisibleMessagesRead()
  }
}

async function submitMessage() {
  const content = draft.value.trim()
  if (!content || sending.value) return
  try {
    const sent = await chatStore.sendMessage(content)
    if (!sent) return
    draft.value = ''
    hasNewMessages.value = false
    await scrollToBottom('smooth')
    await markVisibleMessagesRead()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '消息发送失败')
  }
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing || composing.value) return
  event.preventDefault()
  void submitMessage()
}

function formatMessageTime(value: string) {
  const date = new Date(value)
  const today = new Date()
  const sameDay = date.toDateString() === today.toDateString()
  return new Intl.DateTimeFormat('zh-CN', {
    ...(sameDay ? {} : { month: 'numeric', day: 'numeric' }),
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

onMounted(async () => {
  if (!hasFamily.value) return
  try {
    await chatStore.loadInitialMessages()
    await scrollToBottom()
    await markVisibleMessagesRead()
  } catch {
    // 初始错误由页面内状态展示。
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<template>
  <section class="messages-page yy-page flex flex-col gap-4 pb-2 pt-5">
    <header class="yy-enter flex items-start justify-between gap-4 px-1">
      <div>
        <p class="yy-kicker">Family messages</p>
        <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">消息</h1>
        <p v-if="hasFamily" class="mt-2 text-sm text-[var(--yy-muted)]">{{ currentFamily?.name }}的悄悄话</p>
      </div>
      <span class="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--yy-tomato)] text-white shadow-[0_12px_28px_rgba(207,100,71,0.24)]">
        <MessageCircle class="h-6 w-6" :stroke-width="1.8" />
      </span>
    </header>

    <NoFamilyState
      v-if="!hasFamily"
      class="mt-2"
      title="加入家庭后开始聊天"
      description="和家人加入同一个家庭空间，就能在这里分享每一顿饭前后的期待。"
    />

    <template v-else>
      <div
        v-if="connectionError"
        class="flex items-center justify-center gap-2 rounded-2xl bg-amber-50 px-4 py-2 text-xs text-amber-700"
        role="status"
      >
        <WifiOff class="h-3.5 w-3.5" />
        连接暂时不稳定，正在自动重试
      </div>

      <div
        ref="messageList"
        class="message-list min-h-0 flex-1 overflow-y-auto rounded-[28px] border border-[var(--yy-line)] bg-white/55 px-3 py-4"
        aria-live="polite"
        @scroll.passive="handleScroll"
      >
        <div v-if="initialLoading" class="flex h-full items-center justify-center text-sm text-[var(--yy-muted)]">
          正在加载消息…
        </div>

        <template v-else>
          <div class="mb-4 flex justify-center">
            <button
              v-if="hasMore"
              type="button"
              class="rounded-full bg-white px-4 py-2 text-xs text-[var(--yy-muted)] shadow-sm disabled:opacity-60"
              :disabled="olderLoading"
              @click="loadOlder"
            >
              {{ olderLoading ? '正在加载…' : '加载更早消息' }}
            </button>
            <span v-else-if="messages.length" class="text-[11px] text-[var(--yy-muted)]/70">从这里开始聊起</span>
          </div>

          <div v-if="!messages.length" class="flex h-full min-h-52 flex-col items-center justify-center text-center">
            <span class="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]">
              <MessageCircle class="h-6 w-6" />
            </span>
            <p class="mt-4 text-sm font-semibold text-[var(--yy-ink)]">还没有消息</p>
            <p class="mt-1 text-xs text-[var(--yy-muted)]">发一句“今天想吃什么？”开始吧。</p>
          </div>

          <div v-else class="space-y-3">
            <article
              v-for="message in messages"
              :key="message.id"
              class="flex"
              :class="message.sender_id === currentUser?.id ? 'justify-end' : 'justify-start'"
            >
              <div class="max-w-[82%]">
                <p
                  class="mb-1 px-1 text-[11px] text-[var(--yy-muted)]"
                  :class="message.sender_id === currentUser?.id ? 'text-right' : 'text-left'"
                >
                  {{ message.sender_id === currentUser?.id ? '我' : message.sender.nickname }}
                  · {{ formatMessageTime(message.created_at) }}
                </p>
                <p
                  class="whitespace-pre-wrap break-words rounded-[22px] px-4 py-3 text-sm leading-6 shadow-sm"
                  :class="
                    message.sender_id === currentUser?.id
                      ? 'rounded-br-md bg-[var(--yy-ink)] text-white'
                      : 'rounded-bl-md bg-white text-[var(--yy-ink)]'
                  "
                >
                  {{ message.content }}
                </p>
              </div>
            </article>
          </div>
        </template>
      </div>

      <button
        v-if="hasNewMessages"
        type="button"
        class="mx-auto -mt-14 z-10 inline-flex items-center gap-1.5 rounded-full bg-[var(--yy-tomato)] px-4 py-2 text-xs font-medium text-white shadow-lg"
        @click="revealNewMessages"
      >
        <ArrowDown class="h-3.5 w-3.5" />
        有新消息
      </button>

      <form class="yy-card flex items-end gap-2 p-2" @submit.prevent="submitMessage">
        <label class="sr-only" for="chat-composer">输入消息</label>
        <textarea
          id="chat-composer"
          v-model="draft"
          rows="1"
          maxlength="1000"
          enterkeyhint="send"
          placeholder="说点什么…"
          class="max-h-28 min-h-11 flex-1 resize-none rounded-[20px] bg-[var(--yy-cream)] px-4 py-3 text-sm leading-5 text-[var(--yy-ink)] outline-none placeholder:text-[var(--yy-muted)]/70"
          @compositionstart="composing = true"
          @compositionend="composing = false"
          @keydown="handleComposerKeydown"
        ></textarea>
        <button
          type="submit"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--yy-tomato)] text-white transition disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="!canSend"
          aria-label="发送消息"
        >
          <SendHorizontal class="h-5 w-5" />
        </button>
      </form>
    </template>
  </section>
</template>

<style scoped>
.messages-page {
  height: calc(100dvh - 6.75rem - env(safe-area-inset-bottom));
  min-height: 32rem;
}

.message-list {
  scrollbar-width: thin;
  scrollbar-color: var(--yy-line) transparent;
}
</style>
