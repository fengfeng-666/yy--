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

export interface AiRetrievalSource {
  source_type: string
  title: string
  snippet: string
  source_id?: string | null
  score?: number | null
}

export interface AiToolCallTrace {
  tool_name: string
  status: string
  summary: string
}

export interface AiActionDraftItem {
  name: string
  quantity?: number | null
  unit?: string | null
  note?: string | null
  source_dish_name?: string | null
}

export interface AiActionDraft {
  action_type: string
  title: string
  summary?: string | null
  status: 'pending' | 'confirmed' | 'cancelled' | string
  items: AiActionDraftItem[]
  shopping_list_id?: number | null
}

export interface AiChatMetadata {
  summary?: string | null
  recognized_ingredients: string[]
  recommendations: AiRecommendationItem[]
  fridge_image?: FridgeImageAnalysis | null
  retrieval_sources: AiRetrievalSource[]
  tool_calls: AiToolCallTrace[]
  action_draft?: AiActionDraft | null
  confirmation_required?: boolean
  confidence?: number | null
  raw_model_output?: string | null
}

export interface AiChatMessage {
  id: number
  family_id: number
  user_id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  message_kind: 'text' | 'fridge_image' | 'recommendation' | 'tool_result' | 'plan' | 'draft_action'
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

export interface ConfirmAiActionResponse {
  message: AiChatMessage
}
