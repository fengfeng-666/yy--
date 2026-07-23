import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type { AiChatConversationPage, AiChatMessagePage, AiChatTurnResponse } from '@/types/aiChat'

export async function fetchAiChatConversations(): Promise<AiChatConversationPage> {
  const { data } = await http.get<ApiResponse<AiChatConversationPage>>('/ai-chat/conversations')
  return data.data
}

export async function deleteAiChatConversation(conversationId: number): Promise<void> {
  await http.delete<ApiResponse<null>>(`/ai-chat/conversations/${conversationId}`)
}

export async function fetchAiChatMessages(params?: {
  conversation_id: number
  before_id?: number
  limit?: number
}): Promise<AiChatMessagePage> {
  const { data } = await http.get<ApiResponse<AiChatMessagePage>>('/ai-chat/messages', { params })
  return data.data
}

export async function sendAiChatMessage(payload: {
  content: string
  conversationId?: number | null
  imageFile?: File | null
}): Promise<AiChatTurnResponse> {
  const formData = new FormData()
  formData.append('content', payload.content)
  if (payload.conversationId) {
    formData.append('conversation_id', String(payload.conversationId))
  }
  if (payload.imageFile) {
    formData.append('image', payload.imageFile)
  }

  const { data } = await http.post<ApiResponse<AiChatTurnResponse>>('/ai-chat/messages', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data.data
}
