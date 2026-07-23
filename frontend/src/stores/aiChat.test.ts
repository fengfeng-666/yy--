import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  deleteAiChatConversation,
  fetchAiChatConversations,
  fetchAiChatMessages,
  sendAiChatMessage,
} from '@/api/aiChat'
import { ApiError } from '@/api/http'
import { useAiChatStore } from '@/stores/aiChat'
import type { AiChatConversation, AiChatMessage } from '@/types/aiChat'

vi.mock('@/api/aiChat', () => ({
  deleteAiChatConversation: vi.fn(),
  fetchAiChatConversations: vi.fn(),
  fetchAiChatMessages: vi.fn(),
  sendAiChatMessage: vi.fn(),
}))

function makeConversation(id: number, title = `对话 ${id}`): AiChatConversation {
  return {
    id,
    family_id: 1,
    user_id: 1,
    title,
    last_message_preview: `最近消息 ${id}`,
    last_message_at: `2026-07-23T10:${String(id).padStart(2, '0')}:30Z`,
    created_at: `2026-07-23T10:${String(id).padStart(2, '0')}:00Z`,
    updated_at: `2026-07-23T10:${String(id).padStart(2, '0')}:30Z`,
  }
}

function makeMessage(id: number, role: 'user' | 'assistant' = 'assistant', conversationId = 1): AiChatMessage {
  return {
    id,
    family_id: 1,
    user_id: 1,
    conversation_id: conversationId,
    role,
    content: role === 'user' ? `问题 ${id}` : `回答 ${id}`,
    message_kind: role === 'user' ? 'text' : 'recommendation',
    metadata_json:
      role === 'assistant'
        ? {
            summary: `总结 ${id}`,
            recognized_ingredients: ['鸡蛋'],
            recommendations: [
              {
                dish_name: '番茄炒蛋',
                rating: 5,
                required_ingredients: ['番茄', '鸡蛋'],
                matched_ingredients: ['鸡蛋'],
                steps: ['切番茄', '炒鸡蛋'],
                reason: '简单好做',
              },
            ],
          }
        : null,
    created_at: `2026-07-23T10:${String(id).padStart(2, '0')}:00Z`,
  }
}

describe('AI 聊天状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('加载最新 AI 消息并向前分页', async () => {
    vi.mocked(fetchAiChatConversations).mockResolvedValue({ items: [makeConversation(1)] })
    vi.mocked(fetchAiChatMessages)
      .mockResolvedValueOnce({ items: [makeMessage(3, 'user'), makeMessage(4)], has_more: true })
      .mockResolvedValueOnce({ items: [makeMessage(1, 'user'), makeMessage(2)], has_more: false })
    const store = useAiChatStore()

    await store.loadInitialMessages()
    await store.loadOlderMessages()

    expect(fetchAiChatConversations).toHaveBeenCalledTimes(1)
    expect(fetchAiChatMessages).toHaveBeenNthCalledWith(1, { conversation_id: 1, limit: 30 })
    expect(fetchAiChatMessages).toHaveBeenNthCalledWith(2, { conversation_id: 1, before_id: 3, limit: 30 })
    expect(store.messages.map((message) => message.id)).toEqual([1, 2, 3, 4])
    expect(store.currentConversationId).toBe(1)
    expect(store.hasMore).toBe(false)
  })

  it('发送图片消息时使用默认提示词并创建新对话', async () => {
    vi.mocked(sendAiChatMessage).mockResolvedValue({
      conversation: makeConversation(9, '冰箱图片推荐'),
      user_message: makeMessage(1, 'user', 9),
      assistant_message: makeMessage(2, 'assistant', 9),
    })
    const store = useAiChatStore()
    const file = new File(['fake'], 'fridge.png', { type: 'image/png' })
    store.startNewConversation()
    store.setSelectedImage(file)

    const turn = await store.sendMessage('')

    expect(turn?.conversation.id).toBe(9)
    expect(turn?.assistant_message.id).toBe(2)
    expect(sendAiChatMessage).toHaveBeenCalledWith({
      content: '请根据这张冰箱图片推荐可以做的菜',
      conversationId: null,
      imageFile: file,
    })
    expect(store.selectedImage).toBeNull()
    expect(store.currentConversationId).toBe(9)
    expect(store.conversations[0]?.id).toBe(9)
    expect(store.messages.map((message) => message.id)).toEqual([1, 2])
  })

  it('没有历史对话时加载空白新对话', async () => {
    vi.mocked(fetchAiChatConversations).mockResolvedValue({ items: [] })
    const store = useAiChatStore()

    const items = await store.loadInitialMessages()

    expect(items).toEqual([])
    expect(fetchAiChatMessages).not.toHaveBeenCalled()
    expect(store.currentConversationId).toBeNull()
    expect(store.messages).toEqual([])
  })

  it('删除当前对话后自动切换到下一条历史对话', async () => {
    vi.mocked(deleteAiChatConversation).mockResolvedValue()
    vi.mocked(fetchAiChatConversations).mockResolvedValue({
      items: [makeConversation(2), makeConversation(1)],
    })
    vi.mocked(fetchAiChatMessages)
      .mockResolvedValueOnce({ items: [makeMessage(1, 'user', 2), makeMessage(2, 'assistant', 2)], has_more: false })
      .mockResolvedValueOnce({ items: [makeMessage(3, 'user', 1), makeMessage(4, 'assistant', 1)], has_more: false })
    const store = useAiChatStore()

    await store.loadInitialMessages()
    await store.deleteConversation(2)

    expect(deleteAiChatConversation).toHaveBeenCalledWith(2)
    expect(store.currentConversationId).toBe(1)
    expect(store.conversations.map((conversation) => conversation.id)).toEqual([1])
    expect(store.messages.map((message) => message.id)).toEqual([3, 4])
  })

  it('发送失败时保留已选图片并标记连接异常', async () => {
    vi.mocked(sendAiChatMessage).mockRejectedValue(new Error('AI 服务异常'))
    const store = useAiChatStore()
    const file = new File(['fake'], 'fridge.png', { type: 'image/png' })
    store.setSelectedImage(file)

    await expect(store.sendMessage('看看能做什么')).rejects.toThrow('AI 服务异常')

    expect(store.selectedImage).toBe(file)
    expect(store.connectionError).toBe(true)
    expect(store.sending).toBe(false)
  })

  it('业务错误时不显示连接异常横幅', async () => {
    vi.mocked(fetchAiChatConversations).mockResolvedValue({ items: [makeConversation(1)] })
    vi.mocked(fetchAiChatMessages).mockRejectedValue(new ApiError('AI 对话不存在或已被删除', 404))
    const store = useAiChatStore()

    await expect(store.loadInitialMessages()).rejects.toThrow('AI 对话不存在或已被删除')

    expect(store.connectionError).toBe(false)
  })
})
