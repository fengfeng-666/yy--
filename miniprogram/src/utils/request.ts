import type { ApiResponse } from '@/types/api'
import { clearSession } from '@/stores/session'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1').replace(
  /\/+$/,
  '',
)

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly code?: number,
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

export function resolveAssetUrl(path?: string | null): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  const origin = API_BASE_URL.replace(/\/api\/v1$/, '')
  return `${origin}${path.startsWith('/') ? path : `/${path}`}`
}

export function request<T>(options: {
  url: string
  method?: UniApp.RequestOptions['method']
  data?: unknown
}): Promise<T> {
  const token = uni.getStorageSync('yy-kitchen-access-token')
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method ?? 'GET',
      data: options.data as UniApp.RequestOptions['data'],
      header: token ? { Authorization: `Bearer ${token}` } : {},
      timeout: 12000,
      success(response) {
        const body = response.data as ApiResponse<T>
        if (response.statusCode >= 200 && response.statusCode < 300 && body?.code === 0) {
          resolve(body.data)
          return
        }
        if (response.statusCode === 401) {
          clearSession()
          uni.reLaunch({ url: '/pages/login/index' })
        }
        reject(
          new ApiRequestError(
            body?.message || `请求失败（${response.statusCode}）`,
            response.statusCode,
            body?.code,
          ),
        )
      },
      fail(error) {
        reject(new Error(error.errMsg || '网络连接失败'))
      },
    })
  })
}

export function showError(error: unknown, fallback = '操作失败') {
  uni.showToast({
    title: error instanceof Error ? error.message : fallback,
    icon: 'none',
  })
}
