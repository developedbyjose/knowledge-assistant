"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"

import { AppHeader } from "@/components/layout/app-header"
import { UserRole } from "@/lib/api"
import { useAuth } from "./auth-context"

export function AuthGate({ children, roles }: { children: React.ReactNode; roles?: UserRole[] }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const authorized = Boolean(user && (!roles || roles.includes(user.role)))

  useEffect(() => {
    if (loading) return
    if (!user) router.replace(`/login?next=${encodeURIComponent(pathname)}`)
    else if (user.must_change_password) router.replace("/change-password")
    else if (!authorized) router.replace("/chat")
  }, [authorized, loading, pathname, router, user])

  if (loading || !authorized || user?.must_change_password) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading account…</div>
  }

  return <><AppHeader />{children}</>
}
