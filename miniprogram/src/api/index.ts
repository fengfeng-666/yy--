import type {
  AuthPayload,
  DishItem,
  FamilyProfile,
  HomeSummary,
  MealOrder,
  NotificationEventType,
} from '@/types/api'
import { request } from '@/utils/request'

export function wechatLogin(code: string, nickname?: string) {
  return request<AuthPayload>({
    url: '/auth/wechat/login',
    method: 'POST',
    data: { code, nickname },
  })
}

export function fetchCurrentFamily() {
  return request<FamilyProfile>({ url: '/families/current' })
}

export function fetchFamilyMembers() {
  return request<FamilyProfile['members']>({ url: '/families/current/members' })
}

export function createFamily(name: string, description?: string) {
  return request<{ family: FamilyProfile }>({
    url: '/families',
    method: 'POST',
    data: { name, description },
  })
}

export function joinFamily(inviteCode: string) {
  return request<{ family: FamilyProfile }>({
    url: '/families/join',
    method: 'POST',
    data: { invite_code: inviteCode },
  })
}

export function fetchHomeSummary() {
  return request<HomeSummary>({ url: '/home/summary' })
}

export function fetchDishes() {
  return request<DishItem[]>({ url: '/dishes' })
}

export function fetchOrders(role: 'to_me' | 'my_requested', status: 'pending' | 'accepted') {
  return request<MealOrder[]>({ url: `/orders?role=${role}&status=${status}` })
}

export function createOrder(payload: {
  requestId?: string
  cook_id: number
  planned_date: string
  planned_time?: string
  note?: string
  items: Array<{ dish_id: number; quantity: number }>
}) {
  return request<MealOrder>({ url: '/orders', method: 'POST', data: payload })
}

export function acceptOrder(orderId: number) {
  return request<MealOrder>({ url: `/orders/${orderId}/accept`, method: 'POST' })
}

export function grantSubscriptions(eventTypes: NotificationEventType[]) {
  return request<Array<{ event_type: NotificationEventType; available_count: number }>>({
    url: '/notifications/subscriptions/grant',
    method: 'POST',
    data: { event_types: eventTypes },
  })
}
