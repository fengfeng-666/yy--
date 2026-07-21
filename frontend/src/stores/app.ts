import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

export const useAppStore = defineStore('app', () => {
  const appName = ref('YY私厨')
  const authStore = useAuthStore()
  const familyStore = useFamilyStore()

  const userNickname = computed(() => authStore.nickname)
  const familyName = computed(() => familyStore.familyName)
  const welcomeText = computed(() => `${userNickname.value}，今天也好好吃饭`)

  return {
    appName,
    familyName,
    userNickname,
    welcomeText,
  }
})
