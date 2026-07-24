import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { ApiError } from '@/api/http'
import {
  cancelAiChatAction,
  confirmAiChatAction,
  deleteAiChatConversation,
  fetchAiChatConversations,
  fetchAiChatMessages,
  streamAiChatMessage,
} from '@/api/aiChat'
import type { AiChatConversation, AiChatMessage } from '@/types/aiChat'

const DEFAULT_IMAGE_PROMPT = '请根据这张冰箱图片推荐可以做的菜'
let nextOptimisticMessageId = -1

function shouldMarkConnectionError(error: unknown) {
  if (error instanceof ApiError && error.statusCode) {
    return error.statusCode >= 500
  }
  return true
}

export const useAiChatStore = defineStore('ai-chat', () => {
  const conversations = ref<AiChatConversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const messages = ref<AiChatMessage[]>([])
  const hasMore = ref(false)
  const initialLoading = ref(false)
  const olderLoading = ref(false)
  const sending = ref(false)
  const connectionError = ref(false)
  const selectedImage = ref<File | null>(null)
  const isDraftConversation = ref(false)

  const currentConversation = computed(
    () => conversations.value.find((conversation) => conversation.id === currentConversationId.value) ?? null,
  )
  const oldestMessageId = computed(() => messages.value[0]?.id)

  function getConversationSortTime(conversation: AiChatConversation) {
    return conversation.last_message_at ?? conversation.updated_at
  }

  function sortConversations(items: AiChatConversation[]) {
    return [...items].sort((left, right) => {
      const rightTime = new Date(getConversationSortTime(right)).getTime()
      const leftTime = new Date(getConversationSortTime(left)).getTime()
      if (rightTime !== leftTime) return rightTime - leftTime
      return right.id - left.id
    })
  }

  function upsertConversation(incoming: AiChatConversation) {
    const merged = new Map(conversations.value.map((conversation) => [conversation.id, conversation]))
    merged.set(incoming.id, incoming)
    conversations.value = sortConversations(Array.from(merged.values()))
  }

  function removeConversation(conversationId: number) {
    conversations.value = conversations.value.filter((conversation) => conversation.id !== conversationId)
  }

  function clearMessageState() {
    messages.value = []
    hasMore.value = false
    connectionError.value = false
  }

  function syncConversationSelection() {
    if (
      currentConversationId.value &&
      conversations.value.some((conversation) => conversation.id === currentConversationId.value)
    ) {
      return
    }
    if (isDraftConversation.value) {
      currentConversationId.value = null
      return
    }
    currentConversationId.value = conversations.value[0]?.id ?? null
  }

  function mergeMessages(incoming: AiChatMessage[]) {
    if (!incoming.length) return 0
    const previousIds = new Set(messages.value.map((message) => message.id))
    const merged = new Map(messages.value.map((message) => [message.id, message]))
    incoming.forEach((message) => merged.set(message.id, message))
    messages.value = Array.from(merged.values()).sort((a, b) => a.id - b.id)
    return incoming.filter((message) => !previousIds.has(message.id)).length
  }

  async function loadConversations() {
    const page = await fetchAiChatConversations()
    conversations.value = sortConversations(page.items)
    syncConversationSelection()
    return conversations.value
  }

  async function loadInitialMessages() {
    initialLoading.value = true
    try {
      await loadConversations()
      if (!currentConversationId.value) {
        clearMessageState()
        return []
      }
      const page = await fetchAiChatMessages({ conversation_id: currentConversationId.value, limit: 30 })
      messages.value = page.items
      hasMore.value = page.has_more
      connectionError.value = false
      return page.items
    } catch (error) {
      connectionError.value = shouldMarkConnectionError(error)
      throw error
    } finally {
      initialLoading.value = false
    }
  }

  function replaceMessage(incoming: AiChatMessage) {
    const existingIndex = messages.value.findIndex((message) => message.id === incoming.id)
    if (existingIndex === -1) {
      mergeMessages([incoming])
      return
    }
    messages.value = messages.value.map((message) => (message.id === incoming.id ? incoming : message))
  }

  async function loadOlderMessages() {
    if (olderLoading.value || !hasMore.value || !oldestMessageId.value || !currentConversationId.value) return 0
    olderLoading.value = true
    try {
      const page = await fetchAiChatMessages({
        conversation_id: currentConversationId.value,
        before_id: oldestMessageId.value,
        limit: 30,
      })
      const added = mergeMessages(page.items)
      hasMore.value = page.has_more
      connectionError.value = false
      return added
    } catch (error) {
      connectionError.value = shouldMarkConnectionError(error)
      throw error
    } finally {
      olderLoading.value = false
    }
  }

  async function sendMessage(content: string) {
    if (sending.value) return null
    sending.value = true
    const userMessageId = nextOptimisticMessageId--
    const assistantMessageId = nextOptimisticMessageId--
    const createdAt = new Date().toISOString()
    const conversationId = currentConversationId.value ?? 0
    const optimisticUser: AiChatMessage = {
      id: userMessageId,
      family_id: 0,
      user_id: 0,
      conversation_id: conversationId,
      role: 'user',
      content: content.trim() || DEFAULT_IMAGE_PROMPT,
      message_kind: selectedImage.value ? 'fridge_image' : 'text',
      metadata_json: null,
      created_at: createdAt,
    }
    const optimisticAssistant: AiChatMessage = {
      id: assistantMessageId,
      family_id: 0,
      user_id: 0,
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
      message_kind: 'recommendation',
      metadata_json: {
        summary: '',
        recognized_ingredients: [],
        recommendations: [],
        retrieval_sources: [],
        tool_calls: [],
      },
      created_at: createdAt,
    }
    messages.value = [...messages.value, optimisticUser, optimisticAssistant]

    try {
      const normalizedContent = content.trim() || DEFAULT_IMAGE_PROMPT
      const turn = await streamAiChatMessage(
        {
          content: normalizedContent,
          conversationId: currentConversationId.value,
          imageFile: selectedImage.value,
        },
        {
          onDelta(delta) {
            const message = messages.value.find((item) => item.id === assistantMessageId)
            if (!message) return
            const summary = `${message.metadata_json?.summary ?? ''}${delta}`
            replaceMessage({
              ...message,
              content: summary,
              metadata_json: { ...message.metadata_json!, summary },
            })
          },
        },
      )
      messages.value = messages.value.filter(
        (message) => message.id !== userMessageId && message.id !== assistantMessageId,
      )
      upsertConversation(turn.conversation)
      currentConversationId.value = turn.conversation.id
      isDraftConversation.value = false
      mergeMessages([turn.user_message, turn.assistant_message])
      clearSelectedImage()
      connectionError.value = false
      return turn
    } catch (error) {
      messages.value = messages.value.filter(
        (message) => message.id !== userMessageId && message.id !== assistantMessageId,
      )
      connectionError.value = shouldMarkConnectionError(error)
      throw error
    } finally {
      sending.value = false
    }
  }

  function setSelectedImage(file: File | null) {
    selectedImage.value = file
  }

  function clearSelectedImage() {
    selectedImage.value = null
  }

  async function selectConversation(conversationId: number) {
    currentConversationId.value = conversationId
    isDraftConversation.value = false
    clearMessageState()
    return loadInitialMessages()
  }

  function startNewConversation() {
    currentConversationId.value = null
    isDraftConversation.value = true
    clearMessageState()
    clearSelectedImage()
  }

  async function deleteConversation(conversationId: number) {
    await deleteAiChatConversation(conversationId)
    const wasCurrentConversation = currentConversationId.value === conversationId
    removeConversation(conversationId)
    if (wasCurrentConversation) {
      const nextConversation = conversations.value[0] ?? null
      if (nextConversation) {
        currentConversationId.value = nextConversation.id
        isDraftConversation.value = false
        clearMessageState()
        const page = await fetchAiChatMessages({ conversation_id: nextConversation.id, limit: 30 })
        messages.value = page.items
        hasMore.value = page.has_more
        connectionError.value = false
      } else {
        startNewConversation()
      }
    } else {
      syncConversationSelection()
    }
  }

  async function confirmAction(messageId: number) {
    const response = await confirmAiChatAction(messageId)
    replaceMessage(response.message)
    return response.message
  }

  async function cancelAction(messageId: number) {
    const response = await cancelAiChatAction(messageId)
    replaceMessage(response.message)
    return response.message
  }

  function reset() {
    conversations.value = []
    currentConversationId.value = null
    messages.value = []
    hasMore.value = false
    connectionError.value = false
    isDraftConversation.value = false
    clearSelectedImage()
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    messages,
    hasMore,
    initialLoading,
    olderLoading,
    sending,
    connectionError,
    selectedImage,
    oldestMessageId,
    loadConversations,
    loadInitialMessages,
    loadOlderMessages,
    sendMessage,
    setSelectedImage,
    clearSelectedImage,
    selectConversation,
    deleteConversation,
    confirmAction,
    cancelAction,
    startNewConversation,
    reset,
  }
})
