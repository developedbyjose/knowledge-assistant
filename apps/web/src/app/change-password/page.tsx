"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { KeyRoundIcon, Loader2Icon } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/features/auth/auth-context"
import { changePassword } from "@/lib/api"

export default function ChangePasswordPage() {
  const { user, loading, setUser } = useAuth()
  const router = useRouter()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmation, setConfirmation] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) router.replace("/login")
  }, [loading, router, user])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (newPassword !== confirmation) { setError("New passwords do not match."); return }
    setSubmitting(true); setError(null)
    try {
      const result = await changePassword(currentPassword, newPassword)
      setUser(result.user)
      router.replace(result.user.role === "user" ? "/chat" : "/")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to change password.")
    } finally { setSubmitting(false) }
  }

  if (loading || !user) return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading account…</div>

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto flex size-10 items-center justify-center rounded-lg border bg-background"><KeyRoundIcon className="size-5" /></div>
          <div><CardTitle className="text-xl">Set a new password</CardTitle><CardDescription className="mt-1">Replace your temporary password before continuing.</CardDescription></div>
        </CardHeader>
        <CardContent><form className="space-y-4" onSubmit={handleSubmit}>
          {error ? <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert> : null}
          <div className="space-y-2"><label htmlFor="current-password" className="text-sm font-medium">Temporary password</label><Input id="current-password" type="password" autoComplete="current-password" required value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /></div>
          <div className="space-y-2"><label htmlFor="new-password" className="text-sm font-medium">New password</label><Input id="new-password" type="password" minLength={12} maxLength={128} autoComplete="new-password" required value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /><p className="text-xs text-muted-foreground">Use 12–128 characters.</p></div>
          <div className="space-y-2"><label htmlFor="confirm-password" className="text-sm font-medium">Confirm new password</label><Input id="confirm-password" type="password" minLength={12} maxLength={128} autoComplete="new-password" required value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></div>
          <Button className="w-full" type="submit" disabled={submitting}>{submitting ? <Loader2Icon className="size-4 animate-spin" /> : null}Change password</Button>
        </form></CardContent>
      </Card>
    </main>
  )
}
