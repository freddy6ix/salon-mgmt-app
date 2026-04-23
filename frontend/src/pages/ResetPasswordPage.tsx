import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30">
        <div className="bg-white border rounded-xl p-8 max-w-sm w-full text-center space-y-3">
          <p className="font-medium">Invalid reset link</p>
          <p className="text-sm text-muted-foreground">This link is missing or malformed.</p>
          <Button variant="outline" onClick={() => navigate('/login')}>Go to login</Button>
        </div>
      </div>
    )
  }

  if (done) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30">
        <div className="bg-white border rounded-xl p-8 max-w-sm w-full text-center space-y-4">
          <p className="text-xl font-semibold">Password set!</p>
          <p className="text-sm text-muted-foreground">You can now sign in with your new password.</p>
          <Button onClick={() => navigate('/login')}>Go to login</Button>
        </div>
      </div>
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await resetPassword(token, password)
      setDone(true)
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <div className="bg-white border rounded-xl p-8 max-w-sm w-full space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Set your password</h1>
          <p className="text-sm text-muted-foreground mt-1">Choose a password to activate your account.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="password">New password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm">Confirm password</Label>
            <Input
              id="confirm"
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat password"
              required
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Saving…' : 'Set password'}
          </Button>
        </form>
      </div>
    </div>
  )
}
