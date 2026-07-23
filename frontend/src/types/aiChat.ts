export interface AiRecommendationItem {
  dish_name: string
  rating: number
  required_ingredients: string[]
  matched_ingredients: string[]
  steps: string[]
  reason: string
}

export interface FridgeImageAnalysis {
  image_url: string
  recognized_ingredients: string[]
}

export interface AiChatMetadata {
  summary?: string | null
  recognized_ingredients: string[]
  recommendations: AiRecommendationItem[]
  fridge_image?: FridgeImageAnalysis | null
  raw_model_output?: string | null
}

export interface AiChatMessage {
  id: number
  family_id: number
  user_id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  message_kind: 'text' | 'fridge_image' | 'recommendation'
  metadata_json?: AiChatMetadata | null
  created_at: string
}

export interface AiChatConversation {
  id: number
  family_id: number
  user_id: number
  title: string
  last_message_preview?: string | null
  last_message_at?: string | null
  created_at: string
  updated_at: string
}

export interface AiChatConversationPage {
  items: AiChatConversation[]
}

export interface AiChatMessagePage {
  items: AiChatMessage[]
  has_more: boolean
}

export interface AiChatTurnResponse {
  conversation: AiChatConversation
  user_message: AiChatMessage
  assistant_message: AiChatMessage
}
