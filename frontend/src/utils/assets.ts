import { apiBaseUrl } from '@/utils/env'

const backendOrigin = apiBaseUrl.replace(/\/api\/v1\/?$/, '')

export function resolveAssetUrl(url?: string | null): string {
  if (!url) {
    return ''
  }
  if (/^https?:\/\//i.test(url)) {
    return url
  }
  return `${backendOrigin}${url.startsWith('/') ? url : `/${url}`}`
}
