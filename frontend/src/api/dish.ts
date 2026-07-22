import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type {
  CreateDishPayload,
  DishItem,
  ImageUploadPayload,
  UpdateDishPayload,
} from '@/types/dish'

export async function fetchDishes(): Promise<DishItem[]> {
  const { data } = await http.get<ApiResponse<DishItem[]>>('/dishes')
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
