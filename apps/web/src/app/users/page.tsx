"use client"

import { FormEvent, useCallback, useEffect, useState } from "react"
import { KeyRoundIcon, Loader2Icon, PlusIcon, RefreshCwIcon, UserCogIcon } from "lucide-react"

import { PageContainer } from "@/components/layout/page-container"
import { PageHeader } from "@/components/layout/page-header"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { AuthGate } from "@/features/auth/auth-gate"
import { AuthUser, UserRole, createUser, listUsers, resetUserPassword, updateUser } from "@/lib/api"

function UsersPageContent() {
  const [users, setUsers] = useState<AuthUser[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [role, setRole] = useState<UserRole>("user")
  const [temporaryPassword, setTemporaryPassword] = useState("")
  const [resetTarget, setResetTarget] = useState<AuthUser | null>(null)
  const [resetPassword, setResetPassword] = useState("")

  const load = useCallback(async () => {
    setError(null)
    try { setUsers(await listUsers()) }
    catch (caught) { setError(message(caught)) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    let active = true
    async function loadInitialUsers() {
      try {
        const loaded = await listUsers()
        if (active) setUsers(loaded)
      } catch (caught) {
        if (active) setError(message(caught))
      } finally {
        if (active) setLoading(false)
      }
    }
    void loadInitialUsers()
    return () => { active = false }
  }, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault(); setSubmitting(true); setError(null)
    try {
      const created = await createUser({ email, display_name: displayName, role, temporary_password: temporaryPassword })
      setUsers((current) => [created, ...current]); setEmail(""); setDisplayName(""); setRole("user"); setTemporaryPassword("")
    } catch (caught) { setError(message(caught)) }
    finally { setSubmitting(false) }
  }

  async function patchUser(user: AuthUser, values: { role?: UserRole; is_active?: boolean }) {
    setError(null)
    try {
      const updated = await updateUser(user.id, values)
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (caught) { setError(message(caught)) }
  }

  async function handleReset() {
    if (!resetTarget) return
    setSubmitting(true); setError(null)
    try {
      const updated = await resetUserPassword(resetTarget.id, resetPassword)
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item))
      setResetTarget(null); setResetPassword("")
    } catch (caught) { setError(message(caught)) }
    finally { setSubmitting(false) }
  }

  return (
    <PageContainer size="wide" className="py-8">
      <PageHeader title="Users" description="Create accounts, assign roles, and manage access." actions={<Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}><RefreshCwIcon className={loading ? "size-4 animate-spin" : "size-4"} />Refresh</Button>} />
      {error ? <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert> : null}
      <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Card><CardHeader><CardTitle>Create user</CardTitle><CardDescription>The temporary password must be changed at first login.</CardDescription></CardHeader><CardContent>
          <form className="space-y-4" onSubmit={handleCreate}>
            <Field label="Display name" id="display-name"><Input id="display-name" required value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></Field>
            <Field label="Email" id="new-email"><Input id="new-email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></Field>
            <Field label="Role" id="new-role"><select id="new-role" value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option value="user">User</option><option value="admin">Admin</option><option value="superadmin">Superadmin</option></select></Field>
            <Field label="Temporary password" id="temporary-password"><Input id="temporary-password" type="password" minLength={12} maxLength={128} required value={temporaryPassword} onChange={(event) => setTemporaryPassword(event.target.value)} /></Field>
            <Button className="w-full" type="submit" disabled={submitting}>{submitting ? <Loader2Icon className="size-4 animate-spin" /> : <PlusIcon className="size-4" />}Create account</Button>
          </form>
        </CardContent></Card>

        <Card><CardHeader><CardTitle>Accounts</CardTitle><CardDescription>{users.length} configured user{users.length === 1 ? "" : "s"}.</CardDescription></CardHeader><CardContent>
          {loading ? <p className="py-8 text-center text-sm text-muted-foreground">Loading users…</p> : users.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">No users found.</p> : (
            <Table><TableHeader><TableRow><TableHead>User</TableHead><TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader><TableBody>
              {users.map((user) => <TableRow key={user.id}>
                <TableCell><p className="font-medium">{user.display_name}</p><p className="text-xs text-muted-foreground">{user.email}</p>{user.must_change_password ? <p className="mt-1 text-xs text-amber-700">Password change required</p> : null}</TableCell>
                <TableCell><select aria-label={`Role for ${user.display_name}`} value={user.role} onChange={(event) => void patchUser(user, { role: event.target.value as UserRole })} className="h-9 rounded-md border border-input bg-background px-2 text-sm"><option value="user">User</option><option value="admin">Admin</option><option value="superadmin">Superadmin</option></select></TableCell>
                <TableCell><Badge variant={user.is_active ? "secondary" : "outline"}>{user.is_active ? "Active" : "Inactive"}</Badge></TableCell>
                <TableCell><div className="flex justify-end gap-2"><Button variant="outline" size="sm" onClick={() => { setResetTarget(user); setResetPassword("") }}><KeyRoundIcon className="size-4" />Reset</Button><Button variant={user.is_active ? "destructive" : "secondary"} size="sm" onClick={() => void patchUser(user, { is_active: !user.is_active })}><UserCogIcon className="size-4" />{user.is_active ? "Deactivate" : "Activate"}</Button></div></TableCell>
              </TableRow>)}
            </TableBody></Table>
          )}
        </CardContent></Card>
      </div>

      <Dialog open={resetTarget !== null} onOpenChange={(open) => { if (!open) setResetTarget(null) }}><DialogContent><DialogHeader><DialogTitle>Reset temporary password</DialogTitle><DialogDescription>This revokes all sessions for {resetTarget?.display_name} and requires a password change on next login.</DialogDescription></DialogHeader><Field label="New temporary password" id="reset-password"><Input id="reset-password" type="password" minLength={12} maxLength={128} value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} /></Field><DialogFooter><Button variant="outline" onClick={() => setResetTarget(null)}>Cancel</Button><Button onClick={() => void handleReset()} disabled={submitting || resetPassword.length < 12}>Reset password</Button></DialogFooter></DialogContent></Dialog>
    </PageContainer>
  )
}

function Field({ label, id, children }: { label: string; id: string; children: React.ReactNode }) {
  return <div className="space-y-2"><label htmlFor={id} className="text-sm font-medium">{label}</label>{children}</div>
}

function message(caught: unknown) { return caught instanceof Error ? caught.message : "Something went wrong." }

export default function UsersPage() {
  return <AuthGate roles={["superadmin"]}><UsersPageContent /></AuthGate>
}
