import { grantSubscriptions } from '@/api'
import type { NotificationEventType } from '@/types/api'

const templateIds: Record<NotificationEventType, string> = {
  new_order: import.meta.env.VITE_WECHAT_TEMPLATE_NEW_ORDER || '',
  order_accepted: import.meta.env.VITE_WECHAT_TEMPLATE_ORDER_ACCEPTED || '',
}

export async function requestSubscriptions(eventTypes: NotificationEventType[]) {
  const configured = eventTypes.filter((eventType) => templateIds[eventType])
  if (!configured.length) {
    throw new Error('消息模板尚未配置')
  }

  const result = await new Promise<Record<string, string>>((resolve, reject) => {
    uni.requestSubscribeMessage({
      tmplIds: configured.map((eventType) => templateIds[eventType]),
      success: (response) => resolve(response as unknown as Record<string, string>),
      fail: reject,
    })
  })
  const accepted = configured.filter((eventType) => result[templateIds[eventType]] === 'accept')
  if (accepted.length) {
    await grantSubscriptions(accepted)
  }
  return accepted
}
