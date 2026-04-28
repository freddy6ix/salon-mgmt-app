import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Save } from 'lucide-react'
import {
  getBranding,
  updateBranding,
  type BrandingSettings,
  type ContactDetails,
  type SlotMinutes,
  type TimeFormat,
  SLOT_OPTIONS,
  getOperatingHours,
  updateOperatingHours,
  type OperatingHoursDay,
  getRequestNotifications,
  updateRequestNotifications,
} from '@/api/settings'
import { getEmailConfig, saveEmailConfig, testEmailConfig } from '@/api/admin'
import {
  listPaymentMethods,
  createPaymentMethod,
  updatePaymentMethod,
  KIND_OPTIONS,
  type PaymentMethod,
  type PaymentMethodKind,
} from '@/api/paymentMethods'
import { listPromotions, createPromotion, updatePromotion, type Promotion, type PromotionKind } from '@/api/promotions'
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
  const [slotMinutes, setSlotMinutes] = useState<SlotMinutes>(10)
  const [timeFormat, setTimeFormat] = useState<TimeFormat>('12h')
  const EMPTY_CONTACT: ContactDetails = {
    address_line1: null, address_line2: null, city: null, region: null,
    postal_code: null, country: null, phone: null, hours_summary: null,
  }
  const [contact, setContact] = useState<ContactDetails>(EMPTY_CONTACT)

  useEffect(() => {
    if (branding) {
      setLogoUrl(branding.logo_url ?? '')
      setBrandColor(branding.brand_color ?? '#18181b')
      setSlotMinutes((branding.slot_minutes ?? 10) as SlotMinutes)
      setTimeFormat(branding.time_format ?? '12h')
      setContact({
        address_line1: branding.address_line1,
        address_line2: branding.address_line2,
        city: branding.city,
        region: branding.region,
        postal_code: branding.postal_code,
        country: branding.country,
        phone: branding.phone,
        hours_summary: branding.hours_summary,
      })
    }
  }, [branding])

  function setContactField<K extends keyof ContactDetails>(field: K, value: string) {
    setContact(prev => ({ ...prev, [field]: value || null }))
  }

  const brandingMutation = useMutation({
    mutationFn: () => updateBranding({
      logo_url: logoUrl || null,
      brand_color: brandColor,
      slot_minutes: slotMinutes,
      time_format: timeFormat,
      ...contact,
    }),
    onSuccess: (updated: BrandingSettings) => {
      qc.setQueryData(['branding'], updated)
      qc.invalidateQueries({ queryKey: ['public-tenant-info'] })
      applyBranding(updated)
    },
  })

  const [tab, setTab] = useState<'branding' | 'scheduling' | 'payment-methods' | 'promotions' | 'email'>('branding')

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading…</div>

  const tabs = [
    { id: 'branding', label: 'Branding' },
    { id: 'scheduling', label: 'Scheduling' },
    ...(isAdmin ? [{ id: 'payment-methods', label: 'Payment methods' }] : []),
    ...(isAdmin ? [{ id: 'promotions', label: 'Promotions' }] : []),
    ...(isAdmin ? [{ id: 'email', label: 'Email' }] : []),
  ] as const

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your salon configuration.</p>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as typeof tab)}
              className={`px-4 py-2 text-sm border-b-2 -mb-px transition-colors ${
                tab === t.id
                  ? 'border-foreground font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Branding tab */}
        {tab === 'branding' && (
          <section className="border rounded-lg p-5 space-y-5 bg-white">
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

            <div className="space-y-3 border-t pt-5">
              <div>
                <h2 className="text-sm font-medium">Contact</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Shown on the public landing page and in outbound email footers.
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Address</label>
                <input
                  type="text"
                  value={contact.address_line1 ?? ''}
                  onChange={e => setContactField('address_line1', e.target.value)}
                  placeholder="Street address"
                  className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
                />
                <input
                  type="text"
                  value={contact.address_line2 ?? ''}
                  onChange={e => setContactField('address_line2', e.target.value)}
                  placeholder="Suite, floor (optional)"
                  className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
                />
                <div className="grid grid-cols-3 gap-2">
                  <input
                    type="text"
                    value={contact.city ?? ''}
                    onChange={e => setContactField('city', e.target.value)}
                    placeholder="City"
                    className="border border-input rounded-md px-3 py-2 text-sm bg-background"
                  />
                  <input
                    type="text"
                    value={contact.region ?? ''}
                    onChange={e => setContactField('region', e.target.value)}
                    placeholder="Province / state"
                    className="border border-input rounded-md px-3 py-2 text-sm bg-background"
                  />
                  <input
                    type="text"
                    value={contact.postal_code ?? ''}
                    onChange={e => setContactField('postal_code', e.target.value)}
                    placeholder="Postal code"
                    className="border border-input rounded-md px-3 py-2 text-sm bg-background"
                  />
                </div>
                <input
                  type="text"
                  value={contact.country ?? ''}
                  onChange={e => setContactField('country', e.target.value.toUpperCase().slice(0, 2))}
                  placeholder="Country (2-letter)"
                  maxLength={2}
                  className="w-24 border border-input rounded-md px-3 py-2 text-sm bg-background uppercase"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs uppercase tracking-wider text-muted-foreground">Phone</label>
                  <input
                    type="tel"
                    value={contact.phone ?? ''}
                    onChange={e => setContactField('phone', e.target.value)}
                    placeholder="416-555-0100"
                    className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs uppercase tracking-wider text-muted-foreground">Hours summary</label>
                  <input
                    type="text"
                    value={contact.hours_summary ?? ''}
                    onChange={e => setContactField('hours_summary', e.target.value)}
                    placeholder="Tue–Sat · 9–6"
                    className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
                  />
                </div>
              </div>
            </div>

            {brandingMutation.isError && (
              <p className="text-xs text-destructive">
                {brandingMutation.error instanceof Error ? brandingMutation.error.message : 'Save failed'}
              </p>
            )}

            <Button onClick={() => brandingMutation.mutate()} disabled={brandingMutation.isPending}>
              <Save size={14} className="mr-1.5" />
              {brandingMutation.isPending ? 'Saving…' : 'Save'}
            </Button>
          </section>
        )}

        {/* Scheduling tab */}
        {tab === 'scheduling' && (
          <>
            <OperatingHoursSection isAdmin={isAdmin} />
            <section className="border rounded-lg p-5 space-y-5 bg-white">
              <div className="space-y-2">
                <label className="text-sm font-medium">Appointment book granularity</label>
                <div className="flex gap-2">
                  {SLOT_OPTIONS.map(opt => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setSlotMinutes(opt)}
                      className={`px-3 py-1.5 rounded-md border text-sm transition-colors ${
                        slotMinutes === opt
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'border-input bg-background hover:bg-muted/50'
                      }`}
                    >
                      {opt} min
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Controls the time slot grid resolution and snaps new appointment start times to these intervals.
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Time format</label>
                <div className="flex gap-2">
                  {(['12h', '24h'] as TimeFormat[]).map(opt => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setTimeFormat(opt)}
                      className={`px-3 py-1.5 rounded-md border text-sm transition-colors ${
                        timeFormat === opt
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'border-input bg-background hover:bg-muted/50'
                      }`}
                    >
                      {opt === '12h' ? '12-hour (9:00 AM)' : '24-hour (09:00)'}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Affects how times are displayed throughout the app.
                </p>
              </div>

              {brandingMutation.isError && (
                <p className="text-xs text-destructive">
                  {brandingMutation.error instanceof Error ? brandingMutation.error.message : 'Save failed'}
                </p>
              )}

              <Button onClick={() => brandingMutation.mutate()} disabled={brandingMutation.isPending}>
                <Save size={14} className="mr-1.5" />
                {brandingMutation.isPending ? 'Saving…' : 'Save'}
              </Button>
            </section>
          </>
        )}

        {/* Payment methods tab — admin only */}
        {tab === 'payment-methods' && isAdmin && <PaymentMethodsSection />}

        {/* Promotions tab — admin only */}
        {tab === 'promotions' && isAdmin && <PromotionsSection />}

        {/* Email tab — admin only */}
        {tab === 'email' && isAdmin && (
          <>
            <EmailSection />
            <RequestNotificationsSection />
          </>
        )}
      </div>
    </div>
  )
}

const DAY_LABELS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function OperatingHoursSection({ isAdmin }: { isAdmin: boolean }) {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['operating-hours'],
    queryFn: getOperatingHours,
  })

  const [days, setDays] = useState<OperatingHoursDay[]>([])
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (data) {
      setDays(data.map(d => ({ ...d })))
      setDirty(false)
    }
  }, [data])

  function update(dow: number, patch: Partial<OperatingHoursDay>) {
    setDays(prev => prev.map(d => d.day_of_week === dow ? { ...d, ...patch } : d))
    setDirty(true)
    setError(null)
  }

  function toggleOpen(dow: number, open: boolean) {
    if (open) {
      update(dow, { is_open: true, open_time: '09:00', close_time: '18:00' })
    } else {
      update(dow, { is_open: false, open_time: null, close_time: null })
    }
  }

  const mutation = useMutation({
    mutationFn: () => updateOperatingHours(days),
    onSuccess: updated => {
      qc.setQueryData(['operating-hours'], updated)
      setDirty(false)
      setError(null)
    },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Save failed'),
  })

  if (isLoading) return null

  return (
    <section className="border rounded-lg p-5 space-y-4 bg-white">
      <div>
        <h2 className="text-base font-medium">Operating hours</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Days the salon is open and the hours within which providers can be scheduled.
          {!isAdmin && ' Read-only — only admins can edit.'}
        </p>
      </div>

      <div className="space-y-1.5">
        {days.map(d => (
          <div key={d.day_of_week} className="flex items-center gap-3 text-sm">
            <label className="flex items-center gap-2 w-32 cursor-pointer">
              <input
                type="checkbox"
                checked={d.is_open}
                onChange={e => toggleOpen(d.day_of_week, e.target.checked)}
                disabled={!isAdmin}
                className="accent-primary"
              />
              <span>{DAY_LABELS[d.day_of_week]}</span>
            </label>
            {d.is_open ? (
              <div className="flex items-center gap-1.5">
                <input
                  type="time"
                  value={d.open_time ?? ''}
                  onChange={e => update(d.day_of_week, { open_time: e.target.value })}
                  disabled={!isAdmin}
                  className="border border-input rounded px-2 py-1 text-sm bg-background w-[120px]"
                />
                <span className="text-xs text-muted-foreground">–</span>
                <input
                  type="time"
                  value={d.close_time ?? ''}
                  onChange={e => update(d.day_of_week, { close_time: e.target.value })}
                  disabled={!isAdmin}
                  className="border border-input rounded px-2 py-1 text-sm bg-background w-[120px]"
                />
              </div>
            ) : (
              <span className="text-xs text-muted-foreground">Closed</span>
            )}
          </div>
        ))}
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {isAdmin && (
        <Button onClick={() => mutation.mutate()} disabled={!dirty || mutation.isPending}>
          <Save size={14} className="mr-1.5" />
          {mutation.isPending ? 'Saving…' : 'Save'}
        </Button>
      )}
    </section>
  )
}

function PaymentMethodsSection() {
  const qc = useQueryClient()
  const { data: methods = [], isLoading } = useQuery({
    queryKey: ['payment-methods'],
    queryFn: () => listPaymentMethods(false),
  })

  const [showNew, setShowNew] = useState(false)

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>

  return (
    <section className="border rounded-lg p-5 space-y-4 bg-white">
      <div>
        <h2 className="text-base font-medium">Payment methods</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Configure the payment options shown at checkout. Inactive methods stay on past sales but won't appear in the picker.
        </p>
      </div>

      <div className="space-y-2">
        {methods.length === 0 && (
          <p className="text-sm text-muted-foreground italic">No payment methods yet.</p>
        )}
        {methods.map(m => (
          <PaymentMethodRow key={m.id} method={m} onSaved={() => qc.invalidateQueries({ queryKey: ['payment-methods'] })} />
        ))}
      </div>

      {showNew ? (
        <NewPaymentMethodForm
          onCancel={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); qc.invalidateQueries({ queryKey: ['payment-methods'] }) }}
        />
      ) : (
        <Button variant="outline" size="sm" onClick={() => setShowNew(true)}>
          + Add payment method
        </Button>
      )}
    </section>
  )
}

function PaymentMethodRow({ method, onSaved }: { method: PaymentMethod; onSaved: () => void }) {
  const [label, setLabel] = useState(method.label)
  const [code, setCode] = useState(method.code)
  const [kind, setKind] = useState<PaymentMethodKind>(method.kind)
  const [isActive, setIsActive] = useState(method.is_active)
  const [error, setError] = useState<string | null>(null)

  const dirty =
    label !== method.label ||
    code !== method.code ||
    kind !== method.kind ||
    isActive !== method.is_active

  const mutation = useMutation({
    mutationFn: () => updatePaymentMethod(method.id, {
      label,
      code,
      kind,
      is_active: isActive,
    }),
    onSuccess: () => { setError(null); onSaved() },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Save failed'),
  })

  return (
    <div className={`border rounded-md px-3 py-2.5 grid grid-cols-12 gap-2 items-center ${!isActive ? 'opacity-60' : ''}`}>
      <input
        value={label}
        onChange={e => setLabel(e.target.value)}
        className="col-span-4 border border-input rounded px-2 py-1 text-sm bg-background"
        placeholder="Label"
      />
      <input
        value={code}
        onChange={e => setCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
        className="col-span-2 border border-input rounded px-2 py-1 text-sm bg-background font-mono"
        placeholder="code"
      />
      <select
        value={kind}
        onChange={e => setKind(e.target.value as PaymentMethodKind)}
        className="col-span-2 border border-input rounded px-2 py-1 text-sm bg-background"
      >
        {KIND_OPTIONS.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      <label className="col-span-2 flex items-center gap-1.5 text-xs text-muted-foreground">
        <input
          type="checkbox"
          checked={isActive}
          onChange={e => setIsActive(e.target.checked)}
          className="h-3.5 w-3.5"
        />
        Active
      </label>
      <Button
        size="sm"
        variant="outline"
        className="col-span-2"
        disabled={!dirty || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? 'Saving…' : 'Save'}
      </Button>
      {error && <p className="col-span-12 text-xs text-destructive">{error}</p>}
    </div>
  )
}

function NewPaymentMethodForm({ onCancel, onSaved }: { onCancel: () => void; onSaved: () => void }) {
  const [label, setLabel] = useState('')
  const [code, setCode] = useState('')
  const [kind, setKind] = useState<PaymentMethodKind>('card')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => createPaymentMethod({ label, code, kind }),
    onSuccess: () => { setError(null); onSaved() },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Failed to add'),
  })

  function submit() {
    if (!label.trim()) { setError('Label required'); return }
    if (!code.trim()) { setError('Code required'); return }
    setError(null)
    mutation.mutate()
  }

  return (
    <div className="border border-dashed rounded-md px-3 py-3 space-y-2 bg-muted/20">
      <p className="text-xs font-medium text-muted-foreground">New payment method</p>
      <div className="grid grid-cols-12 gap-2 items-center">
        <input
          value={label}
          onChange={e => {
            setLabel(e.target.value)
            if (!code) setCode(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '_'))
          }}
          placeholder="Label (e.g. Apple Pay)"
          className="col-span-4 border border-input rounded px-2 py-1 text-sm bg-background"
        />
        <input
          value={code}
          onChange={e => setCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
          placeholder="code"
          className="col-span-3 border border-input rounded px-2 py-1 text-sm bg-background font-mono"
        />
        <select
          value={kind}
          onChange={e => setKind(e.target.value as PaymentMethodKind)}
          className="col-span-3 border border-input rounded px-2 py-1 text-sm bg-background"
        >
          {KIND_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <Button size="sm" className="col-span-1" onClick={submit} disabled={mutation.isPending}>
          {mutation.isPending ? '…' : 'Add'}
        </Button>
        <Button size="sm" variant="ghost" className="col-span-1" onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

function PromotionsSection() {
  const qc = useQueryClient()
  const [adding, setAdding] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newLabel, setNewLabel] = useState('')
  const [newKind, setNewKind] = useState<PromotionKind>('percent')
  const [newValue, setNewValue] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const { data: promos = [], isLoading } = useQuery({
    queryKey: ['promotions'],
    queryFn: () => listPromotions(false),
  })

  const createMutation = useMutation({
    mutationFn: () => createPromotion({
      code: newCode.trim(), label: newLabel.trim(),
      kind: newKind, value: newValue,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['promotions'] })
      setAdding(false)
      setNewCode(''); setNewLabel(''); setNewValue(''); setFormError(null)
    },
    onError: (e: Error) => setFormError(e.message),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updatePromotion(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['promotions'] }),
  })

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    if (!newCode.trim() || !newLabel.trim() || !newValue) {
      setFormError('All fields required')
      return
    }
    createMutation.mutate()
  }

  return (
    <section className="border rounded-lg bg-white overflow-hidden">
      <div className="px-5 py-3 border-b bg-muted/30 flex items-center justify-between">
        <h2 className="text-sm font-medium">Promotions</h2>
        {!adding && (
          <Button size="sm" variant="outline" onClick={() => setAdding(true)}>+ Add</Button>
        )}
      </div>
      <div className="p-5 space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : promos.length === 0 && !adding ? (
          <p className="text-sm text-muted-foreground">No promotions yet.</p>
        ) : (
          <ul className="space-y-2">
            {promos.map(p => (
              <li key={p.id} className={`flex items-center justify-between rounded-md border px-3 py-2 text-sm ${!p.is_active ? 'opacity-50' : ''}`}>
                <div>
                  <span className="font-medium">{p.label}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {p.kind === 'percent' ? `${p.value}% off` : `$${p.value} off`} · code: {p.code}
                  </span>
                </div>
                <button
                  onClick={() => toggleMutation.mutate({ id: p.id, is_active: !p.is_active })}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  {p.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </li>
            ))}
          </ul>
        )}

        {adding && (
          <form onSubmit={handleAdd} className="space-y-3 border rounded-md p-3 bg-muted/20">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Label</Label>
                <Input value={newLabel} onChange={e => setNewLabel(e.target.value)} placeholder="Senior Tuesday" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Code</Label>
                <Input value={newCode} onChange={e => setNewCode(e.target.value)} placeholder="SENIOR_TUE" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Type</Label>
                <select
                  value={newKind}
                  onChange={e => setNewKind(e.target.value as PromotionKind)}
                  className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background"
                >
                  <option value="percent">Percent (%)</option>
                  <option value="amount">Fixed amount ($)</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Value</Label>
                <Input
                  type="text"
                  inputMode="decimal"
                  value={newValue}
                  onChange={e => setNewValue(e.target.value)}
                  placeholder={newKind === 'percent' ? '10' : '5.00'}
                />
              </div>
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Saving…' : 'Save'}
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => { setAdding(false); setFormError(null) }}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </div>
    </section>
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
          <Save size={14} className="mr-1.5" />
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

function RequestNotificationsSection() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['request-notifications'],
    queryFn: getRequestNotifications,
  })

  const [enabled, setEnabled] = useState(true)
  const [recipientsText, setRecipientsText] = useState('')
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedMsg, setSavedMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) {
      setEnabled(data.enabled)
      setRecipientsText(data.recipients.join('\n'))
      setDirty(false)
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: () => {
      const recipients = recipientsText
        .split(/[\n,]/)
        .map(r => r.trim())
        .filter(Boolean)
      return updateRequestNotifications({ enabled, recipients })
    },
    onSuccess: updated => {
      qc.setQueryData(['request-notifications'], updated)
      setRecipientsText(updated.recipients.join('\n'))
      setDirty(false)
      setError(null)
      setSavedMsg('Saved.')
      setTimeout(() => setSavedMsg(null), 3000)
    },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Save failed'),
  })

  if (isLoading) return null

  return (
    <section className="border rounded-lg p-5 space-y-4 bg-white">
      <div>
        <h2 className="text-base font-medium">Booking-request notifications</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Email the salon when a guest submits a booking request through the public form.
          Independent of the SMTP configuration above — uses the same outbound credentials.
        </p>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={enabled}
          onChange={e => { setEnabled(e.target.checked); setDirty(true) }}
          className="h-4 w-4"
        />
        <span className="text-sm">Send notifications when a new request is submitted</span>
      </label>

      <div className="space-y-1.5">
        <Label htmlFor="recipients">Recipient emails</Label>
        <textarea
          id="recipients"
          value={recipientsText}
          onChange={e => { setRecipientsText(e.target.value); setDirty(true) }}
          rows={3}
          placeholder="bookings@salonlyol.ca&#10;manager@salonlyol.ca"
          className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none font-mono"
        />
        <p className="text-xs text-muted-foreground">
          One per line (or comma-separated). Leave blank to disable notifications even when the toggle is on.
        </p>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      <div className="flex items-center gap-3">
        <Button onClick={() => mutation.mutate()} disabled={!dirty || mutation.isPending}>
          <Save size={14} className="mr-1.5" />
          {mutation.isPending ? 'Saving…' : 'Save'}
        </Button>
        {savedMsg && <span className="text-sm text-green-600">{savedMsg}</span>}
      </div>
    </section>
  )
}
