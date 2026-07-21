import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchCurrentUser, login, register } from '@/api/auth'
import type { AuthPayload, LoginPayload, RegisterPayload, UserProfile } from '@/types/api'

const TOKEN_STORAGE_KEY = 'yy-kitchen-access-token'
const USER_STORAGE_KEY = 'yy-kitchen-user'

function readStoredUser(): UserProfile | null {
  const rawValue = window.localStorage.getItem(USER_STORAGE_KEY)
  if (!rawValue) {
    return null
  }

  try {
    return JSON.parse(rawValue) as UserProfile
  } catch {
    window.localStorage.removeItem(USER_STORAGE_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string>(window.localStorage.getItem(TOKEN_STORAGE_KEY) ?? '')
  const currentUser = ref<UserProfile | null>(readStoredUser())
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(accessToken.value) && Boolean(currentUser.value))
  const nickname = computed(() => currentUser.value?.nickname ?? '你')

  function persistAuth(payload: AuthPayload) {
    accessToken.value = payload.tokens.access_token
    currentUser.value = payload.user
    window.localStorage.setItem(TOKEN_STORAGE_KEY, payload.tokens.access_token)
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(payload.user))
  }

  function clearAuth() {
    accessToken.value = ''
    currentUser.value = null
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    window.localStorage.removeItem(USER_STORAGE_KEY)
  }

  async function loginWithPassword(payload: LoginPayload) {
    const authPayload = await login(payload)
    persistAuth(authPayload)
    return authPayload
  }

  async function registerWithPassword(payload: RegisterPayload) {
    const authPayload = await register(payload)
    persistAuth(authPayload)
    return authPayload
  }

  async function restoreSession() {
    if (!accessToken.value) {
      initialized.value = true
      return
    }

    try {
      currentUser.value = await fetchCurrentUser()
      window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(currentUser.value))
    } catch {
      clearAuth()
    } finally {
      initialized.value = true
    }
  }

  return {
    accessToken,
    currentUser,
    initialized,
    isAuthenticated,
    nickname,
    clearAuth,
    loginWithPassword,
    registerWithPassword,
    restoreSession,
  }
})
