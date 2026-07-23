import { beforeEach, describe, expect, it, vi } from 'vitest'


const grantSubscriptions = vi.fn()
vi.mock('../src/api', () => ({ grantSubscriptions }))

describe('requestSubscriptions', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    vi.stubEnv('VITE_WECHAT_TEMPLATE_NEW_ORDER', 'template-new-order')
    vi.stubEnv('VITE_WECHAT_TEMPLATE_ORDER_ACCEPTED', 'template-order-accepted')
  })

  it('only records subscriptions accepted by the user', async () => {
    vi.stubGlobal('uni', {
      requestSubscribeMessage: vi.fn((options) => {
        options.success({
          'template-new-order': 'accept',
          'template-order-accepted': 'reject',
        })
      }),
    })
    const { requestSubscriptions } = await import('../src/utils/subscriptions')

    await expect(requestSubscriptions(['new_order', 'order_accepted'])).resolves.toEqual([
      'new_order',
    ])
    expect(grantSubscriptions).toHaveBeenCalledWith(['new_order'])
  })
})
