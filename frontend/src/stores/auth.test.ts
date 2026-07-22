import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser, login, updateProfile } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { makeUser } from '@/test/factories'

vi.mock('@/api/auth', () => ({
  fetchCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  updateProfile: vi.fn(),
}))

describe('认证状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('登录成功后保存令牌和用户信息', async () => {
    const user = makeUser()
    vi.mocked(login).mockResolvedValue({
      user,
      tokens: {
        access_token: 'access-token',
        token_type: 'bearer',
        expires_at: '2026-07-22T01:00:00Z',
      },
    })
    const store = useAuthStore()

    await store.loginWithPassword({ username: 'chef01', password: 'secret123' })

    expect(store.isAuthenticated).toBe(true)
    expect(store.currentUser).toEqual(user)
    expect(window.localStorage.getItem('yy-kitchen-access-token')).toBe('access-token')
    expect(JSON.parse(window.localStorage.getItem('yy-kitchen-user') ?? '{}')).toEqual(user)
  })

  it('恢复会话失败时清理过期凭证', async () => {
    window.localStorage.setItem('yy-kitchen-access-token', 'expired-token')
    vi.mocked(fetchCurrentUser).mockRejectedValue(new Error('unauthorized'))
    const store = useAuthStore()

    await store.restoreSession()

    expect(store.initialized).toBe(true)
    expect(store.isAuthenticated).toBe(false)
    expect(window.localStorage.getItem('yy-kitchen-access-token')).toBeNull()
  })

  it('更新资料后同步本地缓存', async () => {
    const updatedUser = makeUser({ nickname: '新昵称' })
    vi.mocked(updateProfile).mockResolvedValue(updatedUser)
    const store = useAuthStore()

    await store.updateCurrentProfile({ nickname: '新昵称' })

    expect(store.nickname).toBe('新昵称')
    expect(JSON.parse(window.localStorage.getItem('yy-kitchen-user') ?? '{}')).toEqual(updatedUser)
  })
})
