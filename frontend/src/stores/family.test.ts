import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createFamily,
  fetchCurrentFamily,
  fetchCurrentFamilyMembers,
  joinFamily,
} from '@/api/family'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'
import { makeFamily, makeFamilyAccess, makeUser } from '@/test/factories'

vi.mock('@/api/auth', () => ({
  fetchCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  updateProfile: vi.fn(),
}))

vi.mock('@/api/family', () => ({
  createFamily: vi.fn(),
  fetchCurrentFamily: vi.fn(),
  fetchCurrentFamilyMembers: vi.fn(),
  joinFamily: vi.fn(),
}))

describe('家庭状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('创建家庭后填充家庭和成员状态', async () => {
    const payload = makeFamilyAccess()
    vi.mocked(createFamily).mockResolvedValue(payload)
    const authStore = useAuthStore()
    authStore.currentUser = makeUser({ id: 1 })
    const store = useFamilyStore()

    await store.createFamilySpace({ name: 'YY私厨' })

    expect(store.initialized).toBe(true)
    expect(store.hasFamily).toBe(true)
    expect(store.familyName).toBe('YY私厨')
    expect(store.isOwner).toBe(true)
    expect(store.members).toHaveLength(1)
  })

  it('加入家庭时应用接口返回的数据', async () => {
    const payload = makeFamilyAccess({ name: '新的家庭' })
    vi.mocked(joinFamily).mockResolvedValue(payload)
    const store = useFamilyStore()

    await store.joinFamilySpace({ invite_code: 'YY2026' })

    expect(store.familyName).toBe('新的家庭')
    expect(store.inviteCode).toBe('YY2026')
  })

  it('当前用户没有家庭时完成初始化并清空状态', async () => {
    vi.mocked(fetchCurrentFamily).mockRejectedValue(new Error('not found'))
    vi.mocked(fetchCurrentFamilyMembers).mockResolvedValue([])
    const store = useFamilyStore()
    store.currentFamily = makeFamily()

    await store.loadCurrentFamily()

    expect(store.initialized).toBe(true)
    expect(store.currentFamily).toBeNull()
    expect(store.members).toEqual([])
  })
})
