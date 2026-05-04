import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { register } from '@/api/auth'
import { useAuth } from '@/store/auth'
import { Button } from '@/components/ui/button'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { setUser } = useAuth()
  const { t } = useTranslation()

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (form.password !== form.confirm_password) {
      setError(t('auth.passwords_no_match'))
      return
    }
    if (form.password.length < 8) {
      setError(t('auth.password_too_short'))
      return
    }

    setLoading(true)
    try {
      const user = await register(form.first_name, form.last_name, form.email, form.phone, form.password)
      setUser(user)
      navigate('/my-requests', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const fieldClass =
    'w-full border-0 border-b border-input bg-transparent px-0 py-2 text-sm focus:outline-none focus:border-foreground transition-colors'
  const labelClass = 'text-xs uppercase tracking-wider text-muted-foreground'

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

      {/* Right: registration form */}
      <div className="flex items-center justify-center px-6 py-12 bg-[#faf9f7]">
        <div className="w-full max-w-sm space-y-8">
          <div className="flex justify-center lg:hidden">
            <img src="/salon-lyol-logo.png" alt="Salon Lyol" className="h-12 w-auto" />
          </div>

          <div className="space-y-2 text-center lg:text-left">
            <p className="text-xs tracking-[0.3em] uppercase text-muted-foreground">{t('auth.new_here')}</p>
            <h1
              className="text-3xl font-light"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              {t('auth.register_heading')}
            </h1>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label htmlFor="first_name" className={labelClass}>{t('auth.first_name')}</label>
                <input id="first_name" name="first_name" value={form.first_name} onChange={handleChange} required autoComplete="given-name" className={fieldClass} />
              </div>
              <div className="space-y-1">
                <label htmlFor="last_name" className={labelClass}>{t('auth.last_name')}</label>
                <input id="last_name" name="last_name" value={form.last_name} onChange={handleChange} required autoComplete="family-name" className={fieldClass} />
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="email" className={labelClass}>{t('auth.email_label')}</label>
              <input id="email" name="email" type="email" value={form.email} onChange={handleChange} required autoComplete="email" className={fieldClass} />
            </div>

            <div className="space-y-1">
              <label htmlFor="phone" className={labelClass}>{t('auth.cell_phone')}</label>
              <input id="phone" name="phone" type="tel" value={form.phone} onChange={handleChange} required autoComplete="tel" placeholder="416-555-0100" className={fieldClass} />
            </div>

            <div className="space-y-1">
              <label htmlFor="password" className={labelClass}>{t('auth.password_label')}</label>
              <input id="password" name="password" type="password" value={form.password} onChange={handleChange} required autoComplete="new-password" className={fieldClass} />
            </div>

            <div className="space-y-1">
              <label htmlFor="confirm_password" className={labelClass}>{t('auth.confirm_password')}</label>
              <input id="confirm_password" name="confirm_password" type="password" value={form.confirm_password} onChange={handleChange} required autoComplete="new-password" className={fieldClass} />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" disabled={loading} className="mt-2 h-12 rounded-sm tracking-widest uppercase text-xs">
              {loading ? t('auth.creating_account') : t('auth.create_account')}
            </Button>

            <p className="text-center text-sm text-muted-foreground pt-2">
              {t('auth.already_have_account')}{' '}
              <Link to="/login" className="text-foreground underline-offset-4 hover:underline">
                {t('auth.sign_in_link')}
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
