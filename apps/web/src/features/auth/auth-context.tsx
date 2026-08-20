"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { ApiError, AuthUser, getMe, logout as logoutRequest } from "@/lib/api"

type AuthContextValue = {
  user: AuthUser | null
  loading: boolean
  refresh: () => Promise<AuthUser | null>
  setUser: (user: AuthUser | null) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const current = await getMe()
      setUser(current)
      return current
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setUser(null)
        return null
      }
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    async function loadCurrentUser() {
      try {
        const current = await getMe()
        if (active) setUser(current)
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 401)) throw error
      } finally {
        if (active) setLoading(false)
      }
    }
    void loadCurrentUser()
    return () => { active = false }
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ user, loading, refresh, setUser, logout }), [user, loading, refresh, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }
  return context
}
