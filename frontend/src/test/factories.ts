import type { FamilyAccessPayload, FamilyMember, FamilyProfile, UserProfile } from '@/types/api'
import type { DishItem } from '@/types/dish'
import type { MealOrder } from '@/types/order'

export function makeUser(overrides: Partial<UserProfile> = {}): UserProfile {
  return {
    id: 1,
    username: 'chef01',
    nickname: '主厨',
    is_active: true,
    created_at: '2026-07-22T00:00:00Z',
    ...overrides,
  }
}

export function makeFamilyMember(overrides: Partial<FamilyMember> = {}): FamilyMember {
  const user = overrides.user ?? makeUser({ id: overrides.user_id ?? 1 })
  return {
    id: 1,
    family_id: 1,
    user_id: user.id,
    role: 'owner',
    joined_at: '2026-07-22T00:00:00Z',
    ...overrides,
    user,
  }
}

export function makeFamily(overrides: Partial<FamilyProfile> = {}): FamilyProfile {
  return {
    id: 1,
    name: 'YY私厨',
    description: null,
    cover_url: null,
    invite_code: 'YY2026',
    owner_id: 1,
    max_members: 2,
    created_at: '2026-07-22T00:00:00Z',
    updated_at: '2026-07-22T00:00:00Z',
    members: [makeFamilyMember()],
    ...overrides,
  }
}

export function makeFamilyAccess(overrides: Partial<FamilyProfile> = {}): FamilyAccessPayload {
  return { family: makeFamily(overrides), needs_onboarding: false }
}

export function makeDish(overrides: Partial<DishItem> = {}): DishItem {
  return {
    id: 1,
    family_id: 1,
    name: '番茄炒蛋',
    description: '家常味道',
    price: 18,
    image_url: null,
    cooking_minutes: null,
    difficulty: null,
    spicy_level: null,
    need_prepare_ahead: false,
    suitable_for_weekday: false,
    is_available: true,
    ingredients: [],
    steps: [],
    preferences: [],
    created_at: '2026-07-22T00:00:00Z',
    updated_at: '2026-07-22T00:00:00Z',
    ...overrides,
  }
}

export function makeOrder(overrides: Partial<MealOrder> = {}): MealOrder {
  const requester = makeUser({ id: 1, nickname: '小雨' })
  const cook = makeUser({ id: 2, username: 'chef02', nickname: '阿阳' })
  return {
    id: 1,
    family_id: 1,
    requester_id: requester.id,
    cook_id: cook.id,
    status: 'pending',
    planned_date: '2026-07-22',
    planned_time: '19:00:00',
    note: null,
    accepted_at: null,
    created_at: '2026-07-22T00:00:00Z',
    updated_at: '2026-07-22T00:00:00Z',
    requester,
    cook,
    items: [],
    status_logs: [],
    review: null,
    ...overrides,
  }
}
