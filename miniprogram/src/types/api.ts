export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface UserProfile {
  id: number
  username: string
  nickname: string
  is_active: boolean
  created_at: string
}

export interface AuthPayload {
  user: UserProfile
  tokens: {
    access_token: string
    token_type: string
    expires_at: string
  }
}

export interface FamilyMember {
  id: number
  family_id: number
  user_id: number
  role: 'owner' | 'member'
  joined_at: string
  user: UserProfile
}

export interface FamilyProfile {
  id: number
  name: string
  description: string | null
  invite_code: string
  owner_id: number
  members: FamilyMember[]
}

export interface HomeSummary {
  pending_orders_count: number
  pending_to_me_count: number
  monthly_accepted_orders_count: number
  monthly_top_dish_name: string | null
  review_pending_count: number
  today_order: MealOrder | null
  recent_history: MealOrder[]
}

export interface DishItem {
  id: number
  name: string
  description: string | null
  price: number
  image_url: string | null
  is_available: boolean
}

export interface MealOrder {
  id: number
  requester_id: number
  cook_id: number
  status: 'pending' | 'accepted'
  planned_date: string
  planned_time: string | null
  note: string | null
  requester: UserProfile
  cook: UserProfile
  items: Array<{
    id: number
    dish_id: number
    quantity: number
    dish: { id: number; name: string; image_url: string | null }
  }>
  review: { rating: number; content: string | null } | null
}

export type NotificationEventType = 'new_order' | 'order_accepted'
