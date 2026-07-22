import type { MealOrder } from '@/types/order'

export interface HomeSummary {
  pending_orders_count: number
  pending_to_me_count: number
  review_pending_count: number
  monthly_accepted_orders_count: number
  monthly_top_dish_name: string | null
  monthly_top_dish_count: number
  today_order: MealOrder | null
  recent_history: MealOrder[]
}
