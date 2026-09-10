import { expect, it } from 'vitest'
import { orderSubmission } from '../src/utils/orderSubmission'

it('retains the submission key across retries and changes it after a successful order', () => {
  const submission = orderSubmission()
  const first = submission.prepare({ cook_id: 2 })
  expect(submission.prepare({ cook_id: 2 }).requestId).toBe(first.requestId)
  expect(submission.prepare({ cook_id: 3 }).requestId).not.toBe(first.requestId)
  submission.complete()
  expect(submission.prepare({ cook_id: 2 }).requestId).not.toBe(first.requestId)
})
