import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type {
  CreateDishCategoryPayload,
  CreateDishPayload,
  DishCategory,
  DishItem,
  ImageUploadPayload,
  UpdateDishCategoryPayload,
  UpdateDishPayload,
} from '@/types/dish'

export async function fetchDishCategories(): Promise<DishCategory[]> {
  const { data } = await http.get<ApiResponse<DishCategory[]>>('/dish-categories')
  return data.data
}

export async function createDishCategory(payload: CreateDishCategoryPayload): Promise<DishCategory> {
  const { data } = await http.post<ApiResponse<DishCategory>>('/dish-categories', payload)
  return data.data
}

export async function updateDishCategory(
  categoryId: number,
  payload: UpdateDishCategoryPayload,
): Promise<DishCategory> {
  const { data } = await http.patch<ApiResponse<DishCategory>>(
    `/dish-categories/${categoryId}`,
    payload,
  )
  return data.data
}

export async function deleteDishCategory(categoryId: number): Promise<void> {
  await http.delete<ApiResponse<null>>(`/dish-categories/${categoryId}`)
}

export async function fetchDishes(categoryId?: number): Promise<DishItem[]> {
  const { data } = await http.get<ApiResponse<DishItem[]>>('/dishes', {
    params: categoryId ? { category_id: categoryId } : undefined,
  })
  return data.data
}

export async function fetchDishDetail(dishId: number): Promise<DishItem> {
  const { data } = await http.get<ApiResponse<DishItem>>(`/dishes/${dishId}`)
  return data.data
}

export async function createDish(payload: CreateDishPayload): Promise<DishItem> {
  const { data } = await http.post<ApiResponse<DishItem>>('/dishes', payload)
  return data.data
}

export async function updateDish(dishId: number, payload: UpdateDishPayload): Promise<DishItem> {
  const { data } = await http.patch<ApiResponse<DishItem>>(`/dishes/${dishId}`, payload)
  return data.data
}

export async function deleteDish(dishId: number): Promise<void> {
  await http.delete<ApiResponse<null>>(`/dishes/${dishId}`)
}

export async function uploadDishImage(file: File): Promise<ImageUploadPayload> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post<ApiResponse<ImageUploadPayload>>('/uploads/images', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data.data
}
