import { describe, expect, it } from 'vitest'
import { orderSubmission } from './orderSubmission'

describe('order submission idempotency', () => {
  it('reuses a key for an unchanged failed submission, changes it after edits or success', () => {
    const submission = orderSubmission()
    const first = submission.prepare({ cook_id: 2, items: [{ dish_id: 1, quantity: 1 }] })
    expect(submission.prepare({ cook_id: 2, items: [{ dish_id: 1, quantity: 1 }] }).requestId).toBe(first.requestId)
    const edited = submission.prepare({ cook_id: 2, items: [{ dish_id: 1, quantity: 2 }] })
    expect(edited.requestId).not.toBe(first.requestId)
    submission.complete()
    expect(submission.prepare({ cook_id: 2, items: [{ dish_id: 1, quantity: 2 }] }).requestId).not.toBe(edited.requestId)
  })
})
