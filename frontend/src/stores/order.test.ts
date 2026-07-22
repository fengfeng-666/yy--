import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  acceptOrder,
  createMealReview,
  createOrder,
  fetchDiningHistory,
  fetchOrderDetail,
  fetchOrders,
} from '@/api/order'
import { useOrderStore } from '@/stores/order'
import { makeOrder, makeUser } from '@/test/factories'

vi.mock('@/api/order', () => ({
  acceptOrder: vi.fn(),
  createMealReview: vi.fn(),
  createOrder: vi.fn(),
  fetchDiningHistory: vi.fn(),
  fetchOrderDetail: vi.fn(),
  fetchOrders: vi.fn(),
}))

describe('点菜状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('按角色和状态加载订单', async () => {
    const order = makeOrder()
    vi.mocked(fetchOrders).mockResolvedValue([order])
    const store = useOrderStore()

    await store.loadOrders({ role: 'to_me', status: 'pending' })

    expect(fetchOrders).toHaveBeenCalledWith({ role: 'to_me', status: 'pending' })
    expect(store.orders).toEqual([order])
    expect(store.loading).toBe(false)
  })

  it('接受点菜后同步列表和当前详情', async () => {
    const pendingOrder = makeOrder()
    const acceptedOrder = makeOrder({ status: 'accepted', accepted_at: '2026-07-22T01:00:00Z' })
    vi.mocked(acceptOrder).mockResolvedValue(acceptedOrder)
    const store = useOrderStore()
    store.orders = [pendingOrder]

    await store.acceptOrderItem(pendingOrder.id)

    expect(store.currentOrder).toEqual(acceptedOrder)
    expect(store.orders[0].status).toBe('accepted')
  })

  it('提交评价后同步详情、订单列表和历史记录', async () => {
    const order = makeOrder()
    const reviewedOrder = makeOrder({
      review: {
        id: 1,
        meal_order_id: 1,
        reviewer_id: 1,
        rating: 5,
        content: '很好吃',
        created_at: '2026-07-22T02:00:00Z',
        updated_at: '2026-07-22T02:00:00Z',
        reviewer: makeUser(),
      },
    })
    vi.mocked(createMealReview).mockResolvedValue(reviewedOrder)
    const store = useOrderStore()
    store.orders = [order]
    store.historyOrders = [order]

    await store.submitMealReview(order.id, { rating: 5, content: '很好吃' })

    expect(store.currentOrder?.review?.rating).toBe(5)
    expect(store.orders[0].review?.content).toBe('很好吃')
    expect(store.historyOrders[0].review?.rating).toBe(5)
  })

  it('创建订单后写入当前详情', async () => {
    const order = makeOrder()
    vi.mocked(createOrder).mockResolvedValue(order)
    const store = useOrderStore()

    await store.createOrderItem({
      cook_id: 2,
      planned_date: '2026-07-22',
      items: [{ dish_id: 1, quantity: 1 }],
    })

    expect(store.currentOrder).toEqual(order)
  })

  it('分别加载订单详情和用餐历史', async () => {
    const order = makeOrder()
    vi.mocked(fetchOrderDetail).mockResolvedValue(order)
    vi.mocked(fetchDiningHistory).mockResolvedValue([order])
    const store = useOrderStore()

    await store.loadOrderDetail(order.id)
    await store.loadDiningHistory()

    expect(store.currentOrder).toEqual(order)
    expect(store.historyOrders).toEqual([order])
    expect(store.detailLoading).toBe(false)
    expect(store.historyLoading).toBe(false)
  })
})
