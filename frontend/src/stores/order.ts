import { ref } from 'vue'
import { defineStore } from 'pinia'

import { acceptOrder, createOrder, fetchOrderDetail, fetchOrders } from '@/api/order'
import type { CreateMealOrderPayload, MealOrder, MealOrderRole, MealOrderStatus } from '@/types/order'

export const useOrderStore = defineStore('order', () => {
  const orders = ref<MealOrder[]>([])
  const currentOrder = ref<MealOrder | null>(null)
  const loading = ref(false)
  const detailLoading = ref(false)

  async function loadOrders(filters?: { role?: MealOrderRole; status?: MealOrderStatus }) {
    loading.value = true
    try {
      orders.value = await fetchOrders(filters)
    } finally {
      loading.value = false
    }
  }

  async function loadOrderDetail(orderId: number) {
    detailLoading.value = true
    try {
      currentOrder.value = await fetchOrderDetail(orderId)
      return currentOrder.value
    } finally {
      detailLoading.value = false
    }
  }

  async function createOrderItem(payload: CreateMealOrderPayload) {
    const order = await createOrder(payload)
    currentOrder.value = order
    return order
  }

  async function acceptOrderItem(orderId: number) {
    const order = await acceptOrder(orderId)
    currentOrder.value = order
    orders.value = orders.value.map((item) => (item.id === order.id ? order : item))
    return order
  }

  return {
    orders,
    currentOrder,
    loading,
    detailLoading,
    loadOrders,
    loadOrderDetail,
    createOrderItem,
    acceptOrderItem,
  }
})
