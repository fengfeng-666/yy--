import type { UserProfile } from '@/types/api'

export interface ChatMessage {
  id: number
  family_id: number
  sender_id: number
  content: string
  created_at: string
  sender: UserProfile
}

export interface ChatMessagePage {
  items: ChatMessage[]
  has_more: boolean
}

export interface ChatUnreadCount {
  unread_count: number
}
