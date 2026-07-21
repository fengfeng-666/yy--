import { describe, expect, it } from 'vitest'

import { apiBaseUrl } from '@/utils/env'

describe('apiBaseUrl', () => {
  it('提供默认后端地址', () => {
    expect(apiBaseUrl).toBe('http://localhost:8001/api/v1')
  })
})
