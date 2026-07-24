import http, { ApiError } from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type {
  AiChatConversationPage,
  AiChatMessagePage,
  AiChatTurnResponse,
  ConfirmAiActionResponse,
} from '@/types/aiChat'
import { apiBaseUrl } from '@/utils/env'

interface AiChatStreamEvent {
  event: string
  data: string
}

export interface AiChatStreamHandlers {
  onDelta?: (content: string) => void // eslint-disable-line no-unused-vars
}

function parseSseEvent(block: string): AiChatStreamEvent | null {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of block.split(/\r?\n/)) {
    if (!line || line.startsWith(':')) continue
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }
  return dataLines.length ? { event, data: dataLines.join('\n') } : null
}

async function readErrorResponse(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { message?: string }
    return new ApiError(body.message || `请求失败（${response.status}）`, response.status)
  } catch {
    return new ApiError(`请求失败（${response.status}）`, response.status)
  }
}

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

  const { data } = await http.post<ApiResponse<AiChatTurnResponse>>('/ai-chat/messages', formData)
  return data.data
}

export async function streamAiChatMessage(
  payload: {
    content: string
    conversationId?: number | null
    imageFile?: File | null
  },
  handlers: AiChatStreamHandlers = {},
  signal?: AbortSignal,
): Promise<AiChatTurnResponse> {
  const formData = new FormData()
  formData.append('content', payload.content)
  if (payload.conversationId) formData.append('conversation_id', String(payload.conversationId))
  if (payload.imageFile) formData.append('image', payload.imageFile)

  const token = window.localStorage.getItem('yy-kitchen-access-token')
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}/ai-chat/messages/stream`, {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError('无法连接服务器，请检查后端服务或网络连接')
  }

  if (!response.ok) throw await readErrorResponse(response)
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('text/event-stream')) {
    throw new ApiError('服务器未返回 SSE 流，请检查代理配置', response.status)
  }
  if (!response.body) throw new ApiError('浏览器未收到可读取的流式响应', response.status)

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let completedTurn: AiChatTurnResponse | null = null

  const handleEvent = (event: AiChatStreamEvent | null) => {
    if (!event) return
    let data: unknown
    try {
      data = JSON.parse(event.data)
    } catch {
      throw new ApiError('AI 流式响应格式错误')
    }
    if (event.event === 'delta') {
      const content = (data as { content?: unknown }).content
      if (typeof content === 'string') handlers.onDelta?.(content)
    } else if (event.event === 'complete') {
      completedTurn = data as AiChatTurnResponse
    } else if (event.event === 'error') {
      const error = data as { message?: string; status_code?: number }
      throw new ApiError(error.message || 'AI 服务暂时不可用，请稍后再试', error.status_code)
    }
  }

  try {
    let streamDone = false
    while (!streamDone) {
      const { done, value } = await reader.read()
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true })
      streamDone = done

      let boundary = buffer.match(/\r?\n\r?\n/)
      while (boundary?.index !== undefined) {
        const block = buffer.slice(0, boundary.index)
        buffer = buffer.slice(boundary.index + boundary[0].length)
        handleEvent(parseSseEvent(block))
        boundary = buffer.match(/\r?\n\r?\n/)
      }
    }
    if (buffer.trim()) handleEvent(parseSseEvent(buffer))
  } catch (error) {
    if (error instanceof ApiError || (error instanceof DOMException && error.name === 'AbortError')) {
      throw error
    }
    throw new ApiError('AI 流式响应中断，请检查网络后重试')
  } finally {
    reader.releaseLock()
  }
  if (!completedTurn) throw new ApiError('AI 流式响应意外中断，请重试')
  return completedTurn
}

export async function confirmAiChatAction(messageId: number): Promise<ConfirmAiActionResponse> {
  const { data } = await http.post<ApiResponse<ConfirmAiActionResponse>>(`/ai-chat/actions/${messageId}/confirm`)
  return data.data
}

export async function cancelAiChatAction(messageId: number): Promise<ConfirmAiActionResponse> {
  const { data } = await http.post<ApiResponse<ConfirmAiActionResponse>>(`/ai-chat/actions/${messageId}/cancel`)
  return data.data
}
