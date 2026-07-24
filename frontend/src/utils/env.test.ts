import { describe, expect, it } from 'vitest'

import { apiBaseUrl, normalizeApiBaseUrl } from '@/utils/env'

describe('前端环境配置', () => {
  it('未配置时使用同源 API 地址', () => {
    expect(normalizeApiBaseUrl()).toBe('/api/v1')
    expect(apiBaseUrl).toBe('/api/v1')
  })

  it('支持生产环境同源 API 地址', () => {
    expect(normalizeApiBaseUrl('/api/v1/')).toBe('/api/v1')
  })

  it('清理配置两端的空白和末尾斜杠', () => {
    expect(normalizeApiBaseUrl(' https://api.example.com/api/v1/// ')).toBe(
      'https://api.example.com/api/v1',
    )
  })
})
