import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '@/api/auth'
import { Button } from '@/components/ui/button'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const fieldClass =
    'w-full border-0 border-b border-input bg-transparent px-0 py-2 text-sm focus:outline-none focus:border-foreground transition-colors'
  const labelClass = 'text-xs uppercase tracking-wider text-muted-foreground'

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
    <div className="min-h-screen grid lg:grid-cols-[1.1fr_1fr]">
      {/* Left: portrait hero panel */}
      <div className="relative hidden lg:block">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(/images/Erin.Salon.Final-5.jpg)' }}
          aria-hidden
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-black/30 to-black/60" aria-hidden />
        <div className="relative z-10 h-full flex flex-col justify-between p-10 text-white">
          <Link to="/" className="inline-block">
            <img src="/salon-lyol-logo.png" alt="Salon Lyol" className="h-9 w-auto" />
          </Link>
          <div className="space-y-4 max-w-sm">
            <p className="text-xs tracking-[0.4em] uppercase text-white/70">Salon Lyol · Toronto</p>
            <p
              className="text-3xl xl:text-4xl font-light leading-tight"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Every day can be a <em className="font-normal">good hair day.</em>
            </p>
          </div>
        </div>
      </div>

      {/* Right: reset form */}
      <div className="flex items-center justify-center px-6 py-12 bg-[#faf9f7]">
        <div className="w-full max-w-sm space-y-8">
          <div className="flex justify-center lg:hidden">
            <img src="/salon-lyol-logo.png" alt="Salon Lyol" className="h-12 w-auto" />
          </div>

          {!token ? (
            <div className="text-center space-y-3">
              <h1 className="text-3xl font-light" style={{ fontFamily: 'var(--font-display)' }}>
                Invalid reset link
              </h1>
              <p className="text-sm text-muted-foreground">This link is missing or malformed.</p>
              <Button variant="outline" onClick={() => navigate('/login')}>Go to login</Button>
            </div>
          ) : done ? (
            <div className="text-center space-y-4">
              <p className="text-xs tracking-[0.3em] uppercase text-muted-foreground">All set</p>
              <h1 className="text-3xl font-light" style={{ fontFamily: 'var(--font-display)' }}>
                Password set
              </h1>
              <p className="text-sm text-muted-foreground">You can now sign in with your new password.</p>
              <Button onClick={() => navigate('/login')} className="h-12 rounded-sm tracking-widest uppercase text-xs">
                Go to sign in
              </Button>
            </div>
          ) : (
            <>
              <div className="space-y-2 text-center lg:text-left">
                <p className="text-xs tracking-[0.3em] uppercase text-muted-foreground">Almost there</p>
                <h1 className="text-3xl font-light" style={{ fontFamily: 'var(--font-display)' }}>
                  Set your password
                </h1>
                <p className="text-sm text-muted-foreground">Choose a password to activate your account.</p>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="space-y-1">
                  <label htmlFor="password" className={labelClass}>New password</label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    required
                    className={fieldClass}
                  />
                </div>
                <div className="space-y-1">
                  <label htmlFor="confirm" className={labelClass}>Confirm password</label>
                  <input
                    id="confirm"
                    type="password"
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    placeholder="Repeat password"
                    required
                    className={fieldClass}
                  />
                </div>
                {error && <p className="text-sm text-destructive">{error}</p>}
                <Button type="submit" disabled={loading} className="mt-2 h-12 rounded-sm tracking-widest uppercase text-xs">
                  {loading ? 'Saving…' : 'Set password'}
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
