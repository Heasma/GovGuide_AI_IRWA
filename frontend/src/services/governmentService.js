/**
 * GovGuide AI — Government Service API Service
 *
 * Wraps all /api/v1/services and /api/v1/sources endpoints.
 * Uses the existing configured api instance from apiClient.js.
 * Never duplicates Axios configuration.
 */

import { api } from './apiClient'

export const governmentService = {
  /**
   * Fetch a paginated list of government services.
   * @param {number} skip - Offset for pagination
   * @param {number} limit - Page size (max 100)
   * @param {string|null} category - Optional category filter
   * @returns {Promise<{total: number, items: Array}>}
   */
  listServices: async (skip = 0, limit = 24, category = null) => {
    const params = { skip, limit }
    if (category && category !== 'All') params.category = category
    const { data } = await api.get('/services', { params })
    return data
  },

  /**
   * Fetch distinct service categories from the database.
   * @returns {Promise<{total: number, categories: string[]}>}
   */
  getCategories: async () => {
    const { data } = await api.get('/services/categories')
    return data
  },

  /**
   * Search services by keyword against the real backend.
   * @param {string} query - Search term
   * @param {number} skip - Pagination offset
   * @param {number} limit - Page size
   * @returns {Promise<{query: string, total: number, items: Array}>}
   */
  searchServices: async (query = '', skip = 0, limit = 24) => {
    const { data } = await api.get('/services/search', {
      params: { query, skip, limit },
    })
    return data
  },

  /**
   * Fetch full detail for a single service by UUID.
   * @param {string} id - Service UUID
   * @returns {Promise<Object>}
   */
  getService: async (id) => {
    const { data } = await api.get(`/services/${id}`)
    return data
  },

  /**
   * Fetch system health status.
   * @returns {Promise<{status: string, version: string, environment: string, database: string, agents: Object}>}
   */
  getHealth: async () => {
    const { data } = await api.get('/health')
    return data
  },

  /**
   * Fetch paginated official knowledge sources.
   * Returns total=0 and items=[] when the RAG pipeline has not yet been populated.
   * @param {number} skip
   * @param {number} limit
   * @returns {Promise<{total: number, items: Array}>}
   */
  listSources: async (skip = 0, limit = 50) => {
    const { data } = await api.get('/sources', { params: { skip, limit } })
    return data
  },
}
