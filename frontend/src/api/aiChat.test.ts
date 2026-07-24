import { describe, expect, it, vi } from 'vitest'

import { streamAiChatMessage } from '@/api/aiChat'
import type { AiChatTurnResponse } from '@/types/aiChat'

function makeTurn(): AiChatTurnResponse {
  const createdAt = '2026-07-24T10:00:00Z'
  return {
    conversation: {
      id: 3,
      family_id: 1,
      user_id: 1,
      title: '推荐一道菜',
      created_at: createdAt,
      updated_at: createdAt,
    },
    user_message: {
      id: 10,
      family_id: 1,
      user_id: 1,
      conversation_id: 3,
      role: 'user',
      content: '推荐一道菜',
      message_kind: 'text',
      created_at: createdAt,
    },
    assistant_message: {
      id: 11,
      family_id: 1,
      user_id: 1,
      conversation_id: 3,
      role: 'assistant',
      content: '番茄炒蛋',
      message_kind: 'recommendation',
      created_at: createdAt,
    },
  }
}

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)))
      controller.close()
    },
  })
  return new Response(body, { headers: { 'Content-Type': 'text/event-stream' } })
}

describe('AI 聊天 SSE 客户端', () => {
  it('跨数据块解析增量事件和完成事件，并携带鉴权', async () => {
    const turn = makeTurn()
    const fetchMock = vi.fn().mockResolvedValue(
      sseResponse([
        'event: ready\ndata: {"status":"processing"}\n\nevent: del',
        'ta\ndata: {"content":"番茄"}\n\nevent: complete\ndata: ',
        `${JSON.stringify(turn)}\n\n`,
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)
    window.localStorage.setItem('yy-kitchen-access-token', 'test-token')
    const deltas: string[] = []

    const result = await streamAiChatMessage(
      { content: '推荐一道菜' },
      { onDelta: (content) => deltas.push(content) },
    )

    expect(result.assistant_message.id).toBe(11)
    expect(deltas).toEqual(['番茄'])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/ai-chat/messages/stream',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
      }),
    )
  })

  it('把 SSE error 事件转换成带状态码的 ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        sseResponse([
          'event: error\ndata: {"message":"AI 功能尚未开启","status_code":400}\n\n',
        ]),
      ),
    )

    await expect(streamAiChatMessage({ content: '推荐一道菜' })).rejects.toEqual(
      expect.objectContaining({
        name: 'ApiError',
        message: 'AI 功能尚未开启',
        statusCode: 400,
      }),
    )
  })
})
