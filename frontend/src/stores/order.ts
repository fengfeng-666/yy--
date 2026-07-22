import { ref } from 'vue'
import { defineStore } from 'pinia'

import {
  acceptOrder,
  createMealReview,
  createOrder,
  fetchDiningHistory,
  fetchOrderDetail,
  fetchOrders,
} from '@/api/order'
import type {
  CreateMealOrderPayload,
  CreateMealReviewPayload,
  MealOrder,
  MealOrderRole,
  MealOrderStatus,
} from '@/types/order'

export const useOrderStore = defineStore('order', () => {
  const orders = ref<MealOrder[]>([])
  const historyOrders = ref<MealOrder[]>([])
  const currentOrder = ref<MealOrder | null>(null)
  const loading = ref(false)
  const detailLoading = ref(false)
  const historyLoading = ref(false)

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

  async function loadDiningHistory() {
    historyLoading.value = true
    try {
      historyOrders.value = await fetchDiningHistory()
      return historyOrders.value
    } finally {
      historyLoading.value = false
    }
  }

  async function submitMealReview(orderId: number, payload: CreateMealReviewPayload) {
    const order = await createMealReview(orderId, payload)
    currentOrder.value = order
    orders.value = orders.value.map((item) => (item.id === order.id ? order : item))
    historyOrders.value = historyOrders.value.map((item) => (item.id === order.id ? order : item))
    return order
  }

  return {
    orders,
    historyOrders,
    currentOrder,
    loading,
    detailLoading,
    historyLoading,
    loadOrders,
    loadOrderDetail,
    createOrderItem,
    acceptOrderItem,
    loadDiningHistory,
    submitMealReview,
  }
})
