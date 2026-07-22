export interface DishItem {
  id: number
  family_id: number
  name: string
  description: string | null
  price: number
  image_url: string | null
  is_available: boolean
  created_at: string
  updated_at: string
}

export interface CreateDishPayload {
  name: string
  description?: string
  price: number
  image_url?: string
  is_available: boolean
}

export interface UpdateDishPayload extends CreateDishPayload {}

export interface ImageUploadPayload {
  path: string
  url: string
}
