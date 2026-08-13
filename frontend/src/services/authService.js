import { api } from './apiClient'

export const authService = {
  login: async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    return data
  },
  register: async (email, password) => {
    const { data } = await api.post('/auth/register', { email, password })
    return data
  },
  getProfile: async () => {
    const { data } = await api.get('/auth/me')
    return data
  },
  logout: async () => {
    try { await api.post('/auth/logout') } catch {}
  },
}

export const queryService = {
  submitQuery: async (query, sessionId) => {
    const { data } = await api.post('/query', { query, session_id: sessionId })
    return data
  },
  submitFeedback: async (requestId, rating, comment) => {
    const { data } = await api.post(`/query/${requestId}/feedback`, { rating, comment })
    return data
  },
}
