import { createContext, useContext, useState, useCallback } from 'react'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('govguide_user')
      return stored ? JSON.parse(stored) : null
    } catch { return null }
  })

  const login = useCallback(async (email, password) => {
    const data = await authService.login(email, password)
    localStorage.setItem('govguide_access_token', data.access_token)
    localStorage.setItem('govguide_refresh_token', data.refresh_token)
    const profile = await authService.getProfile()
    localStorage.setItem('govguide_user', JSON.stringify(profile))
    setUser(profile)
    return profile
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('govguide_access_token')
    localStorage.removeItem('govguide_refresh_token')
    localStorage.removeItem('govguide_user')
    setUser(null)
  }, [])

  const isAuthenticated = !!user

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
