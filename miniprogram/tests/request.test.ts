import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('request', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubGlobal('uni', {
      getStorageSync: vi.fn(() => 'token-123'),
      removeStorageSync: vi.fn(),
      reLaunch: vi.fn(),
      request: vi.fn(),
    })
  })

  it('returns response data and includes the access token', async () => {
    const { request } = await import('../src/utils/request')
    const uniMock = globalThis.uni as unknown as {
      request: ReturnType<typeof vi.fn>
    }
    uniMock.request.mockImplementation((options) => {
      expect(options.header).toEqual({ Authorization: 'Bearer token-123' })
      options.success({ statusCode: 200, data: { code: 0, message: 'ok', data: { id: 7 } } })
    })

    await expect(request<{ id: number }>({ url: '/home/summary' })).resolves.toEqual({ id: 7 })
  })

  it('clears local authentication after an unauthorized response', async () => {
    const { request } = await import('../src/utils/request')
    const uniMock = globalThis.uni as unknown as {
      request: ReturnType<typeof vi.fn>
      removeStorageSync: ReturnType<typeof vi.fn>
    }
    uniMock.request.mockImplementation((options) => {
      options.success({
        statusCode: 401,
        data: { code: 40100, message: '请先登录', data: null },
      })
    })

    await expect(request({ url: '/auth/me' })).rejects.toThrow('请先登录')
    expect(uniMock.removeStorageSync).toHaveBeenCalledWith('yy-kitchen-access-token')
    expect(uniMock.removeStorageSync).toHaveBeenCalledWith('yy-kitchen-user')
  })
})
