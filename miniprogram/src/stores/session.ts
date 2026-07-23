import { reactive } from 'vue'

import type { AuthPayload, FamilyProfile, UserProfile } from '@/types/api'

interface SessionState {
  token: string
  user: UserProfile | null
  family: FamilyProfile | null
}

function readUser(): UserProfile | null {
  return uni.getStorageSync('yy-kitchen-user') || null
}

export const session = reactive<SessionState>({
  token: uni.getStorageSync('yy-kitchen-access-token') || '',
  user: readUser(),
  family: null,
})

export function applyAuth(payload: AuthPayload) {
  session.token = payload.tokens.access_token
  session.user = payload.user
  uni.setStorageSync('yy-kitchen-access-token', payload.tokens.access_token)
  uni.setStorageSync('yy-kitchen-user', payload.user)
}

export function clearSession() {
  session.token = ''
  session.user = null
  session.family = null
  uni.removeStorageSync('yy-kitchen-access-token')
  uni.removeStorageSync('yy-kitchen-user')
}
