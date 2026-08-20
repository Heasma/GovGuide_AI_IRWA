/**
 * GovGuide AI — Citizen-Friendly Error Message Utility
 *
 * Maps Axios/API errors and provider failure payloads to safe, citizen-readable messages.
 * NEVER exposes: stack traces, JWT tokens, API keys, database errors,
 * raw Python/OpenAI exceptions, internal error codes, or [LLM_PROVIDER_ERROR] strings.
 */

const CITIZEN_MESSAGES = {
  // HTTP status codes
  422: 'Please enter a question to get assistance.',
  429: 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.',
  500: 'GovGuide AI is temporarily unavailable. Please try again later.',
  502: 'GovGuide AI is temporarily unavailable. Please try again later.',
  503: 'GovGuide AI is temporarily unavailable. Please try again later.',
  504: 'GovGuide AI took too long to respond. Please try again.',

  // Known backend error codes in response detail
  LLM_PROVIDER_ERROR: 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.',
  LLM_PROVIDER_ERROR_RATELIMIT: 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.',
  LLM_PROVIDER_ERROR_AUTH: 'GovGuide AI is temporarily unavailable. Please try again later.',
  LLM_PROVIDER_ERROR_TIMEOUT: 'GovGuide AI took too long to respond. Please try again.',
  LLM_PROVIDER_ERROR_NETWORK: 'Unable to connect to the AI service. Please try again.',
  LLM_TIMEOUT: 'GovGuide AI took too long to respond. Please try again.',
  RETRIEVAL_ERROR: 'There was a problem searching for information. Please try again.',
  RATE_LIMIT_EXCEEDED: 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.',
  CONTEXT_TOO_LONG: 'Your question is too long. Please shorten it and try again.',
  QUERY_TOO_SHORT: 'Please provide a more detailed question.',

  // Default fallback
  DEFAULT: 'An error occurred. Please try again.',
}

/**
 * Detects whether a backend query response indicates a provider/LLM/pipeline failure.
 *
 * @param {Object} result - The QueryResponse object returned by POST /api/v1/query.
 * @returns {boolean} True if the response represents an error rather than a valid answer.
 */
export function isProviderErrorResponse(result) {
  if (!result || typeof result !== 'object') return true
  const answer = typeof result.answer === 'string' ? result.answer.trim() : ''
  if (!answer) return true

  // Check for LLM provider error markers
  if (
    answer.includes('LLM_PROVIDER_ERROR') ||
    answer.includes('[LLM_PROVIDER_ERROR]') ||
    answer.includes('RATE_LIMIT_EXCEEDED') ||
    answer.includes('Rate limit exceeded on LLM provider') ||
    answer.includes('Authentication failure with the configured LLM provider') ||
    answer.includes('LLM provider error:') ||
    answer.includes('Unexpected error during LLM generation:') ||
    answer.startsWith('[ERROR]')
  ) {
    return true
  }

  return false
}

/**
 * Converts an Axios error or any error object into a citizen-friendly string.
 *
 * @param {unknown} err - The error thrown by an API call.
 * @returns {string} A safe, citizen-readable error message.
 */
export function getCitizenErrorMessage(err) {
  // Network error (no response from server)
  if (err && !err.response && err.request) {
    return 'Unable to connect. Please check your connection and try again.'
  }

  const status = err?.response?.status
  const detail = err?.response?.data?.detail

  // Check HTTP status first
  if (status && CITIZEN_MESSAGES[status]) {
    return CITIZEN_MESSAGES[status]
  }

  // Check for known backend error codes in the detail string
  if (typeof detail === 'string') {
    for (const code of Object.keys(CITIZEN_MESSAGES)) {
      if (detail.includes(code)) {
        return CITIZEN_MESSAGES[code]
      }
    }
  }

  // Check for known backend error codes in a structured detail object
  if (detail && typeof detail === 'object' && detail.error_code) {
    const code = detail.error_code
    if (CITIZEN_MESSAGES[code]) return CITIZEN_MESSAGES[code]
  }

  return CITIZEN_MESSAGES.DEFAULT
}
