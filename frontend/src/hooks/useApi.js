/**
 * GovGuide AI — useApi Custom Hook
 *
 * Generic data-fetching hook providing loading, error, and data states.
 * Triggers on mount and whenever `deps` change.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useApi(
 *     () => governmentService.listServices(0, 24),
 *     []
 *   )
 */

import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * @param {Function} apiFn - Async function returning data
 * @param {Array}    deps  - Dependency array (like useEffect)
 * @param {boolean}  skip  - When true, API call is not made (e.g. waiting for input)
 */
export function useApi(apiFn, deps = [], { skip = false } = {}) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(!skip)
  const [error, setError]     = useState(null)
  const mountedRef             = useRef(true)

  const execute = useCallback(async () => {
    if (skip) return
    setLoading(true)
    setError(null)
    try {
      const result = await apiFn()
      if (mountedRef.current) setData(result)
    } catch (err) {
      if (mountedRef.current) {
        const status = err?.response?.status
        if (status === 401) {
          setError('Your session has expired. Please log in again.')
        } else if (status === 429) {
          setError('Too many requests. Please wait a moment and try again.')
        } else if (status >= 500) {
          setError('A server error occurred. Please try again later.')
        } else if (!err.response && err.request) {
          setError('Unable to connect. Please check your internet connection.')
        } else {
          setError('An error occurred. Please try again.')
        }
      }
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [skip, ...deps])

  useEffect(() => {
    mountedRef.current = true
    execute()
    return () => { mountedRef.current = false }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execute])

  return { data, loading, error, refetch: execute }
}
