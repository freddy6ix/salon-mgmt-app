import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getBranding, updateBranding, type BrandingSettings } from '@/api/settings'
import { getEmailConfig, saveEmailConfig, testEmailConfig } from '@/api/admin'
import { useAuth } from '@/store/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { applyBranding } from '@/lib/branding'

export default function SettingsPage() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin'

  const { data: branding, isLoading } = useQuery({
    queryKey: ['branding'],
    queryFn: getBranding,
  })

  const [logoUrl, setLogoUrl] = useState('')
  const [brandColor, setBrandColor] = useState('#18181b')

  useEffect(() => {
    if (branding) {
      setLogoUrl(branding.logo_url ?? '')
      setBrandColor(branding.brand_color ?? '#18181b')
    }
  }, [branding])

  const brandingMutation = useMutation({
    mutationFn: () => updateBranding({ logo_url: logoUrl || null, brand_color: brandColor }),
    onSuccess: (updated: BrandingSettings) => {
      qc.setQueryData(['branding'], updated)
      applyBranding(updated)
    },
  })

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading…</div>

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your salon configuration.</p>
        </div>

        {/* Branding */}
        <section className="border rounded-lg p-5 space-y-5 bg-white">
          <h2 className="text-base font-medium">Branding</h2>

          <div className="space-y-2">
            <label className="text-sm font-medium">Logo URL</label>
            <input
              type="url"
              value={logoUrl}
              onChange={e => setLogoUrl(e.target.value)}
              placeholder="https://example.com/logo.png"
              className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
            />
            <p className="text-xs text-muted-foreground">
              Paste a publicly accessible image URL. Recommended: square PNG or SVG, transparent background.
            </p>
            {logoUrl && (
              <div className="flex items-center gap-4 pt-1">
                <img
                  src={logoUrl}
                  alt="Logo preview"
                  className="h-12 w-auto object-contain border rounded p-1 bg-muted/30"
                  onError={e => (e.currentTarget.style.display = 'none')}
                />
                <span className="text-xs text-muted-foreground">Preview</span>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Brand colour</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={brandColor}
                onChange={e => setBrandColor(e.target.value)}
                className="h-9 w-16 cursor-pointer rounded border border-input p-0.5 bg-background"
              />
              <input
                type="text"
                value={brandColor}
                onChange={e => {
                  const v = e.target.value
                  if (/^#[0-9a-fA-F]{0,6}$/.test(v)) setBrandColor(v)
                }}
                className="w-28 border border-input rounded-md px-3 py-2 text-sm bg-background font-mono"
                maxLength={7}
              />
              <div
                className="h-9 w-24 rounded border border-input text-xs flex items-center justify-center font-medium"
                style={{ backgroundColor: brandColor.length === 7 ? brandColor : undefined }}
              >
                <span style={{ color: colorIsDark(brandColor) ? '#fff' : '#000' }}>Button</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Applied to buttons and accents throughout the app.</p>
          </div>

          {brandingMutation.isError && (
            <p className="text-xs text-destructive">
              {brandingMutation.error instanceof Error ? brandingMutation.error.message : 'Save failed'}
            </p>
          )}

          <Button onClick={() => brandingMutation.mutate()} disabled={brandingMutation.isPending}>
            {brandingMutation.isPending ? 'Saving…' : 'Save branding'}
          </Button>
        </section>

        {/* Email — admin only */}
        {isAdmin && <EmailSection />}
      </div>
    </div>
  )
}

function EmailSection() {
  const { user } = useAuth()
  const qc = useQueryClient()

  const { data: cfg, isLoading } = useQuery({
    queryKey: ['email-config'],
    queryFn: getEmailConfig,
  })

  const [host, setHost] = useState('')
  const [port, setPort] = useState('587')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [useTls, setUseTls] = useState(true)
  const [fromAddress, setFromAddress] = useState('')
  const [testTo, setTestTo] = useState(user?.email ?? '')
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [testMsg, setTestMsg] = useState<string | null>(null)

  useEffect(() => {
    if (cfg?.is_configured) {
      setHost(cfg.smtp_host)
      setPort(String(cfg.smtp_port))
      setUsername(cfg.smtp_username)
      setUseTls(cfg.smtp_use_tls)
      setFromAddress(cfg.from_address)
    }
  }, [cfg])

  const saveMutation = useMutation({
    mutationFn: () => saveEmailConfig({
      smtp_host: host.trim(),
      smtp_port: parseInt(port, 10),
      smtp_username: username.trim(),
      smtp_password: password || undefined,
      smtp_use_tls: useTls,
      from_address: fromAddress.trim(),
    }),
    onSuccess: updated => {
      qc.setQueryData(['email-config'], updated)
      setPassword('')
      setSaveMsg('Saved.')
      setTimeout(() => setSaveMsg(null), 3000)
    },
    onError: (err: unknown) => setSaveMsg((err as Error).message),
  })

  const testMutation = useMutation({
    mutationFn: () => testEmailConfig(testTo),
    onSuccess: () => {
      setTestMsg(`Test email sent to ${testTo}`)
      setTimeout(() => setTestMsg(null), 5000)
    },
    onError: (err: unknown) => setTestMsg((err as Error).message),
  })

  if (isLoading) return null

  return (
    <section className="border rounded-lg p-5 space-y-5 bg-white">
      <div>
        <h2 className="text-base font-medium">Email (SMTP)</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Used for welcome emails and password resets. Works with Google Workspace, Resend SMTP, SendGrid, or any provider.
        </p>
      </div>

      {cfg?.is_configured && (
        <div className="text-xs bg-green-50 border border-green-200 text-green-800 rounded-md px-3 py-2">
          Configured — sending from <strong>{cfg.from_address}</strong>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5 col-span-2 sm:col-span-1">
          <Label htmlFor="smtp-host">SMTP host</Label>
          <Input
            id="smtp-host"
            value={host}
            onChange={e => setHost(e.target.value)}
            placeholder="smtp.gmail.com"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="smtp-port">Port</Label>
          <Input
            id="smtp-port"
            type="number"
            value={port}
            onChange={e => setPort(e.target.value)}
            placeholder="587"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="smtp-username">Username</Label>
        <Input
          id="smtp-username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="noreply@salonlyol.ca"
          autoComplete="off"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="smtp-password">
          Password / App password
          {cfg?.smtp_password_set && (
            <span className="ml-2 text-xs font-normal text-muted-foreground">(leave blank to keep current)</span>
          )}
        </Label>
        <Input
          id="smtp-password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder={cfg?.smtp_password_set ? '••••••••' : 'Required'}
          autoComplete="new-password"
        />
        <p className="text-xs text-muted-foreground">
          For Google Workspace: use an{' '}
          <strong>App Password</strong> (Google Account → Security → 2-Step Verification → App passwords).
          For Resend SMTP: username <code className="bg-muted px-1 rounded">resend</code>, password = your API key.
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="from-address">From address</Label>
        <Input
          id="from-address"
          value={fromAddress}
          onChange={e => setFromAddress(e.target.value)}
          placeholder="Salon Lyol <noreply@salonlyol.ca>"
        />
        <p className="text-xs text-muted-foreground">
          Use the format <code className="bg-muted px-1 rounded">Name &lt;email@domain.com&gt;</code>
        </p>
      </div>

      <div className="flex items-center gap-2">
        <input
          id="use-tls"
          type="checkbox"
          checked={useTls}
          onChange={e => setUseTls(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300"
        />
        <Label htmlFor="use-tls" className="font-normal cursor-pointer">
          Use STARTTLS (recommended for port 587)
        </Label>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <Button
          onClick={() => { setSaveMsg(null); saveMutation.mutate() }}
          disabled={saveMutation.isPending}
        >
          {saveMutation.isPending ? 'Saving…' : 'Save'}
        </Button>
        {saveMsg && (
          <span className={`text-sm ${saveMsg === 'Saved.' ? 'text-green-600' : 'text-destructive'}`}>
            {saveMsg}
          </span>
        )}
      </div>

      {cfg?.is_configured && (
        <div className="border-t pt-4 space-y-3">
          <h3 className="text-sm font-medium">Send test email</h3>
          <div className="flex gap-2 items-center flex-wrap">
            <Input
              className="max-w-xs"
              type="email"
              value={testTo}
              onChange={e => setTestTo(e.target.value)}
              placeholder="recipient@example.com"
            />
            <Button
              variant="outline"
              onClick={() => { setTestMsg(null); testMutation.mutate() }}
              disabled={testMutation.isPending || !testTo}
            >
              {testMutation.isPending ? 'Sending…' : 'Send test'}
            </Button>
          </div>
          {testMsg && (
            <p className={`text-sm ${testMsg.startsWith('Test email sent') ? 'text-green-600' : 'text-destructive'}`}>
              {testMsg}
            </p>
          )}
        </div>
      )}
    </section>
  )
}

function colorIsDark(hex: string): boolean {
  if (hex.length !== 7) return true
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5
}
