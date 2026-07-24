export type ShoppingListStatus = 'active' | 'completed'
export type ShoppingListSourceType = 'ai_agent' | 'manual'

export interface ShoppingListItem {
  id: number
  shopping_list_id: number
  ingredient_id: number | null
  name: string
  quantity: number | null
  unit: string | null
  note: string | null
  source_dish_name: string | null
  is_purchased: boolean
  sort_order: number
}

export interface ShoppingList {
  id: number
  family_id: number
  name: string
  status: ShoppingListStatus
  source_type: ShoppingListSourceType
  source_reference: string | null
  created_at: string
  updated_at: string
  items: ShoppingListItem[]
}
