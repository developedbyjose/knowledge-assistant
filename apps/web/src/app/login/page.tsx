"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { BookOpenIcon, Loader2Icon } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/features/auth/auth-context"
import { login } from "@/lib/api"

export default function LoginPage() {
  const { user, loading, setUser } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && user) {
      router.replace(user.must_change_password ? "/change-password" : user.role === "user" ? "/chat" : "/")
    }
  }, [loading, router, user])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const result = await login(email, password)
      setUser(result.user)
      router.replace(result.must_change_password ? "/change-password" : result.user.role === "user" ? "/chat" : "/")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto flex size-10 items-center justify-center rounded-lg border bg-background"><BookOpenIcon className="size-5" /></div>
          <div><CardTitle className="text-xl">Sign in</CardTitle><CardDescription className="mt-1">Use your organization-provided account.</CardDescription></div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            {error ? <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert> : null}
            <div className="space-y-2"><label htmlFor="email" className="text-sm font-medium">Email</label><Input id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></div>
            <div className="space-y-2"><label htmlFor="password" className="text-sm font-medium">Password</label><Input id="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></div>
            <Button className="w-full" type="submit" disabled={submitting}>{submitting ? <Loader2Icon className="size-4 animate-spin" /> : null}Sign in</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}
