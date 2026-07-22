import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { fetchHomeSummary } from '@/api/home'
import type { HomeSummary } from '@/types/home'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

export const useAppStore = defineStore('app', () => {
  const appName = ref('YY私厨')
  const homeSummary = ref<HomeSummary | null>(null)
  const homeLoading = ref(false)
  const authStore = useAuthStore()
  const familyStore = useFamilyStore()

  const userNickname = computed(() => authStore.nickname)
  const familyName = computed(() => familyStore.familyName)
  const welcomeText = computed(() => `${userNickname.value}，今天也好好吃饭`)

  async function loadHomeSummary() {
    homeLoading.value = true
    try {
      homeSummary.value = await fetchHomeSummary()
      return homeSummary.value
    } finally {
      homeLoading.value = false
    }
  }

  return {
    appName,
    familyName,
    homeLoading,
    homeSummary,
    userNickname,
    welcomeText,
    loadHomeSummary,
  }
})
