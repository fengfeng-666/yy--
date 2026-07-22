import type { UserProfile } from '@/types/api'

export type MealOrderStatus = 'pending' | 'accepted'
export type MealOrderRole = 'my_requested' | 'to_me'

export interface DishBrief {
  id: number
  name: string
  image_url: string | null
}

export interface MealOrderItem {
  id: number
  meal_order_id: number
  dish_id: number
  quantity: number
  note: string | null
  sort_order: number
  dish: DishBrief
}

export interface OrderStatusLog {
  id: number
  meal_order_id: number
  from_status: MealOrderStatus | null
  to_status: MealOrderStatus
  operator_id: number
  note: string | null
  created_at: string
  operator: UserProfile
}

export interface MealOrder {
  id: number
  family_id: number
  requester_id: number
  cook_id: number
  status: MealOrderStatus
  planned_date: string
  planned_time: string | null
  note: string | null
  accepted_at: string | null
  created_at: string
  updated_at: string
  requester: UserProfile
  cook: UserProfile
  items: MealOrderItem[]
  status_logs: OrderStatusLog[]
}

export interface CreateMealOrderItemPayload {
  dish_id: number
  quantity: number
  note?: string
  sort_order?: number
}

export interface CreateMealOrderPayload {
  cook_id: number
  planned_date: string
  planned_time?: string
  note?: string
  items: CreateMealOrderItemPayload[]
}
