import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const appName = ref('YY私厨')
  const familyName = ref('YY 私厨')
  const userNickname = ref('睿丰')

  const welcomeText = computed(() => `${userNickname.value}，今天也好好吃饭`)

  return {
    appName,
    familyName,
    userNickname,
    welcomeText,
  }
})
