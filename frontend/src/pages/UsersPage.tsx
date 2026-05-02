import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MailIcon, PlusIcon, ShieldCheckIcon, Trash2Icon, UserIcon } from 'lucide-react'
import {
  type AdminUser,
  createUser,
  deleteUser,
  listUsers,
  sendWelcomeEmail,
  updateUser,
} from '@/api/admin'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const ROLE_LABEL: Record<string, string> = {
  super_admin: 'Super Admin',
  tenant_admin: 'Admin',
  staff: 'Staff',
  guest: 'Guest',
}

const ROLE_VARIANT: Record<string, 'default' | 'secondary' | 'outline'> = {
  super_admin: 'default',
  tenant_admin: 'default',
  staff: 'secondary',
  guest: 'outline',
}

function RoleBadge({ role }: { role: string }) {
  return (
    <Badge variant={ROLE_VARIANT[role] ?? 'outline'}>
      {ROLE_LABEL[role] ?? role}
    </Badge>
  )
}

// ── New user dialog ───────────────────────────────────────────────────────────

function NewUserDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('staff')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => createUser({
      email: email.trim(),
      role,
      send_welcome: true,
      first_name: firstName.trim() || null,
      last_name: lastName.trim() || null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      setEmail('')
      setRole('staff')
      setFirstName('')
      setLastName('')
      setError(null)
      onClose()
    },
    onError: (err: unknown) => {
      setError((err as Error).message ?? 'Something went wrong')
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    mutation.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add user</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="first-name">First name</Label>
              <Input
                id="first-name"
                value={firstName}
                onChange={e => setFirstName(e.target.value)}
                placeholder="Optional"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="last-name">Last name</Label>
              <Input
                id="last-name"
                value={lastName}
                onChange={e => setLastName(e.target.value)}
                placeholder="Optional"
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="name@example.com"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="role">Role</Label>
            <Select value={role} onValueChange={v => { if (v) setRole(v) }}>
              <SelectTrigger id="role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="staff">Staff</SelectItem>
                <SelectItem value="tenant_admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <p className="text-xs text-muted-foreground">
            A welcome email with a password setup link will be sent automatically.
          </p>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Sending…' : 'Create & send welcome email'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── Edit role dialog ──────────────────────────────────────────────────────────

function EditUserDialog({
  user,
  onClose,
}: {
  user: AdminUser
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [role, setRole] = useState(user.role)
  const [firstName, setFirstName] = useState(user.first_name ?? '')
  const [lastName, setLastName] = useState(user.last_name ?? '')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => updateUser(user.id, {
      role,
      first_name: firstName.trim() || null,
      last_name: lastName.trim() || null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      onClose()
    },
    onError: (err: unknown) => {
      setError((err as Error).message ?? 'Something went wrong')
    },
  })

  const isDirty = role !== user.role
    || firstName.trim() !== (user.first_name ?? '')
    || lastName.trim() !== (user.last_name ?? '')

  return (
    <Dialog open onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Edit user</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <p className="text-xs text-muted-foreground">{user.email}</p>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>First name</Label>
              <Input value={firstName} onChange={e => setFirstName(e.target.value)} placeholder="Optional" />
            </div>
            <div className="space-y-1.5">
              <Label>Last name</Label>
              <Input value={lastName} onChange={e => setLastName(e.target.value)} placeholder="Optional" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select value={role} onValueChange={v => { if (v) setRole(v as AdminUser['role']) }}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="staff">Staff</SelectItem>
                <SelectItem value="tenant_admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !isDirty}>
              Save
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── User row ──────────────────────────────────────────────────────────────────

function UserRow({ user }: { user: AdminUser }) {
  const qc = useQueryClient()
  const [editOpen, setEditOpen] = useState(false)
  const [confirmDeactivate, setConfirmDeactivate] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const welcomeMutation = useMutation({
    mutationFn: () => sendWelcomeEmail(user.id),
    onError: (err: unknown) => {
      setActionError((err as Error).message ?? 'Failed to send email')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: () => updateUser(user.id, { is_active: !user.is_active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      setConfirmDeactivate(false)
    },
    onError: (err: unknown) => {
      setActionError((err as Error).message ?? 'Something went wrong')
    },
  })

  const [confirmDelete, setConfirmDelete] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => deleteUser(user.id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-users'] }); setConfirmDelete(false) },
    onError: (err: unknown) => { setActionError((err as Error).message ?? 'Delete failed'); setConfirmDelete(false) },
  })

  const isGuest = user.role === 'guest'

  return (
    <>
      <tr className={`border-b last:border-0 ${!user.is_active ? 'opacity-50' : ''}`}>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {user.role === 'tenant_admin' || user.role === 'super_admin'
              ? <ShieldCheckIcon size={14} className="text-muted-foreground flex-shrink-0" />
              : <UserIcon size={14} className="text-muted-foreground flex-shrink-0" />
            }
            <div>
              <p className="text-sm font-medium">{user.email}</p>
              {(user.first_name || user.last_name) ? (
                <p className="text-xs text-muted-foreground">
                  {[user.first_name, user.last_name].filter(Boolean).join(' ')}
                </p>
              ) : user.client_name ? (
                <p className="text-xs text-muted-foreground">{user.client_name}</p>
              ) : null}
            </div>
          </div>
        </td>
        <td className="px-4 py-3">
          <RoleBadge role={user.role} />
        </td>
        <td className="px-4 py-3">
          <span className={`text-xs font-medium ${user.is_active ? 'text-green-600' : 'text-muted-foreground'}`}>
            {user.is_active ? 'Active' : 'Inactive'}
          </span>
        </td>
        <td className="px-4 py-3 text-right">
          {actionError && (
            <span className="text-xs text-destructive mr-2">{actionError}</span>
          )}
          <div className="flex items-center justify-end gap-1">
            {!isGuest && (
              <Button
                size="sm"
                variant="ghost"
                className="text-xs h-7"
                onClick={() => setEditOpen(true)}
              >
                Edit
              </Button>
            )}
            {!isGuest && (
              <Button
                size="sm"
                variant="ghost"
                className="text-xs h-7"
                disabled={welcomeMutation.isPending}
                onClick={() => { setActionError(null); welcomeMutation.mutate() }}
                title="Send welcome / password reset email"
              >
                <MailIcon size={13} className="mr-1" />
                {welcomeMutation.isPending ? 'Sending…' : welcomeMutation.isSuccess ? 'Sent!' : 'Send welcome'}
              </Button>
            )}
            {!isGuest && !confirmDeactivate && (
              <Button
                size="sm"
                variant="ghost"
                className="text-xs h-7 text-muted-foreground"
                onClick={() => setConfirmDeactivate(true)}
              >
                {user.is_active ? 'Deactivate' : 'Reactivate'}
              </Button>
            )}
            {confirmDeactivate && (
              <span className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">Sure?</span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs h-7 text-destructive"
                  disabled={toggleMutation.isPending}
                  onClick={() => toggleMutation.mutate()}
                >
                  Yes
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs h-7"
                  onClick={() => setConfirmDeactivate(false)}
                >
                  No
                </Button>
              </span>
            )}
            {!confirmDelete && (
              <Button
                size="sm"
                variant="ghost"
                className="text-xs h-7 text-muted-foreground"
                onClick={() => { setConfirmDelete(true); setConfirmDeactivate(false); setActionError(null) }}
                title="Permanently delete user"
              >
                <Trash2Icon size={13} />
              </Button>
            )}
            {confirmDelete && (
              <span className="flex items-center gap-1 flex-wrap justify-end">
                <span className="text-xs text-muted-foreground">
                  Permanently delete?
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs h-7 text-destructive"
                  disabled={deleteMutation.isPending}
                  onClick={() => deleteMutation.mutate()}
                >
                  {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs h-7"
                  onClick={() => setConfirmDelete(false)}
                >
                  Cancel
                </Button>
              </span>
            )}
          </div>
        </td>
      </tr>
      {editOpen && <EditUserDialog user={user} onClose={() => setEditOpen(false)} />}
    </>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function UsersPage() {
  const [newOpen, setNewOpen] = useState(false)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: listUsers,
  })

  const staffAndAdmin = users.filter(u => u.role !== 'guest')
  const guests = users.filter(u => u.role === 'guest')

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Users</h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              Manage staff and admin accounts.
            </p>
          </div>
          <Button onClick={() => setNewOpen(true)}>
            <PlusIcon size={14} className="mr-1.5" />
            Add user
          </Button>
        </div>

        {isLoading ? (
          <div className="bg-white border rounded-lg p-8 text-center text-sm text-muted-foreground">
            Loading…
          </div>
        ) : (
          <>
            <div className="bg-white border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b">
                <h2 className="text-sm font-medium">Staff & Admins</h2>
              </div>
              {staffAndAdmin.length === 0 ? (
                <p className="text-sm text-muted-foreground px-4 py-6 text-center">No staff users yet.</p>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground">User</th>
                      <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground">Role</th>
                      <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                      <th className="px-4 py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {staffAndAdmin.map(u => <UserRow key={u.id} user={u} />)}
                  </tbody>
                </table>
              )}
            </div>

            {guests.length > 0 && (
              <div className="bg-white border rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b">
                  <h2 className="text-sm font-medium">Guest accounts</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Self-registered clients — created when a client books online.
                  </p>
                </div>
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground">User</th>
                      <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground">Role</th>
                      <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                      <th className="px-4 py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {guests.map(u => <UserRow key={u.id} user={u} />)}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      <NewUserDialog open={newOpen} onClose={() => setNewOpen(false)} />
    </div>
  )
}
