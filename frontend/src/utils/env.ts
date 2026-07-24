// 始终使用同源地址。开发环境由 Vite 代理到后端，这样从局域网、容器或
// 移动设备打开页面时，不会错误地请求访问者自己的 localhost。
const DEFAULT_API_BASE_URL = '/api/v1'

export function normalizeApiBaseUrl(value?: string): string {
  const normalized = value?.trim() || DEFAULT_API_BASE_URL
  return normalized.replace(/\/+$/, '')
}

export const apiBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL)
