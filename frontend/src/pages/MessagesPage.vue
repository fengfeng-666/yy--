<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { ArrowDown, Bot, ChevronRight, History, ImagePlus, MessageCircle, Plus, SendHorizontal, Trash2, WifiOff } from 'lucide-vue-next'

import AiActionDraftCard from '@/components/AiActionDraftCard.vue'
import AiImageAttachmentPreview from '@/components/AiImageAttachmentPreview.vue'
import AiRecommendationCard from '@/components/AiRecommendationCard.vue'
import AiRetrievalSources from '@/components/AiRetrievalSources.vue'
import AiToolTrace from '@/components/AiToolTrace.vue'
import NoFamilyState from '@/components/NoFamilyState.vue'
import { useAiChatStore } from '@/stores/aiChat'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useFamilyStore } from '@/stores/family'
import type { AiChatMessage } from '@/types/aiChat'
import { resolveAssetUrl } from '@/utils/assets'

const POLL_INTERVAL_MS = 3000
const BOTTOM_THRESHOLD_PX = 80

const authStore = useAuthStore()
const aiChatStore = useAiChatStore()
const chatStore = useChatStore()
const familyStore = useFamilyStore()
const { currentUser } = storeToRefs(authStore)
const {
  connectionError: familyConnectionError,
  hasMore: familyHasMore,
  initialLoading: familyInitialLoading,
  messages: familyMessages,
  olderLoading: familyOlderLoading,
  sending: familySending,
} = storeToRefs(chatStore)
const {
  connectionError: aiConnectionError,
  conversations: aiConversations,
  currentConversation,
  currentConversationId,
  hasMore: aiHasMore,
  initialLoading: aiInitialLoading,
  messages: aiMessages,
  olderLoading: aiOlderLoading,
  selectedImage,
  sending: aiSending,
} = storeToRefs(aiChatStore)
const { currentFamily, hasFamily } = storeToRefs(familyStore)

const activeTab = ref<'family' | 'ai'>('family')
const familyDraft = ref('')
const aiDraft = ref('')
const familyMessageList = ref<HTMLElement | null>(null)
const aiMessageList = ref<HTMLElement | null>(null)
const aiFileInput = ref<HTMLInputElement | null>(null)
const familyComposing = ref(false)
const aiComposing = ref(false)
const hasNewFamilyMessages = ref(false)
const aiLoaded = ref(false)
const aiImagePreviewUrl = ref('')
const aiHistoryPopupVisible = ref(false)
const aiActionLoadingMessageId = ref<number | null>(null)
let pollTimer: number | undefined

const canSendFamily = computed(() => Boolean(familyDraft.value.trim()) && !familySending.value)
const canSendAi = computed(
  () => (Boolean(aiDraft.value.trim()) || Boolean(selectedImage.value)) && !aiSending.value,
)

function isNearBottom() {
  const element = familyMessageList.value
  if (!element) return true
  return element.scrollHeight - element.scrollTop - element.clientHeight <= BOTTOM_THRESHOLD_PX
}

async function scrollFamilyToBottom(behavior: 'auto' | 'smooth' = 'auto') {
  await nextTick()
  const element = familyMessageList.value
  element?.scrollTo({ top: element.scrollHeight, behavior })
}

async function scrollAiToBottom(behavior: 'auto' | 'smooth' = 'auto') {
  await nextTick()
  const element = aiMessageList.value
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
  if (!hasFamily.value || activeTab.value !== 'family' || document.visibilityState !== 'visible') return
  const shouldFollow = isNearBottom()
  try {
    const added = await chatStore.pollNewMessages()
    if (!added) return
    if (shouldFollow) {
      await scrollFamilyToBottom('smooth')
      await markVisibleMessagesRead()
    } else {
      hasNewFamilyMessages.value = true
    }
  } catch {
    // 状态栏负责提示连接问题，避免每三秒重复弹出 toast。
  }
}

function startPolling() {
  stopPolling()
  if (!hasFamily.value || activeTab.value !== 'family' || document.visibilityState !== 'visible') return
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
  const element = familyMessageList.value
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
  hasNewFamilyMessages.value = false
  await scrollFamilyToBottom('smooth')
  await markVisibleMessagesRead()
}

function handleScroll() {
  if (hasNewFamilyMessages.value && isNearBottom()) {
    hasNewFamilyMessages.value = false
    void markVisibleMessagesRead()
  }
}

async function submitMessage() {
  const content = familyDraft.value.trim()
  if (!content || familySending.value) return
  try {
    const sent = await chatStore.sendMessage(content)
    if (!sent) return
    familyDraft.value = ''
    hasNewFamilyMessages.value = false
    await scrollFamilyToBottom('smooth')
    await markVisibleMessagesRead()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '消息发送失败')
  }
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing || familyComposing.value) return
  event.preventDefault()
  void submitMessage()
}

async function ensureAiMessagesLoaded() {
  if (!hasFamily.value || aiLoaded.value) return
  try {
    await aiChatStore.loadInitialMessages()
    aiLoaded.value = true
    await scrollAiToBottom()
  } catch {
    // AI 分区内提示错误状态即可。
  }
}

async function selectAiConversation(conversationId: number) {
  try {
    await aiChatStore.selectConversation(conversationId)
    aiHistoryPopupVisible.value = false
    await scrollAiToBottom()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '切换 AI 对话失败')
  }
}

async function handleDeleteAiConversation(conversationId: number) {
  try {
    await showConfirmDialog({
      title: '删除历史对话',
      message: '删除后将无法恢复，这个 AI 对话里的历史消息也会一起删除。',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await aiChatStore.deleteConversation(conversationId)
    showSuccessToast('历史对话已删除')
    if (currentConversationId.value) {
      await scrollAiToBottom()
    }
  } catch (error) {
    if (error === 'cancel') return
    showFailToast(error instanceof Error ? error.message : '删除历史对话失败')
  }
}

function handleNewAiConversation() {
  aiChatStore.startNewConversation()
  aiHistoryPopupVisible.value = false
  aiDraft.value = ''
  clearAiSelectedImage()
}

async function loadOlderAiMessages() {
  const element = aiMessageList.value
  const previousHeight = element?.scrollHeight ?? 0
  try {
    await aiChatStore.loadOlderMessages()
    await nextTick()
    if (element) element.scrollTop += element.scrollHeight - previousHeight
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载更早 AI 对话失败')
  }
}

function revokeAiImagePreview() {
  if (!aiImagePreviewUrl.value) return
  URL.revokeObjectURL(aiImagePreviewUrl.value)
  aiImagePreviewUrl.value = ''
}

function clearAiSelectedImage() {
  revokeAiImagePreview()
  aiChatStore.clearSelectedImage()
  if (aiFileInput.value) {
    aiFileInput.value.value = ''
  }
}

function openAiImagePicker() {
  aiFileInput.value?.click()
}

function handleAiImageChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] ?? null
  revokeAiImagePreview()
  aiChatStore.setSelectedImage(file)
  aiImagePreviewUrl.value = file ? URL.createObjectURL(file) : ''
}

async function submitAiMessage() {
  if (!canSendAi.value) return
  const submittedDraft = aiDraft.value
  aiDraft.value = ''
  try {
    const turn = await aiChatStore.sendMessage(submittedDraft)
    if (!turn) return
    clearAiSelectedImage()
    await scrollAiToBottom('smooth')
  } catch (error) {
    if (!aiDraft.value) aiDraft.value = submittedDraft
    showFailToast(error instanceof Error ? error.message : 'AI 消息发送失败')
  }
}

async function handleConfirmAiAction(messageId: number) {
  aiActionLoadingMessageId.value = messageId
  try {
    await aiChatStore.confirmAction(messageId)
    showSuccessToast('购物清单已生成')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '确认失败')
  } finally {
    aiActionLoadingMessageId.value = null
  }
}

async function handleCancelAiAction(messageId: number) {
  aiActionLoadingMessageId.value = messageId
  try {
    await aiChatStore.cancelAction(messageId)
    showSuccessToast('已取消这次生成')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '取消失败')
  } finally {
    aiActionLoadingMessageId.value = null
  }
}

function handleAiComposerKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing || aiComposing.value) return
  event.preventDefault()
  void submitAiMessage()
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

function formatConversationTime(value?: string | null) {
  if (!value) return ''
  return formatMessageTime(value)
}

function getAiSummary(message: AiChatMessage) {
  return message.metadata_json?.summary?.trim() || message.content
}

function getConversationPreview(content?: string | null) {
  if (!content) return '还没有消息'
  return content
}

onMounted(async () => {
  if (!hasFamily.value) return
  try {
    await chatStore.loadInitialMessages()
    await scrollFamilyToBottom()
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
  revokeAiImagePreview()
})

watch(activeTab, async (tab) => {
  if (tab === 'family') {
    startPolling()
    if (familyMessages.value.length) {
      await scrollFamilyToBottom()
      await markVisibleMessagesRead()
    }
    return
  }

  stopPolling()
  await ensureAiMessagesLoaded()
  if (aiMessages.value.length) {
    await scrollAiToBottom()
  }
})

watch(
  () => aiMessages.value.at(-1)?.content,
  () => {
    if (activeTab.value === 'ai' && aiSending.value) void scrollAiToBottom()
  },
)
</script>

<template>
  <section class="messages-page yy-page flex flex-col gap-3 pb-2 pt-3 sm:gap-4 sm:pt-5">
    <header class="yy-enter flex items-start justify-between gap-3 px-1 sm:gap-4">
      <div>
        <p class="yy-kicker">Family messages</p>
        <h1 class="yy-display mt-1.5 text-[28px] font-bold leading-none text-[var(--yy-ink)] sm:mt-2 sm:text-[32px]">消息</h1>
        <p v-if="hasFamily" class="mt-1.5 text-xs text-[var(--yy-muted)] sm:mt-2 sm:text-sm">{{ currentFamily?.name }}的悄悄话</p>
      </div>
      <span class="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--yy-tomato)] text-white shadow-[0_12px_28px_rgba(207,100,71,0.24)] sm:h-12 sm:w-12">
        <MessageCircle class="h-6 w-6" :stroke-width="1.8" />
      </span>
    </header>

    <div class="yy-card flex gap-2 p-1">
      <button
        type="button"
        class="flex flex-1 items-center justify-center gap-2 rounded-[20px] px-3 py-2.5 text-[13px] font-medium transition sm:px-4 sm:py-3 sm:text-sm"
        :class="
          activeTab === 'family'
            ? 'bg-[var(--yy-ink)] text-white shadow-sm'
            : 'text-[var(--yy-muted)]'
        "
        @click="activeTab = 'family'"
      >
        <MessageCircle class="h-4 w-4" />
        家庭聊天
      </button>
      <button
        type="button"
        class="flex flex-1 items-center justify-center gap-2 rounded-[20px] px-3 py-2.5 text-[13px] font-medium transition sm:px-4 sm:py-3 sm:text-sm"
        :class="
          activeTab === 'ai'
            ? 'bg-[var(--yy-tomato)] text-white shadow-sm'
            : 'text-[var(--yy-muted)]'
        "
        @click="activeTab = 'ai'"
      >
        <Bot class="h-4 w-4" />
        AI聊天
      </button>
    </div>

    <NoFamilyState
      v-if="!hasFamily"
      class="mt-2"
      title="加入家庭后开始聊天"
      description="和家人加入同一个家庭空间后，既能聊家常，也能让 AI 根据家庭菜品和冰箱图片给你推荐。"
    />

    <template v-else-if="activeTab === 'family'">
      <div
        v-if="familyConnectionError"
        class="flex items-center justify-center gap-2 rounded-2xl bg-amber-50 px-4 py-2 text-xs text-amber-700"
        role="status"
      >
        <WifiOff class="h-3.5 w-3.5" />
        连接暂时不稳定，正在自动重试
      </div>

      <div
        ref="familyMessageList"
        class="message-list min-h-0 flex-1 overflow-y-auto rounded-[28px] border border-[var(--yy-line)] bg-white/55 px-3 py-4"
        aria-live="polite"
        @scroll.passive="handleScroll"
      >
        <div
          v-if="familyInitialLoading"
          class="flex h-full items-center justify-center text-sm text-[var(--yy-muted)]"
        >
          正在加载消息…
        </div>

        <template v-else>
          <div class="mb-4 flex justify-center">
            <button
              v-if="familyHasMore"
              type="button"
              class="rounded-full bg-white px-4 py-2 text-xs text-[var(--yy-muted)] shadow-sm disabled:opacity-60"
              :disabled="familyOlderLoading"
              @click="loadOlder"
            >
              {{ familyOlderLoading ? '正在加载…' : '加载更早消息' }}
            </button>
            <span v-else-if="familyMessages.length" class="text-[11px] text-[var(--yy-muted)]/70">
              从这里开始聊起
            </span>
          </div>

          <div
            v-if="!familyMessages.length"
            class="flex h-full min-h-52 flex-col items-center justify-center text-center"
          >
            <span class="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]">
              <MessageCircle class="h-6 w-6" />
            </span>
            <p class="mt-4 text-sm font-semibold text-[var(--yy-ink)]">还没有消息</p>
            <p class="mt-1 text-xs text-[var(--yy-muted)]">发一句“今天想吃什么？”开始吧。</p>
          </div>

          <div v-else class="space-y-3">
            <article
              v-for="message in familyMessages"
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
        v-if="hasNewFamilyMessages"
        type="button"
        class="mx-auto -mt-14 z-10 inline-flex items-center gap-1.5 rounded-full bg-[var(--yy-tomato)] px-4 py-2 text-xs font-medium text-white shadow-lg"
        @click="revealNewMessages"
      >
        <ArrowDown class="h-3.5 w-3.5" />
        有新消息
      </button>

      <form class="yy-card flex items-end gap-2 p-2" @submit.prevent="submitMessage">
        <label class="sr-only" for="family-chat-composer">输入消息</label>
        <textarea
          id="family-chat-composer"
          v-model="familyDraft"
          rows="1"
          maxlength="1000"
          enterkeyhint="send"
          placeholder="说点什么…"
          class="max-h-28 min-h-11 flex-1 resize-none rounded-[20px] bg-[var(--yy-cream)] px-4 py-3 text-sm leading-5 text-[var(--yy-ink)] outline-none placeholder:text-[var(--yy-muted)]/70"
          @compositionstart="familyComposing = true"
          @compositionend="familyComposing = false"
          @keydown="handleComposerKeydown"
        ></textarea>
        <button
          type="submit"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--yy-tomato)] text-white transition disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="!canSendFamily"
          aria-label="发送消息"
        >
          <SendHorizontal class="h-5 w-5" />
        </button>
      </form>
    </template>

    <template v-else>
      <input
        ref="aiFileInput"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        class="hidden"
        @change="handleAiImageChange"
      />

      <div class="ai-workspace min-h-0 flex-1 md:grid md:grid-cols-[17.5rem_minmax(0,1fr)] md:gap-4">
        <aside class="yy-card hidden min-h-0 flex-col overflow-hidden p-4 md:flex">
          <div class="flex items-start gap-3 border-b border-[var(--yy-line)] pb-4">
            <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-tomato)] text-white shadow-[0_10px_24px_rgba(207,100,71,0.22)]">
              <Bot class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <p class="text-sm font-semibold text-[var(--yy-ink)]">AI 小厨工作台</p>
              <p class="mt-1 text-xs leading-5 text-[var(--yy-muted)]">菜品、冰箱和家庭偏好，都在一段对话里。</p>
            </div>
          </div>

          <button
            type="button"
            class="mt-4 flex w-full items-center justify-center gap-2 rounded-[20px] bg-[var(--yy-tomato)] px-4 py-3 text-sm font-medium text-white shadow-sm transition"
            :disabled="aiSending"
            @click="handleNewAiConversation"
          >
            <Plus class="h-4 w-4" />
            开启新对话
          </button>

          <div class="mt-5 flex min-h-0 flex-1 flex-col">
            <div class="flex items-center justify-between px-1">
              <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--yy-muted)]">历史对话</p>
              <span class="text-[11px] text-[var(--yy-muted)]/70">{{ aiConversations.length }} 条</span>
            </div>

            <div v-if="!aiConversations.length" class="mt-3 rounded-[20px] bg-[var(--yy-cream)] px-4 py-5 text-center text-xs leading-5 text-[var(--yy-muted)]">
              还没有历史对话，先问问今天吃什么吧。
            </div>

            <div v-else class="message-list mt-3 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
              <div
                v-for="conversation in aiConversations"
                :key="`desktop-${conversation.id}`"
                class="group flex items-center gap-1.5 rounded-[18px] border px-2.5 py-2.5 transition"
                :class="
                  conversation.id === currentConversationId
                    ? 'border-[var(--yy-tomato)] bg-[var(--yy-apricot)]/10'
                    : 'border-transparent bg-[var(--yy-cream)]/70 hover:border-[var(--yy-line)]'
                "
              >
                <button
                  type="button"
                  class="min-w-0 flex-1 text-left"
                  @click="selectAiConversation(conversation.id)"
                >
                  <p class="truncate text-sm font-semibold text-[var(--yy-ink)]">{{ conversation.title }}</p>
                  <p class="mt-1 line-clamp-1 text-[11px] text-[var(--yy-muted)]">
                    {{ getConversationPreview(conversation.last_message_preview) }}
                  </p>
                </button>
                <button
                  type="button"
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[var(--yy-muted)] opacity-70 transition hover:bg-white hover:text-[var(--yy-tomato)] group-hover:opacity-100"
                  aria-label="删除历史对话"
                  @click.stop="handleDeleteAiConversation(conversation.id)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </aside>

        <div class="ai-chat-panel flex min-h-0 flex-col gap-3">
          <div class="yy-card flex shrink-0 items-center gap-3 px-3 py-2.5 sm:px-4 sm:py-3">
            <span class="hidden h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)] sm:flex">
              <Bot class="h-5 w-5" />
            </span>
            <div class="flex min-w-0 flex-1 items-center justify-between gap-2">
          <div class="min-w-0 flex-1">
              <p class="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--yy-muted)]">当前对话</p>
              <h2 class="mt-0.5 truncate text-sm font-semibold text-[var(--yy-ink)] sm:text-base">
              {{ currentConversation?.title ?? '新对话' }}
            </h2>
          </div>
          <div class="flex shrink-0 items-center gap-1.5 sm:gap-2">
            <button
              type="button"
                class="inline-flex h-9 items-center justify-center gap-1.5 rounded-full bg-[var(--yy-cream)] px-2.5 text-xs font-medium text-[var(--yy-ink)] md:hidden"
              aria-label="查看 AI 历史记录"
              :disabled="aiSending"
              @click="aiHistoryPopupVisible = true"
            >
              <History class="h-3.5 w-3.5" />
              <span class="hidden min-[360px]:inline">历史记录</span>
            </button>
            <button
              type="button"
                class="inline-flex h-9 items-center justify-center gap-1.5 rounded-full bg-[var(--yy-tomato)] px-2.5 text-xs font-medium text-white md:hidden"
              aria-label="开始新的 AI 对话"
              :disabled="aiSending"
              @click="handleNewAiConversation"
            >
              <Plus class="h-3.5 w-3.5" />
              <span class="hidden min-[360px]:inline">新对话</span>
            </button>
          </div>
            </div>
          </div>

          <div
            v-if="aiConnectionError"
            class="flex items-center justify-center gap-2 rounded-2xl bg-amber-50 px-4 py-2 text-xs text-amber-700"
            role="status"
          >
            <WifiOff class="h-3.5 w-3.5" />
            AI 服务暂时有点忙，正在尝试恢复
          </div>

          <div
            ref="aiMessageList"
            class="message-list min-h-0 flex-1 overflow-y-auto rounded-[28px] border border-[var(--yy-line)] bg-white/55 px-3 py-4 sm:px-5 sm:py-5 md:px-6"
            aria-live="polite"
          >
        <div
          v-if="aiInitialLoading"
          class="flex h-full items-center justify-center text-sm text-[var(--yy-muted)]"
        >
          正在加载 AI 对话…
        </div>

        <template v-else>
          <div class="mb-4 flex justify-center">
            <button
              v-if="currentConversationId && aiHasMore"
              type="button"
              class="rounded-full bg-white px-4 py-2 text-xs text-[var(--yy-muted)] shadow-sm disabled:opacity-60"
              :disabled="aiOlderLoading"
              @click="loadOlderAiMessages"
            >
              {{ aiOlderLoading ? '正在加载…' : '加载更早对话' }}
            </button>
            <span v-else-if="aiMessages.length && currentConversationId" class="text-[11px] text-[var(--yy-muted)]/70">
              从这里开始和 AI 小厨聊天
            </span>
          </div>

          <div v-if="!aiMessages.length" class="flex h-full min-h-52 flex-col items-center justify-center text-center">
            <span class="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--yy-apricot)]/15 text-[var(--yy-tomato)]">
              <Bot class="h-6 w-6" />
            </span>
            <p class="mt-4 text-sm font-semibold text-[var(--yy-ink)]">
              {{ currentConversationId ? '这个对话还没有消息' : '开始一个新对话' }}
            </p>
            <p class="mt-1 text-xs text-[var(--yy-muted)]">
              {{ currentConversationId ? '继续提问，或切到历史记录查看其他对话。' : '输入想吃什么，或上传冰箱图片让 AI 帮你出主意。' }}
            </p>
          </div>

          <div v-else class="space-y-3">
            <article
              v-for="message in aiMessages"
              :key="message.id"
              class="flex"
              :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div class="max-w-[88%] space-y-2 md:max-w-[82%]">
                <p
                  class="px-1 text-[11px] text-[var(--yy-muted)]"
                  :class="message.role === 'user' ? 'text-right' : 'text-left'"
                >
                  {{ message.role === 'user' ? '我' : 'AI小厨' }}
                  · {{ formatMessageTime(message.created_at) }}
                </p>

                <div
                  class="space-y-3 rounded-[22px] px-4 py-3 text-sm leading-6 shadow-sm"
                  :class="
                    message.role === 'user'
                      ? 'rounded-br-md bg-[var(--yy-ink)] text-white'
                      : 'rounded-bl-md bg-white text-[var(--yy-ink)]'
                  "
                >
                  <img
                    v-if="message.metadata_json?.fridge_image?.image_url"
                    :src="resolveAssetUrl(message.metadata_json.fridge_image.image_url)"
                    alt="冰箱图片"
                    class="max-h-52 w-full rounded-2xl object-cover"
                  />
                  <p class="whitespace-pre-wrap break-words">
                    <template v-if="message.role === 'assistant' && !getAiSummary(message) && aiSending">
                      正在思考<span class="streaming-dots" aria-hidden="true">…</span>
                    </template>
                    <template v-else>
                      {{ message.role === 'assistant' ? getAiSummary(message) : message.content }}
                      <span
                        v-if="message.role === 'assistant' && message.id < 0 && aiSending && getAiSummary(message)"
                        class="streaming-cursor"
                        aria-hidden="true"
                      ></span>
                    </template>
                  </p>
                  <div
                    v-if="message.role === 'assistant' && message.metadata_json?.recognized_ingredients?.length"
                    class="space-y-2"
                  >
                    <p class="text-[11px] uppercase tracking-[0.16em] text-[var(--yy-muted)]">识别到的食材</p>
                    <div class="flex flex-wrap gap-2">
                      <span
                        v-for="ingredient in message.metadata_json.recognized_ingredients"
                        :key="`${message.id}-${ingredient}`"
                        class="rounded-full bg-[var(--yy-apricot)]/20 px-3 py-1 text-xs text-[var(--yy-tomato)]"
                      >
                        {{ ingredient }}
                      </span>
                    </div>
                  </div>
                </div>

                <div
                  v-if="message.role === 'assistant' && message.metadata_json?.recommendations?.length"
                  class="space-y-3"
                >
                  <AiRecommendationCard
                    v-for="recommendation in message.metadata_json.recommendations"
                    :key="`${message.id}-${recommendation.dish_name}`"
                    :recommendation="recommendation"
                  />
                </div>

                <AiRetrievalSources
                  v-if="message.role === 'assistant' && message.metadata_json?.retrieval_sources?.length"
                  :sources="message.metadata_json.retrieval_sources"
                />

                <AiToolTrace
                  v-if="message.role === 'assistant' && message.metadata_json?.tool_calls?.length"
                  :traces="message.metadata_json.tool_calls"
                />

                <AiActionDraftCard
                  v-if="message.role === 'assistant' && message.metadata_json?.action_draft"
                  :draft="message.metadata_json.action_draft"
                  :loading="aiActionLoadingMessageId === message.id"
                  @confirm="handleConfirmAiAction(message.id)"
                  @cancel="handleCancelAiAction(message.id)"
                />
              </div>
            </article>
          </div>
        </template>
      </div>

          <div class="shrink-0 space-y-3">
        <van-popup
          v-model:show="aiHistoryPopupVisible"
          round
          position="bottom"
          :style="{ maxWidth: '430px', margin: '0 auto', width: '100%', padding: '20px 20px 28px' }"
        >
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-[var(--yy-ink)]">历史对话</h3>
                <p class="mt-1 text-xs text-[var(--yy-muted)]">选择一条历史对话继续聊，或直接开启新对话。</p>
              </div>
              <button
                type="button"
                class="text-sm text-[var(--yy-muted)]"
                @click="aiHistoryPopupVisible = false"
              >
                关闭
              </button>
            </div>

            <button
              type="button"
              class="flex w-full items-center justify-center gap-2 rounded-[22px] bg-[var(--yy-tomato)] px-4 py-3 text-sm font-medium text-white"
              @click="handleNewAiConversation"
            >
              <Plus class="h-4 w-4" />
              开启新对话
            </button>

            <div v-if="!aiConversations.length" class="rounded-[22px] bg-[var(--yy-cream)] px-4 py-5 text-center text-sm text-[var(--yy-muted)]">
              还没有历史对话，先发第一条消息吧。
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="conversation in aiConversations"
                :key="conversation.id"
                class="flex items-center gap-2 rounded-[22px] border px-3 py-3 transition"
                :class="
                  conversation.id === currentConversationId
                    ? 'border-[var(--yy-tomato)] bg-[var(--yy-apricot)]/10'
                    : 'border-[var(--yy-line)] bg-white'
                "
              >
                <button
                  type="button"
                  class="flex min-w-0 flex-1 items-center justify-between gap-3 text-left"
                  @click="selectAiConversation(conversation.id)"
                >
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2">
                      <p class="truncate text-sm font-semibold text-[var(--yy-ink)]">{{ conversation.title }}</p>
                      <span
                        v-if="conversation.id === currentConversationId"
                        class="rounded-full bg-[var(--yy-tomato)]/10 px-2 py-0.5 text-[10px] font-medium text-[var(--yy-tomato)]"
                      >
                        当前
                      </span>
                    </div>
                    <p class="mt-1 line-clamp-2 text-xs leading-5 text-[var(--yy-muted)]">
                      {{ getConversationPreview(conversation.last_message_preview) }}
                    </p>
                    <p class="mt-1 text-[11px] text-[var(--yy-muted)]/80">
                      {{ formatConversationTime(conversation.last_message_at ?? conversation.updated_at) }}
                    </p>
                  </div>
                  <ChevronRight class="h-4 w-4 shrink-0 text-[var(--yy-muted)]" />
                </button>
                <button
                  type="button"
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--yy-cream)] text-[var(--yy-muted)] transition hover:text-[var(--yy-tomato)]"
                  aria-label="删除历史对话"
                  @click.stop="handleDeleteAiConversation(conversation.id)"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </van-popup>

        <AiImageAttachmentPreview
          v-if="selectedImage && aiImagePreviewUrl"
          :file-name="selectedImage.name"
          :preview-url="aiImagePreviewUrl"
          @remove="clearAiSelectedImage"
        />

            <form class="yy-card flex items-end gap-2 p-2.5 sm:p-3" @submit.prevent="submitAiMessage">
          <button
            type="button"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--yy-cream)] text-[var(--yy-tomato)] transition"
            aria-label="上传冰箱图片"
            @click="openAiImagePicker"
          >
            <ImagePlus class="h-5 w-5" />
          </button>
          <label class="sr-only" for="ai-chat-composer">输入消息</label>
          <textarea
            id="ai-chat-composer"
            v-model="aiDraft"
            rows="1"
            maxlength="2000"
            enterkeyhint="send"
            :placeholder="selectedImage ? '补充一句，比如“这些食材适合做什么？”' : '问问 AI 今天吃什么…'"
              class="max-h-36 min-h-11 flex-1 resize-none rounded-[20px] bg-[var(--yy-cream)] px-4 py-3 text-sm leading-5 text-[var(--yy-ink)] outline-none placeholder:text-[var(--yy-muted)]/70 sm:min-h-[52px]"
            @compositionstart="aiComposing = true"
            @compositionend="aiComposing = false"
            @keydown="handleAiComposerKeydown"
          ></textarea>
          <button
            type="submit"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--yy-tomato)] text-white transition disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!canSendAi"
            aria-label="发送 AI 消息"
          >
            <SendHorizontal class="h-5 w-5" />
          </button>
            </form>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.messages-page {
  height: calc(100dvh - 6.75rem - env(safe-area-inset-bottom));
  min-height: 0;
  max-height: calc(100dvh - 6.75rem - env(safe-area-inset-bottom));
  overflow: hidden;
}

@supports not (height: 100dvh) {
  .messages-page {
    height: calc(100vh - 6.75rem - env(safe-area-inset-bottom));
    max-height: calc(100vh - 6.75rem - env(safe-area-inset-bottom));
  }
}

.ai-workspace,
.ai-chat-panel {
  min-width: 0;
}

.message-list {
  scrollbar-width: thin;
  scrollbar-color: var(--yy-line) transparent;
}

.streaming-cursor {
  display: inline-block;
  width: 0.12rem;
  height: 1em;
  margin-left: 0.2rem;
  vertical-align: -0.12em;
  background: currentColor;
  animation: streaming-blink 0.9s steps(1) infinite;
}

@keyframes streaming-blink {
  50% {
    opacity: 0;
  }
}

@media (min-width: 768px) {
  .messages-page {
    min-height: 40rem;
    max-height: none;
    padding-right: 2rem;
    padding-left: 2rem;
  }

  .ai-workspace {
    overflow: hidden;
  }
}

@media (prefers-reduced-motion: reduce) {
  .streaming-cursor {
    animation: none;
  }
}
</style>
