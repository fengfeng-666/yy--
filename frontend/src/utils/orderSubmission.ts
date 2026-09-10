/** One key per logical submission. Keep it after errors; reset only after success. */
export function orderSubmission() {
  let signature = ''
  let requestId = ''
  return {
    prepare<T extends object>(payload: T): T & { requestId: string } {
      const next = JSON.stringify(payload)
      if (next !== signature || !requestId) {
        signature = next
        requestId = globalThis.crypto?.randomUUID?.() ?? 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
          const value = Math.floor(Math.random() * 16)
          return (c === 'x' ? value : (value & 3) | 8).toString(16)
        })
      }
      return { ...payload, requestId }
    },
    complete() { signature = ''; requestId = '' },
  }
}
