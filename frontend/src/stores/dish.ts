import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createDish,
  createDishCategory,
  deleteDish,
  deleteDishCategory,
  fetchDishCategories,
  fetchDishes,
  updateDish,
  updateDishCategory,
  uploadDishImage,
} from '@/api/dish'
import type {
  CreateDishCategoryPayload,
  CreateDishPayload,
  DishCategory,
  DishItem,
  ImageUploadPayload,
  UpdateDishCategoryPayload,
  UpdateDishPayload,
} from '@/types/dish'

export const useDishStore = defineStore('dish', () => {
  const categories = ref<DishCategory[]>([])
  const dishes = ref<DishItem[]>([])
  const initialized = ref(false)
  const loading = ref(false)
  const selectedCategoryId = ref<number | null>(null)

  const hasDishes = computed(() => dishes.value.length > 0)

  async function initialize() {
    if (initialized.value) {
      return
    }
    await Promise.all([loadCategories(), loadDishes()])
    initialized.value = true
  }

  async function loadCategories() {
    categories.value = await fetchDishCategories()
  }

  async function loadDishes(categoryId = selectedCategoryId.value) {
    loading.value = true
    try {
      dishes.value = await fetchDishes(categoryId ?? undefined)
      selectedCategoryId.value = categoryId ?? null
    } finally {
      loading.value = false
    }
  }

  async function reloadAll() {
    await loadCategories()
    await loadDishes(selectedCategoryId.value)
    initialized.value = true
  }

  async function createCategory(payload: CreateDishCategoryPayload) {
    const category = await createDishCategory(payload)
    await reloadAll()
    if (selectedCategoryId.value === null) {
      selectedCategoryId.value = category.id
    }
    return category
  }

  async function editCategory(categoryId: number, payload: UpdateDishCategoryPayload) {
    const category = await updateDishCategory(categoryId, payload)
    await reloadAll()
    return category
  }

  async function removeCategory(categoryId: number) {
    await deleteDishCategory(categoryId)
    if (selectedCategoryId.value === categoryId) {
      selectedCategoryId.value = null
    }
    await reloadAll()
  }

  async function createDishItem(payload: CreateDishPayload) {
    const dish = await createDish(payload)
    await loadDishes(selectedCategoryId.value)
    return dish
  }

  async function updateDishItem(dishId: number, payload: UpdateDishPayload) {
    const dish = await updateDish(dishId, payload)
    await loadDishes(selectedCategoryId.value)
    return dish
  }

  async function removeDishItem(dishId: number) {
    await deleteDish(dishId)
    await loadDishes(selectedCategoryId.value)
  }

  async function uploadImage(file: File): Promise<ImageUploadPayload> {
    return uploadDishImage(file)
  }

  return {
    categories,
    dishes,
    initialized,
    loading,
    selectedCategoryId,
    hasDishes,
    initialize,
    loadCategories,
    loadDishes,
    reloadAll,
    createCategory,
    editCategory,
    removeCategory,
    createDishItem,
    updateDishItem,
    removeDishItem,
    uploadImage,
  }
})
