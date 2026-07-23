import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type { ChatMessage, ChatMessagePage, ChatUnreadCount } from '@/types/chat'

export async function fetchChatMessages(params?: {
  before_id?: number
  after_id?: number
  limit?: number
}): Promise<ChatMessagePage> {
  const { data } = await http.get<ApiResponse<ChatMessagePage>>('/chat/messages', { params })
  return data.data
}

export async function sendChatMessage(content: string): Promise<ChatMessage> {
  const { data } = await http.post<ApiResponse<ChatMessage>>('/chat/messages', { content })
  return data.data
}

export async function fetchChatUnreadCount(): Promise<ChatUnreadCount> {
  const { data } = await http.get<ApiResponse<ChatUnreadCount>>('/chat/unread-count')
  return data.data
}

export async function markChatRead(lastReadMessageId: number): Promise<ChatUnreadCount> {
  const { data } = await http.post<ApiResponse<ChatUnreadCount>>('/chat/read', {
    last_read_message_id: lastReadMessageId,
  })
  return data.data
}
