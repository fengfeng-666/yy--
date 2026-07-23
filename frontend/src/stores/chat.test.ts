import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  fetchChatMessages,
  fetchChatUnreadCount,
  markChatRead,
  sendChatMessage,
} from '@/api/chat'
import { useChatStore } from '@/stores/chat'
import type { ChatMessage } from '@/types/chat'
import { makeUser } from '@/test/factories'

vi.mock('@/api/chat', () => ({
  fetchChatMessages: vi.fn(),
  fetchChatUnreadCount: vi.fn(),
  markChatRead: vi.fn(),
  sendChatMessage: vi.fn(),
}))

function makeMessage(id: number, content = `消息 ${id}`): ChatMessage {
  return {
    id,
    family_id: 1,
    sender_id: 1,
    content,
    created_at: `2026-07-23T10:${String(id).padStart(2, '0')}:00Z`,
    sender: makeUser(),
  }
}

describe('聊天状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('加载最新消息并向前分页', async () => {
    vi.mocked(fetchChatMessages)
      .mockResolvedValueOnce({ items: [makeMessage(3), makeMessage(4)], has_more: true })
      .mockResolvedValueOnce({ items: [makeMessage(1), makeMessage(2)], has_more: false })
    const store = useChatStore()

    await store.loadInitialMessages()
    await store.loadOlderMessages()

    expect(fetchChatMessages).toHaveBeenNthCalledWith(1, { limit: 30 })
    expect(fetchChatMessages).toHaveBeenNthCalledWith(2, { before_id: 3, limit: 30 })
    expect(store.messages.map((message) => message.id)).toEqual([1, 2, 3, 4])
    expect(store.hasMore).toBe(false)
  })

  it('增量轮询时合并并去重消息', async () => {
    vi.mocked(fetchChatMessages)
      .mockResolvedValueOnce({ items: [makeMessage(1), makeMessage(2)], has_more: false })
      .mockResolvedValueOnce({ items: [makeMessage(2), makeMessage(3)], has_more: false })
    const store = useChatStore()
    await store.loadInitialMessages()

    const added = await store.pollNewMessages()

    expect(fetchChatMessages).toHaveBeenLastCalledWith({ after_id: 2, limit: 30 })
    expect(added).toBe(1)
    expect(store.messages.map((message) => message.id)).toEqual([1, 2, 3])
  })

  it('发送成功后追加服务端消息并防止并发发送', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(makeMessage(1, '今晚吃什么？'))
    const store = useChatStore()

    const firstRequest = store.sendMessage('今晚吃什么？')
    const duplicateRequest = await store.sendMessage('重复消息')
    await firstRequest

    expect(duplicateRequest).toBeNull()
    expect(sendChatMessage).toHaveBeenCalledTimes(1)
    expect(store.messages[0].content).toBe('今晚吃什么？')
    expect(store.sending).toBe(false)
  })

  it('同步未读数并标记最新消息已读', async () => {
    vi.mocked(fetchChatMessages).mockResolvedValue({
      items: [makeMessage(8)],
      has_more: false,
    })
    vi.mocked(fetchChatUnreadCount).mockResolvedValue({ unread_count: 3 })
    vi.mocked(markChatRead).mockResolvedValue({ unread_count: 0 })
    const store = useChatStore()

    await store.loadInitialMessages()
    await store.refreshUnreadCount()
    await store.markLatestRead()

    expect(markChatRead).toHaveBeenCalledWith(8)
    expect(store.unreadCount).toBe(0)
  })

  it('轮询失败时保留已有消息并标记连接异常', async () => {
    vi.mocked(fetchChatMessages)
      .mockResolvedValueOnce({ items: [makeMessage(1)], has_more: false })
      .mockRejectedValueOnce(new Error('网络错误'))
    const store = useChatStore()
    await store.loadInitialMessages()

    await expect(store.pollNewMessages()).rejects.toThrow('网络错误')

    expect(store.messages.map((message) => message.id)).toEqual([1])
    expect(store.connectionError).toBe(true)
    expect(store.polling).toBe(false)
  })
})
