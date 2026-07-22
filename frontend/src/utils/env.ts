const DEFAULT_API_BASE_URL = import.meta.env.PROD
  ? '/api/v1'
  : 'http://localhost:8001/api/v1'

export function normalizeApiBaseUrl(value?: string): string {
  const normalized = value?.trim() || DEFAULT_API_BASE_URL
  return normalized.replace(/\/+$/, '')
}

export const apiBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL)
