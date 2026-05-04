import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { type MeResponse, getMe } from '@/api/auth'
import { clearToken } from '@/api/client'
import { resetSessionLanguage } from '@/store/language'

interface AuthState {
  user: MeResponse | null
  loading: boolean
  setUser: (u: MeResponse | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  function logout() {
    clearToken()
    resetSessionLanguage()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
