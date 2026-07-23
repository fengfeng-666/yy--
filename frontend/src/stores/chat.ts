import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchChatMessages,
  fetchChatUnreadCount,
  markChatRead,
  sendChatMessage,
} from '@/api/chat'
import type { ChatMessage } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const hasMore = ref(false)
  const initialLoading = ref(false)
  const olderLoading = ref(false)
  const polling = ref(false)
  const sending = ref(false)
  const unreadCount = ref(0)
  const connectionError = ref(false)

  const oldestMessageId = computed(() => messages.value[0]?.id)
  const latestMessageId = computed(() => messages.value.at(-1)?.id)

  function mergeMessages(incoming: ChatMessage[]) {
    if (!incoming.length) return 0
    const previousIds = new Set(messages.value.map((message) => message.id))
    const merged = new Map(messages.value.map((message) => [message.id, message]))
    incoming.forEach((message) => merged.set(message.id, message))
    messages.value = Array.from(merged.values()).sort((a, b) => a.id - b.id)
    return incoming.filter((message) => !previousIds.has(message.id)).length
  }

  async function loadInitialMessages() {
    initialLoading.value = true
    connectionError.value = false
    try {
      const page = await fetchChatMessages({ limit: 30 })
      messages.value = page.items
      hasMore.value = page.has_more
      return page.items
    } catch (error) {
      connectionError.value = true
      throw error
    } finally {
      initialLoading.value = false
    }
  }

  async function loadOlderMessages() {
    if (olderLoading.value || !hasMore.value || !oldestMessageId.value) return 0
    olderLoading.value = true
    try {
      const page = await fetchChatMessages({ before_id: oldestMessageId.value, limit: 30 })
      const added = mergeMessages(page.items)
      hasMore.value = page.has_more
      connectionError.value = false
      return added
    } catch (error) {
      connectionError.value = true
      throw error
    } finally {
      olderLoading.value = false
    }
  }

  async function pollNewMessages() {
    if (polling.value) return 0
    polling.value = true
    try {
      const page = await fetchChatMessages({
        ...(latestMessageId.value ? { after_id: latestMessageId.value } : {}),
        limit: 30,
      })
      const added = mergeMessages(page.items)
      connectionError.value = false
      return added
    } catch (error) {
      connectionError.value = true
      throw error
    } finally {
      polling.value = false
    }
  }

  async function sendMessage(content: string) {
    if (sending.value) return null
    sending.value = true
    try {
      const message = await sendChatMessage(content)
      mergeMessages([message])
      connectionError.value = false
      return message
    } finally {
      sending.value = false
    }
  }

  async function refreshUnreadCount() {
    const result = await fetchChatUnreadCount()
    unreadCount.value = result.unread_count
    return unreadCount.value
  }

  async function markLatestRead() {
    if (!latestMessageId.value) {
      unreadCount.value = 0
      return 0
    }
    const result = await markChatRead(latestMessageId.value)
    unreadCount.value = result.unread_count
    return unreadCount.value
  }

  function reset() {
    messages.value = []
    hasMore.value = false
    unreadCount.value = 0
    connectionError.value = false
  }

  return {
    messages,
    hasMore,
    initialLoading,
    olderLoading,
    polling,
    sending,
    unreadCount,
    connectionError,
    oldestMessageId,
    latestMessageId,
    loadInitialMessages,
    loadOlderMessages,
    pollNewMessages,
    sendMessage,
    refreshUnreadCount,
    markLatestRead,
    reset,
  }
})
