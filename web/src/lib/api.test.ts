import { describe, it, expect } from 'vitest'
import api from './api'

describe('api', () => {
  it('has base url', () => {
    expect(api.defaults.baseURL).toBe('/api')
  })
})
