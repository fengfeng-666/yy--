export interface DishIngredientItem {
  id: number
  dish_id: number
  ingredient_id: number
  quantity: number | null
  unit: string | null
  is_optional: boolean
  note: string | null
  sort_order: number
  ingredient: {
    id: number
    family_id: number
    name: string
    category: string | null
    default_unit: string | null
  }
}

export interface DishStepItem {
  id: number
  dish_id: number
  step_no: number
  content: string
  duration_minutes: number | null
}

export interface DishPreferenceItem {
  id: number
  dish_id: number
  user_id: number
  preference_note: string
  created_at: string
  updated_at: string
}

export interface DishItem {
  id: number
  family_id: number
  name: string
  description: string | null
  price: number
  image_url: string | null
  cooking_minutes: number | null
  difficulty: number | null
  spicy_level: number | null
  need_prepare_ahead: boolean
  suitable_for_weekday: boolean
  is_available: boolean
  ingredients: DishIngredientItem[]
  steps: DishStepItem[]
  preferences: DishPreferenceItem[]
  created_at: string
  updated_at: string
}

export interface CreateDishPayload {
  name: string
  description?: string
  price: number
  image_url?: string
  cooking_minutes?: number
  difficulty?: number
  spicy_level?: number
  need_prepare_ahead?: boolean
  suitable_for_weekday?: boolean
  is_available: boolean
  ingredients?: Array<{
    ingredient_name: string
    quantity?: number
    unit?: string
    is_optional?: boolean
    note?: string
    category?: string
    sort_order?: number
  }>
  steps?: Array<{
    step_no: number
    content: string
    duration_minutes?: number
  }>
  preferences?: Array<{
    user_id: number
    preference_note: string
  }>
}

export interface UpdateDishPayload extends CreateDishPayload {}

export interface ImageUploadPayload {
  path: string
  url: string
}
