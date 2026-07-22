import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type {
  CreateMealOrderPayload,
  CreateMealReviewPayload,
  MealOrder,
  MealOrderRole,
  MealOrderStatus,
} from '@/types/order'

export async function fetchOrders(params?: {
  role?: MealOrderRole
  status?: MealOrderStatus
}): Promise<MealOrder[]> {
  const { data } = await http.get<ApiResponse<MealOrder[]>>('/orders', { params })
  return data.data
}

export async function createOrder(payload: CreateMealOrderPayload): Promise<MealOrder> {
  const { data } = await http.post<ApiResponse<MealOrder>>('/orders', payload)
  return data.data
}

export async function fetchOrderDetail(orderId: number): Promise<MealOrder> {
  const { data } = await http.get<ApiResponse<MealOrder>>(`/orders/${orderId}`)
  return data.data
}

export async function acceptOrder(orderId: number): Promise<MealOrder> {
  const { data } = await http.post<ApiResponse<MealOrder>>(`/orders/${orderId}/accept`)
  return data.data
}

export async function fetchDiningHistory(): Promise<MealOrder[]> {
  const { data } = await http.get<ApiResponse<MealOrder[]>>('/orders/history')
  return data.data
}

export async function createMealReview(
  orderId: number,
  payload: CreateMealReviewPayload,
): Promise<MealOrder> {
  const { data } = await http.post<ApiResponse<MealOrder>>(`/orders/${orderId}/review`, payload)
  return data.data
}
