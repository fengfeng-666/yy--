import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createDish,
  deleteDish,
  fetchDishes,
  updateDish,
  uploadDishImage,
} from '@/api/dish'
import type {
  CreateDishPayload,
  DishItem,
  ImageUploadPayload,
  UpdateDishPayload,
} from '@/types/dish'

export const useDishStore = defineStore('dish', () => {
  const dishes = ref<DishItem[]>([])
  const initialized = ref(false)
  const loading = ref(false)

  const hasDishes = computed(() => dishes.value.length > 0)

  async function initialize() {
    if (initialized.value) {
      return
    }
    await loadDishes()
    initialized.value = true
  }

  async function loadDishes() {
    loading.value = true
    try {
      dishes.value = await fetchDishes()
    } finally {
      loading.value = false
    }
  }

  async function reloadAll() {
    await loadDishes()
    initialized.value = true
  }

  async function createDishItem(payload: CreateDishPayload) {
    const dish = await createDish(payload)
    await loadDishes()
    return dish
  }

  async function updateDishItem(dishId: number, payload: UpdateDishPayload) {
    const dish = await updateDish(dishId, payload)
    await loadDishes()
    return dish
  }

  async function removeDishItem(dishId: number) {
    await deleteDish(dishId)
    await loadDishes()
  }

  async function uploadImage(file: File): Promise<ImageUploadPayload> {
    return uploadDishImage(file)
  }

  return {
    dishes,
    initialized,
    loading,
    hasDishes,
    initialize,
    loadDishes,
    reloadAll,
    createDishItem,
    updateDishItem,
    removeDishItem,
    uploadImage,
  }
})
