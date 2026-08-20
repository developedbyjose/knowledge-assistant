"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { BookOpenIcon, LogOutIcon, MessageSquareIcon, UsersIcon } from "lucide-react"

import { useAuth } from "@/features/auth/auth-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export function AppHeader() {
  const { user, logout } = useAuth()
  const router = useRouter()
  if (!user) return null
  const isAdmin = user.role === "admin" || user.role === "superadmin"

  return (
    <header className="sticky top-0 z-30 border-b bg-background">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-4 px-4 sm:px-6">
        <Link href={isAdmin ? "/" : "/chat"} className="font-semibold tracking-tight">Knowledge Assistant</Link>
        <nav className="flex flex-1 items-center gap-1" aria-label="Primary navigation">
          <Button variant="ghost" size="sm" render={<Link href="/chat" />}><MessageSquareIcon className="size-4" />Chat</Button>
          {isAdmin ? <Button variant="ghost" size="sm" render={<Link href="/" />}><BookOpenIcon className="size-4" />Knowledge</Button> : null}
          {user.role === "superadmin" ? <Button variant="ghost" size="sm" render={<Link href="/users" />}><UsersIcon className="size-4" />Users</Button> : null}
        </nav>
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium leading-none">{user.display_name}</p>
          <p className="mt-1 text-xs text-muted-foreground">{user.email}</p>
        </div>
        <Badge variant="outline" className="capitalize">{user.role}</Badge>
        <Button variant="ghost" size="icon" aria-label="Sign out" onClick={async () => { await logout(); router.replace("/login") }}>
          <LogOutIcon className="size-4" />
        </Button>
      </div>
    </header>
  )
}
