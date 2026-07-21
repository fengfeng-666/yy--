import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createFamily,
  fetchCurrentFamily,
  fetchCurrentFamilyMembers,
  joinFamily,
} from '@/api/family'
import type {
  CreateFamilyPayload,
  FamilyAccessPayload,
  FamilyMember,
  FamilyProfile,
  JoinFamilyPayload,
} from '@/types/api'
import { useAuthStore } from '@/stores/auth'

export const useFamilyStore = defineStore('family', () => {
  const authStore = useAuthStore()
  const currentFamily = ref<FamilyProfile | null>(null)
  const members = ref<FamilyMember[]>([])
  const initialized = ref(false)

  const hasFamily = computed(() => Boolean(currentFamily.value))
  const familyName = computed(() => currentFamily.value?.name ?? '未加入家庭')
  const inviteCode = computed(() => currentFamily.value?.invite_code ?? '')
  const isOwner = computed(() =>
    members.value.some(
      (member) => member.role === 'owner' && member.user_id === authStore.currentUser?.id,
    ),
  )

  function applyFamilyPayload(payload: FamilyAccessPayload) {
    currentFamily.value = payload.family
    members.value = payload.family.members ?? []
  }

  function clearFamily() {
    currentFamily.value = null
    members.value = []
    initialized.value = true
  }

  async function loadCurrentFamily() {
    try {
      currentFamily.value = await fetchCurrentFamily()
      members.value = await fetchCurrentFamilyMembers()
    } catch {
      currentFamily.value = null
      members.value = []
    } finally {
      initialized.value = true
    }
  }

  async function createFamilySpace(payload: CreateFamilyPayload) {
    const response = await createFamily(payload)
    applyFamilyPayload(response)
    initialized.value = true
    return response
  }

  async function joinFamilySpace(payload: JoinFamilyPayload) {
    const response = await joinFamily(payload)
    applyFamilyPayload(response)
    initialized.value = true
    return response
  }

  async function refreshFamilyMembers() {
    if (!currentFamily.value) {
      members.value = []
      return
    }
    members.value = await fetchCurrentFamilyMembers()
  }

  return {
    currentFamily,
    members,
    initialized,
    hasFamily,
    familyName,
    inviteCode,
    isOwner,
    clearFamily,
    loadCurrentFamily,
    createFamilySpace,
    joinFamilySpace,
    refreshFamilyMembers,
  }
})
