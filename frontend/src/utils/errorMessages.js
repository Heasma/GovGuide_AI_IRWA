/**
 * GovGuide AI — Citizen-Friendly Error Message Utility
 *
 * Maps Axios/API errors to safe, citizen-readable messages.
 * NEVER exposes: stack traces, JWT tokens, API keys, database errors,
 * raw Python/OpenAI exceptions, or internal error codes.
 */

const CITIZEN_MESSAGES = {
  // HTTP status codes
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'GovGuide AI encountered an unexpected error. Please try again shortly.',
  502: 'GovGuide AI is temporarily unavailable. Please try again shortly.',
  503: 'GovGuide AI is temporarily unavailable. Please try again shortly.',
  504: 'GovGuide AI is taking too long to respond. Please try again.',

  // Known backend error codes in response detail
  LLM_PROVIDER_ERROR: 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.',
  LLM_TIMEOUT: 'GovGuide AI took too long to respond. Please try again.',
  RETRIEVAL_ERROR: 'There was a problem searching for information. Please try again.',
  RATE_LIMIT_EXCEEDED: 'Too many requests. Please wait a moment and try again.',
  CONTEXT_TOO_LONG: 'Your question is too long. Please shorten it and try again.',
  QUERY_TOO_SHORT: 'Please provide a more detailed question.',

  // Default fallback
  DEFAULT: 'An error occurred. Please try again.',
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
