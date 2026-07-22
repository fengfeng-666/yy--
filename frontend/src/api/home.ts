import http from '@/api/http'
import type { ApiResponse } from '@/types/api'
import type { HomeSummary } from '@/types/home'

export async function fetchHomeSummary(): Promise<HomeSummary> {
  const { data } = await http.get<ApiResponse<HomeSummary>>('/home/summary')
  return data.data
}
