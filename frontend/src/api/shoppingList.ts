import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type { ShoppingList } from '@/types/shoppingList'

export async function fetchShoppingLists(): Promise<ShoppingList[]> {
  const { data } = await http.get<ApiResponse<ShoppingList[]>>('/shopping-lists')
  return data.data
}
