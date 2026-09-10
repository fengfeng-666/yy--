/** Retain the key for network retries, replace it when the order contents change. */
export function orderSubmission() {
  let signature = ''
  let requestId = ''
  return {
    prepare<T extends object>(payload: T): T & { requestId: string } {
      const next = JSON.stringify(payload)
      if (next !== signature || !requestId) {
        signature = next
        requestId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
          const value = Math.floor(Math.random() * 16)
          return (c === 'x' ? value : (value & 3) | 8).toString(16)
        })
      }
      return { ...payload, requestId }
    },
    complete() { signature = ''; requestId = '' },
  }
}
