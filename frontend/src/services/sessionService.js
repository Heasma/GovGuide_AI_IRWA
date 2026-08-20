/**
 * GovGuide AI — Session / Conversation API Service
 *
 * Wraps /api/v1/sessions endpoints.
 * Uses the existing configured api instance from apiClient.js.
 */

import { api } from './apiClient'

export const sessionService = {
  /**
   * List all conversation sessions for the authenticated user.
   * Ordered newest-first by the backend.
   * @returns {Promise<Array<{session_id, started_at, message_count}>>}
   */
  listSessions: async () => {
    const { data } = await api.get('/sessions')
    return data
  },

  /**
   * Retrieve all messages in a specific session.
   * Validates session ownership server-side.
   * @param {string} sessionId - UUID of the session
   * @returns {Promise<Array<{message_id, role, content, confidence_score, sources, created_at}>>}
   */
  getSessionMessages: async (sessionId) => {
    const { data } = await api.get(`/sessions/${sessionId}/messages`)
    return data
  },

  /**
   * Delete a session owned by the current user.
   * @param {string} sessionId - UUID of the session
   * @returns {Promise<{message: string}>}
   */
  deleteSession: async (sessionId) => {
    const { data } = await api.delete(`/sessions/${sessionId}`)
    return data
  },
}
