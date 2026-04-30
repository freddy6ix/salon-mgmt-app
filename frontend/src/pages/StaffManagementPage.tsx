import { useState } from 'react'
import { format } from 'date-fns'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, UserCircle2, CheckCircle2, XCircle } from 'lucide-react'
import {
  listAllProviders,
  createProvider,
  updateProvider,
  deactivateProvider,
  getProviderPayroll,
  type ProviderDetail,
  type CommissionTier,
} from '@/api/providers'
import { listUsers } from '@/api/admin'
import { getWeeklySchedules, setWeeklySchedule, type DayHours } from '@/api/schedules'
import { getOperatingHours, type OperatingHoursDay } from '@/api/settings'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

// ── Types ─────────────────────────────────────────────────────────────────────

type Tab = 'profile' | 'compensation' | 'hr' | 'schedule' | 'payroll'

// ── Helpers ───────────────────────────────────────────────────────────────────

const TODAY = format(new Date(), 'yyyy-MM-dd')
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

type SalonHoursMap = Record<number, { open: string; close: string } | null>

function buildSalonHours(rows: OperatingHoursDay[]): SalonHoursMap {
  const map: SalonHoursMap = { 0: null, 1: null, 2: null, 3: null, 4: null, 5: null, 6: null }
  for (const r of rows) {
    map[r.day_of_week] = r.is_open && r.open_time && r.close_time
      ? { open: r.open_time, close: r.close_time }
      : null
  }
  return map
}

function clamp(value: string, min: string, max: string): string {
  if (value < min) return min
  if (value > max) return max
  return value
}

function typeBadge(type: string) {
  const colors: Record<string, string> = {
    stylist: 'bg-blue-100 text-blue-700',
    colourist: 'bg-purple-100 text-purple-700',
    dualist: 'bg-emerald-100 text-emerald-700',
  }
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded capitalize ${colors[type] ?? 'bg-muted text-muted-foreground'}`}>
      {type}
    </span>
  )
}

function fieldRow(label: string, children: React.ReactNode) {
  return (
    <div className="grid grid-cols-3 gap-4 items-start py-2 border-b last:border-0">
      <Label className="text-sm text-muted-foreground pt-2">{label}</Label>
      <div className="col-span-2">{children}</div>
    </div>
  )
}

function sectionTitle(title: string) {
  return <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mt-6 mb-2 first:mt-0">{title}</h3>
}

// ── Schedule Tab ──────────────────────────────────────────────────────────────

function ScheduleTab({ providerId }: { providerId: string }) {
  const qc = useQueryClient()
  const [saving, setSaving] = useState(false)
  const [effectiveFrom, setEffectiveFrom] = useState(TODAY)
  const [dirty, setDirty] = useState(false)

  const { data: allSchedules = [], isLoading: schedLoading } = useQuery({
    queryKey: ['schedules-weekly'],
    queryFn: getWeeklySchedules,
  })
  const { data: operatingHours = [], isLoading: hoursLoading } = useQuery({
    queryKey: ['operating-hours'],
    queryFn: getOperatingHours,
  })

  const salonHours = buildSalonHours(operatingHours)
  const providerSchedule = allSchedules.find(s => s.provider_id === providerId)

  const [days, setDaysState] = useState<DayHours[] | null>(null)

  const resolvedDays: DayHours[] = days ?? (providerSchedule?.days.map(d => {
    const salon = salonHours[d.day_of_week]
    if (!d.has_schedule && salon) {
      return { ...d, is_working: true, start_time: salon.open, end_time: salon.close }
    }
    return { ...d }
  }) ?? Array.from({ length: 7 }, (_, i) => ({
    day_of_week: i, is_working: false, start_time: null, end_time: null,
  })))

  function updateDay(dow: number, patch: Partial<DayHours>) {
    setDaysState(prev => (prev ?? resolvedDays).map(d => d.day_of_week === dow ? { ...d, ...patch } : d))
    setDirty(true)
  }

  function toggleWorking(dow: number, isWorking: boolean) {
    const salon = salonHours[dow]
    if (isWorking && salon) {
      updateDay(dow, { is_working: true, start_time: salon.open, end_time: salon.close })
    } else {
      updateDay(dow, { is_working: isWorking, start_time: null, end_time: null })
    }
  }

  async function handleSave() {
    setSaving(true)
    try {
      await setWeeklySchedule(providerId, resolvedDays, effectiveFrom)
      qc.invalidateQueries({ queryKey: ['schedules-weekly'] })
      qc.invalidateQueries({ queryKey: ['schedules'] })
      setDirty(false)
    } finally {
      setSaving(false)
    }
  }

  if (schedLoading || hoursLoading) {
    return <p className="text-sm text-muted-foreground">Loading schedule…</p>
  }

  return (
    <div className="space-y-4">
      <div className="overflow-auto">
        <table className="text-sm border-collapse">
          <thead>
            <tr className="border-b bg-muted/30">
              {DAY_NAMES.map(d => (
                <th key={d} className="px-3 py-2 text-left text-xs font-medium text-muted-foreground min-w-[120px]">{d}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {resolvedDays.map(day => {
                const salon = salonHours[day.day_of_week]
                const salonClosed = salon === null
                return (
                  <td key={day.day_of_week} className="px-3 py-3 align-top border-b">
                    {salonClosed ? (
                      <span className="text-xs text-muted-foreground">Closed</span>
                    ) : (
                      <div className="flex flex-col gap-1.5">
                        <label className="flex items-center gap-1.5 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={day.is_working}
                            onChange={e => toggleWorking(day.day_of_week, e.target.checked)}
                            className="accent-primary"
                          />
                          <span className="text-xs">{day.is_working ? 'Working' : 'Off'}</span>
                        </label>
                        {day.is_working && (
                          <div className="flex flex-col gap-1">
                            <input
                              type="time"
                              value={day.start_time ?? ''}
                              min={salon.open}
                              max={day.end_time ?? salon.close}
                              onChange={e => updateDay(day.day_of_week, {
                                start_time: clamp(e.target.value, salon.open, day.end_time ?? salon.close),
                              })}
                              className="text-xs border border-input rounded px-1 py-0.5 w-[80px] bg-background"
                            />
                            <input
                              type="time"
                              value={day.end_time ?? ''}
                              min={day.start_time ?? salon.open}
                              max={salon.close}
                              onChange={e => updateDay(day.day_of_week, {
                                end_time: clamp(e.target.value, day.start_time ?? salon.open, salon.close),
                              })}
                              className="text-xs border border-input rounded px-1 py-0.5 w-[80px] bg-background"
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                )
              })}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">Effective from</label>
          <input
            type="date"
            value={effectiveFrom}
            min={TODAY}
            onChange={e => { setEffectiveFrom(e.target.value); setDirty(true) }}
            className="text-xs border border-input rounded px-2 py-1 bg-background"
          />
        </div>
        <Button size="sm" disabled={!dirty || saving} onClick={handleSave}>
          {saving ? 'Saving…' : 'Save Schedule'}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">
        Provider hours must fall within salon operating hours. Past schedules are locked.
      </p>
    </div>
  )
}

// ── Profile Tab ───────────────────────────────────────────────────────────────

function ProfileTab({ provider }: { provider: ProviderDetail }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    first_name: provider.first_name,
    last_name: provider.last_name,
    display_name: provider.display_name,
    provider_type: provider.provider_type,
    job_title: provider.job_title ?? '',
    provider_code: provider.provider_code ?? '',
    is_owner: provider.is_owner,
    is_active: provider.is_active,
    booking_order: provider.booking_order,
    has_appointments: provider.has_appointments,
    makes_appointments: provider.makes_appointments,
    can_be_cashier: provider.can_be_cashier,
    online_booking_visibility: provider.online_booking_visibility,
    sex: provider.sex ?? '',
    personal_email: provider.personal_email ?? '',
    cell_phone: provider.cell_phone ?? '',
    home_phone: provider.home_phone ?? '',
    other_phone: provider.other_phone ?? '',
    address_line: provider.address_line ?? '',
    city: provider.city ?? '',
    province: provider.province ?? '',
    postal_code: provider.postal_code ?? '',
    birthday: provider.birthday ?? '',
    notes: provider.notes ?? '',
    provider_photo_url: provider.provider_photo_url ?? '',
    user_id: provider.user_id ?? '',
  })

  const { data: users = [] } = useQuery({
    queryKey: ['admin-users'],
    queryFn: listUsers,
  })

  const mutation = useMutation({
    mutationFn: () => updateProvider(provider.id, {
      ...form,
      job_title: form.job_title || null,
      provider_code: form.provider_code || null,
      sex: form.sex || null,
      personal_email: form.personal_email || null,
      cell_phone: form.cell_phone || null,
      home_phone: form.home_phone || null,
      other_phone: form.other_phone || null,
      address_line: form.address_line || null,
      city: form.city || null,
      province: form.province || null,
      postal_code: form.postal_code || null,
      birthday: form.birthday || null,
      notes: form.notes || null,
      provider_photo_url: form.provider_photo_url || null,
      user_id: form.user_id || null,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers-all'] }),
  })

  function set(field: string, value: string | boolean | number) {
    setForm(f => ({ ...f, [field]: value }))
  }

  return (
    <div className="max-w-2xl space-y-1">
      {sectionTitle('Identity')}
      {fieldRow('First name', <Input value={form.first_name} onChange={e => set('first_name', e.target.value)} />)}
      {fieldRow('Last name', <Input value={form.last_name} onChange={e => set('last_name', e.target.value)} />)}
      {fieldRow('Display name', <Input value={form.display_name} onChange={e => set('display_name', e.target.value)} />)}
      {fieldRow('Job title', <Input value={form.job_title} onChange={e => set('job_title', e.target.value)} placeholder="e.g. Senior Stylist" />)}
      {fieldRow('Type', (
        <select
          value={form.provider_type}
          onChange={e => set('provider_type', e.target.value)}
          className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
        >
          <option value="stylist">Stylist</option>
          <option value="colourist">Colourist</option>
          <option value="dualist">Dualist</option>
        </select>
      ))}
      {fieldRow('Provider code', <Input value={form.provider_code} onChange={e => set('provider_code', e.target.value)} placeholder="e.g. GUMI" />)}
      {fieldRow('Login account', (
        <div className="space-y-1">
          <select
            value={form.user_id}
            onChange={e => set('user_id', e.target.value)}
            className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
          >
            <option value="">— Not linked —</option>
            {users.filter(u => u.role !== 'guest' && u.is_active).map(u => (
              <option key={u.id} value={u.id}>{u.email} ({u.role})</option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">Links this provider profile to a staff login account</p>
        </div>
      ))}
      {fieldRow('Photo URL', (
        <div className="space-y-1">
          <Input value={form.provider_photo_url} onChange={e => set('provider_photo_url', e.target.value)} placeholder="https://…" />
          {form.provider_photo_url && (
            <img src={form.provider_photo_url} alt="preview" className="h-16 w-16 rounded-full object-cover mt-1" onError={e => { e.currentTarget.style.display = 'none' }} />
          )}
        </div>
      ))}

      {sectionTitle('Personal')}
      {fieldRow('Sex', (
        <select
          value={form.sex}
          onChange={e => set('sex', e.target.value)}
          className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
        >
          <option value="">—</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option>
          <option value="Non-binary">Non-binary</option>
          <option value="Prefer not to say">Prefer not to say</option>
        </select>
      ))}
      {fieldRow('Birthday', <Input type="date" value={form.birthday} onChange={e => set('birthday', e.target.value)} />)}
      {fieldRow('Personal email', <Input type="email" value={form.personal_email} onChange={e => set('personal_email', e.target.value)} />)}
      {fieldRow('Cell phone', <Input value={form.cell_phone} onChange={e => set('cell_phone', e.target.value)} />)}
      {fieldRow('Home phone', <Input value={form.home_phone} onChange={e => set('home_phone', e.target.value)} />)}
      {fieldRow('Address', <Input value={form.address_line} onChange={e => set('address_line', e.target.value)} />)}
      {fieldRow('City', <Input value={form.city} onChange={e => set('city', e.target.value)} />)}
      {fieldRow('Province', <Input value={form.province} onChange={e => set('province', e.target.value)} maxLength={2} placeholder="ON" />)}
      {fieldRow('Postal code', <Input value={form.postal_code} onChange={e => set('postal_code', e.target.value)} />)}
      {fieldRow('Notes', (
        <textarea
          value={form.notes}
          onChange={e => set('notes', e.target.value)}
          rows={3}
          className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
        />
      ))}

      {sectionTitle('Booking')}
      {fieldRow('Booking order', <Input type="number" value={form.booking_order} onChange={e => set('booking_order', parseInt(e.target.value) || 0)} className="w-24" />)}
      {fieldRow('Online booking', (
        <select
          value={form.online_booking_visibility}
          onChange={e => set('online_booking_visibility', e.target.value)}
          className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
        >
          <option value="not_available">Not available</option>
          <option value="available_to_my_clients">My clients only</option>
          <option value="available_to_all">Available to all</option>
        </select>
      ))}
      {fieldRow('Flags', (
        <div className="flex flex-wrap gap-4 text-sm">
          {([
            ['has_appointments', 'Has appointments'],
            ['makes_appointments', 'Makes appointments'],
            ['can_be_cashier', 'Can be cashier'],
            ['is_owner', 'Owner'],
            ['is_active', 'Active'],
          ] as [string, string][]).map(([field, label]) => (
            <label key={field} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form[field as keyof typeof form] as boolean}
                onChange={e => set(field, e.target.checked)}
                className="accent-primary"
              />
              {label}
            </label>
          ))}
        </div>
      ))}

      <div className="pt-4">
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving…' : 'Save Profile'}
        </Button>
        {mutation.isSuccess && <span className="ml-3 text-sm text-emerald-600">Saved</span>}
      </div>
    </div>
  )
}

// ── Compensation Tab ──────────────────────────────────────────────────────────

const DEFAULT_TIERS: CommissionTier[] = [
  { monthly_threshold: 5000, rate_pct: 50 },
  { monthly_threshold: 5833, rate_pct: 55 },
  { monthly_threshold: 6666, rate_pct: 60 },
  { monthly_threshold: 7500, rate_pct: 65 },
  { monthly_threshold: 8333, rate_pct: 70 },
]

function CompensationTab({ provider }: { provider: ProviderDetail }) {
  const qc = useQueryClient()
  const [payType, setPayType] = useState(provider.pay_type ?? '')
  const [payAmount, setPayAmount] = useState(String(provider.pay_amount ?? ''))
  const [hourlyMin, setHourlyMin] = useState(String(provider.hourly_minimum ?? ''))
  const [vacationPct, setVacationPct] = useState(String(provider.vacation_pct ?? '4'))
  const [retailPct, setRetailPct] = useState(String(provider.retail_commission_pct ?? '10'))
  const [tiers, setTiers] = useState<CommissionTier[]>(
    provider.commission_tiers ?? DEFAULT_TIERS
  )
  const [stylingFee, setStylingFee] = useState(String(provider.product_fee_styling_flat ?? ''))
  const [colourPct, setColourPct] = useState(String(provider.product_fee_colour_pct ?? ''))

  function updateTier(idx: number, field: keyof CommissionTier, value: string) {
    setTiers(prev => prev.map((t, i) => i === idx ? { ...t, [field]: parseFloat(value) || 0 } : t))
  }

  function addTier() {
    setTiers(prev => [...prev, { monthly_threshold: 0, rate_pct: 0 }])
  }

  function removeTier(idx: number) {
    setTiers(prev => prev.filter((_, i) => i !== idx))
  }

  const mutation = useMutation({
    mutationFn: () => updateProvider(provider.id, {
      pay_type: payType || null,
      pay_amount: payAmount ? parseFloat(payAmount) : null,
      hourly_minimum: hourlyMin ? parseFloat(hourlyMin) : null,
      vacation_pct: vacationPct ? parseFloat(vacationPct) : null,
      retail_commission_pct: retailPct ? parseFloat(retailPct) : null,
      commission_tiers: payType === 'commission' ? tiers : null,
      product_fee_styling_flat: stylingFee ? parseFloat(stylingFee) : null,
      product_fee_colour_pct: colourPct ? parseFloat(colourPct) : null,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers-all'] }),
  })

  return (
    <div className="max-w-2xl space-y-1">
      {sectionTitle('Pay Structure')}
      {fieldRow('Pay type', (
        <select
          value={payType}
          onChange={e => setPayType(e.target.value)}
          className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
        >
          <option value="">— Not set —</option>
          <option value="hourly">Hourly</option>
          <option value="salary">Salary</option>
          <option value="commission">Commission (with hourly floor)</option>
        </select>
      ))}

      {payType === 'hourly' && fieldRow('Hourly rate ($)', (
        <Input type="number" step="0.01" value={payAmount} onChange={e => setPayAmount(e.target.value)} className="w-32" />
      ))}

      {payType === 'salary' && fieldRow('Salary ($)', (
        <Input type="number" step="0.01" value={payAmount} onChange={e => setPayAmount(e.target.value)} className="w-40" />
      ))}

      {payType === 'commission' && (
        <>
          {fieldRow('Hourly floor ($)', (
            <div className="space-y-1">
              <Input type="number" step="0.01" value={hourlyMin} onChange={e => setHourlyMin(e.target.value)} className="w-32" />
              <p className="text-xs text-muted-foreground">Minimum guaranteed rate; commission pays if higher</p>
            </div>
          ))}

          {sectionTitle('Commission Brackets')}
          <p className="text-xs text-muted-foreground mb-3">
            Based on annualized monthly net service revenue. The highest bracket the provider's revenue meets applies.
          </p>
          <div className="border rounded-md overflow-hidden mb-2">
            <table className="w-full text-sm">
              <thead className="bg-muted/30">
                <tr>
                  <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground">Monthly threshold ($)</th>
                  <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground">Commission rate (%)</th>
                  <th className="w-10" />
                </tr>
              </thead>
              <tbody>
                {tiers.map((tier, idx) => (
                  <tr key={idx} className="border-t">
                    <td className="px-3 py-2">
                      <Input
                        type="number"
                        value={tier.monthly_threshold}
                        onChange={e => updateTier(idx, 'monthly_threshold', e.target.value)}
                        className="w-28 h-7 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        type="number"
                        value={tier.rate_pct}
                        onChange={e => updateTier(idx, 'rate_pct', e.target.value)}
                        className="w-20 h-7 text-xs"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <button
                        onClick={() => removeTier(idx)}
                        className="text-muted-foreground hover:text-destructive text-xs px-1"
                      >
                        ×
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Button variant="ghost" size="sm" onClick={addTier}>
            <Plus size={14} className="mr-1" /> Add bracket
          </Button>

          {sectionTitle('Product Fees')}
          <p className="text-xs text-muted-foreground mb-3">
            Deducted from service revenue before applying the commission rate.
          </p>
          {fieldRow('Styling fee ($ flat)', (
            <div className="space-y-1">
              <Input type="number" step="0.01" value={stylingFee} onChange={e => setStylingFee(e.target.value)} className="w-32" placeholder="e.g. 5.00" />
              <p className="text-xs text-muted-foreground">Per styling service appointment</p>
            </div>
          ))}
          {fieldRow('Colour fee (% of revenue)', (
            <div className="space-y-1">
              <Input type="number" step="0.1" value={colourPct} onChange={e => setColourPct(e.target.value)} className="w-32" placeholder="e.g. 10" />
              <p className="text-xs text-muted-foreground">% of pre-tax colour service revenue</p>
            </div>
          ))}
        </>
      )}

      {sectionTitle('Other')}
      {fieldRow('Vacation pay (%)', (
        <div className="space-y-1">
          <Input type="number" step="0.1" value={vacationPct} onChange={e => setVacationPct(e.target.value)} className="w-24" />
          <p className="text-xs text-muted-foreground">Added each pay period (e.g. 4% per Ontario ESA minimum)</p>
        </div>
      ))}
      {fieldRow('Retail commission (%)', (
        <div className="space-y-1">
          <Input type="number" step="0.1" value={retailPct} onChange={e => setRetailPct(e.target.value)} className="w-24" />
          <p className="text-xs text-muted-foreground">% of retail product revenue (pre-tax)</p>
        </div>
      ))}

      <div className="pt-4">
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving…' : 'Save Compensation'}
        </Button>
        {mutation.isSuccess && <span className="ml-3 text-sm text-emerald-600">Saved</span>}
      </div>
    </div>
  )
}

// ── HR & Banking Tab ──────────────────────────────────────────────────────────

function HRBankingTab({ provider }: { provider: ProviderDetail }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    hire_date: provider.hire_date ?? '',
    first_day_worked: provider.first_day_worked ?? '',
    certification: provider.certification ?? '',
    sin: '',
    bank_institution_no: provider.bank_institution_no ?? '',
    bank_transit_no: provider.bank_transit_no ?? '',
    bank_account_no: '',
    cpp_exempt: provider.cpp_exempt ?? false,
    ei_exempt: provider.ei_exempt ?? false,
    ei_rate_type: provider.ei_rate_type ?? 'normal',
    province_of_taxation: provider.province_of_taxation ?? '',
    wcb_csst_exempt: provider.wcb_csst_exempt ?? false,
    td1_federal_credit: String(provider.td1_federal_credit ?? ''),
    td1_provincial_credit: String(provider.td1_provincial_credit ?? ''),
  })

  function set(field: string, value: string | boolean) {
    setForm(f => ({ ...f, [field]: value }))
  }

  const mutation = useMutation({
    mutationFn: () => updateProvider(provider.id, {
      hire_date: form.hire_date || null,
      first_day_worked: form.first_day_worked || null,
      certification: form.certification || null,
      sin: form.sin || undefined,
      bank_institution_no: form.bank_institution_no || null,
      bank_transit_no: form.bank_transit_no || null,
      bank_account_no: form.bank_account_no || undefined,
      cpp_exempt: form.cpp_exempt,
      ei_exempt: form.ei_exempt,
      ei_rate_type: form.ei_rate_type || null,
      province_of_taxation: form.province_of_taxation || null,
      wcb_csst_exempt: form.wcb_csst_exempt,
      td1_federal_credit: form.td1_federal_credit ? parseFloat(form.td1_federal_credit) : null,
      td1_provincial_credit: form.td1_provincial_credit ? parseFloat(form.td1_provincial_credit) : null,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers-all'] }),
  })

  return (
    <div className="max-w-2xl space-y-1">
      {sectionTitle('Employment')}
      {fieldRow('Hire date', <Input type="date" value={form.hire_date} onChange={e => set('hire_date', e.target.value)} />)}
      {fieldRow('First day worked', <Input type="date" value={form.first_day_worked} onChange={e => set('first_day_worked', e.target.value)} />)}
      {fieldRow('Certification', (
        <div className="space-y-1">
          <Input value={form.certification} onChange={e => set('certification', e.target.value)} placeholder="e.g. Ontario College of Trades" />
        </div>
      ))}
      {fieldRow('SIN', (
        <div className="space-y-1">
          <Input
            type="password"
            value={form.sin}
            onChange={e => set('sin', e.target.value)}
            placeholder={provider.sin_set ? '••• stored — enter to update' : 'Enter SIN to store'}
            autoComplete="off"
          />
          <p className="text-xs text-muted-foreground">Leave blank to keep current value. Stored encrypted.</p>
        </div>
      ))}

      {sectionTitle('Banking (Direct Deposit)')}
      {fieldRow('Institution # (3 digits)', <Input value={form.bank_institution_no} onChange={e => set('bank_institution_no', e.target.value)} maxLength={3} className="w-24" />)}
      {fieldRow('Transit # (5 digits)', <Input value={form.bank_transit_no} onChange={e => set('bank_transit_no', e.target.value)} maxLength={5} className="w-28" />)}
      {fieldRow('Account number', (
        <div className="space-y-1">
          <Input
            type="password"
            value={form.bank_account_no}
            onChange={e => set('bank_account_no', e.target.value)}
            placeholder={provider.bank_account_masked ? `••• ${provider.bank_account_masked} — enter to update` : 'Enter account number to store'}
            autoComplete="off"
          />
          <p className="text-xs text-muted-foreground">Leave blank to keep current value. Stored encrypted.</p>
        </div>
      ))}

      {sectionTitle('Tax (Paytrak)')}
      {fieldRow('Province of taxation', (
        <Input value={form.province_of_taxation} onChange={e => set('province_of_taxation', e.target.value)} maxLength={2} placeholder="ON" className="w-20" />
      ))}
      {fieldRow('CPP exempt', (
        <label className="flex items-center gap-2 cursor-pointer text-sm">
          <input type="checkbox" checked={form.cpp_exempt} onChange={e => set('cpp_exempt', e.target.checked)} className="accent-primary" />
          Yes
        </label>
      ))}
      {fieldRow('EI exempt', (
        <label className="flex items-center gap-2 cursor-pointer text-sm">
          <input type="checkbox" checked={form.ei_exempt} onChange={e => set('ei_exempt', e.target.checked)} className="accent-primary" />
          Yes
        </label>
      ))}
      {fieldRow('EI rate type', (
        <select
          value={form.ei_rate_type}
          onChange={e => set('ei_rate_type', e.target.value)}
          className="border border-input rounded-md px-3 py-2 text-sm bg-background"
        >
          <option value="normal">Normal</option>
          <option value="reduced">Reduced</option>
        </select>
      ))}
      {fieldRow('WCB / CSST exempt', (
        <label className="flex items-center gap-2 cursor-pointer text-sm">
          <input type="checkbox" checked={form.wcb_csst_exempt} onChange={e => set('wcb_csst_exempt', e.target.checked)} className="accent-primary" />
          Yes
        </label>
      ))}
      {fieldRow('TD1 federal credit ($)', (
        <Input type="number" step="0.01" value={form.td1_federal_credit} onChange={e => set('td1_federal_credit', e.target.value)} className="w-36" />
      ))}
      {fieldRow('TD1 provincial credit ($)', (
        <Input type="number" step="0.01" value={form.td1_provincial_credit} onChange={e => set('td1_provincial_credit', e.target.value)} className="w-36" />
      ))}

      <div className="pt-4">
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving…' : 'Save HR & Banking'}
        </Button>
        {mutation.isSuccess && <span className="ml-3 text-sm text-emerald-600">Saved</span>}
      </div>
    </div>
  )
}

// ── Payroll Tab ───────────────────────────────────────────────────────────────

const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December']

function fmt(n: number) {
  return n.toLocaleString('en-CA', { style: 'currency', currency: 'CAD', minimumFractionDigits: 2 })
}

function PayrollTab({ provider }: { provider: ProviderDetail }) {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['provider-payroll', provider.id, year, month],
    queryFn: () => getProviderPayroll(provider.id, year, month),
    enabled: !!provider.pay_type,
  })

  if (!provider.pay_type) {
    return (
      <div className="text-sm text-muted-foreground">
        Pay type not configured. Set it in the Compensation tab first.
      </div>
    )
  }

  function row(label: string, value: React.ReactNode, bold = false) {
    return (
      <tr className={`border-b last:border-0 ${bold ? 'font-semibold' : ''}`}>
        <td className="py-2 pr-8 text-sm text-muted-foreground">{label}</td>
        <td className="py-2 text-sm text-right">{value}</td>
      </tr>
    )
  }

  function section(title: string) {
    return (
      <tr>
        <td colSpan={2} className="pt-5 pb-1">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{title}</span>
        </td>
      </tr>
    )
  }

  return (
    <div className="max-w-lg">
      {/* Period picker */}
      <div className="flex items-center gap-3 mb-6">
        <select
          value={month}
          onChange={e => setMonth(parseInt(e.target.value))}
          className="border border-input rounded-md px-3 py-1.5 text-sm bg-background"
        >
          {MONTH_NAMES.map((n, i) => <option key={i+1} value={i+1}>{n}</option>)}
        </select>
        <Input
          type="number"
          value={year}
          onChange={e => setYear(parseInt(e.target.value) || year)}
          className="w-24 h-8 text-sm"
        />
        <span className="text-xs text-muted-foreground">Pay period: {MONTH_NAMES[month-1]} {year}</span>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Calculating…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          {(error as Error)?.message ?? 'Could not load payroll data'}
        </p>
      )}

      {data && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-muted/30 px-4 py-3 border-b flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{data.display_name} — {MONTH_NAMES[data.month - 1]} {data.year}</p>
              <p className="text-xs text-muted-foreground capitalize">{data.pay_type} pay</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-semibold">{fmt(data.gross_pay)}</p>
              <p className="text-xs text-muted-foreground">Gross incl. vacation</p>
            </div>
          </div>

          <table className="w-full px-4">
            <tbody className="px-4">
              <tr><td className="w-4" /><td /></tr>

              {section('Hours')}
              {row('Scheduled hours', `${data.scheduled_hours} h`)}
              {data.hourly_minimum && row(`Hourly floor (${data.scheduled_hours} h × ${fmt(data.hourly_minimum)})`, fmt(data.hourly_floor_amount))}

              {data.pay_type === 'commission' && (
                <>
                  {section('Service Revenue')}
                  {row(`Styling / other (${data.styling_item_count} items)`, fmt(data.styling_revenue))}
                  {row(`Colour (${data.colour_item_count} items)`, fmt(data.colour_revenue))}
                  {row('Gross service revenue', fmt(data.gross_service_revenue), true)}

                  {section('Product Fees')}
                  {data.styling_product_fee > 0 && row(`Styling (${data.styling_item_count} × flat fee)`, `(${fmt(data.styling_product_fee)})`)}
                  {data.colour_product_fee > 0 && row(`Colour (${data.commission_tier_applied?.rate_pct ?? 0}% of colour revenue)`, `(${fmt(data.colour_product_fee)})`)}
                  {row('Net service revenue', fmt(data.net_service_revenue), true)}

                  {section('Commission')}
                  {data.commission_tier_applied
                    ? row(`Rate: ${data.commission_tier_applied.rate_pct}% (threshold ${fmt(data.commission_tier_applied.monthly_threshold)}/mo)`, fmt(data.commission_on_services))
                    : row('Commission on services (no tier matched)', fmt(data.commission_on_services))
                  }
                  {row(`Retail (${fmt(data.retail_revenue)} × ${data.commission_tier_applied ? '' : ''}${provider.retail_commission_pct ?? 10}%)`, fmt(data.retail_commission))}
                  {row('Total commission pay', fmt(data.total_commission_pay), true)}

                  {section('Pay Basis')}
                  {row(
                    data.pay_basis === 'commission'
                      ? 'Commission exceeds hourly floor — commission applies'
                      : 'Hourly floor exceeds commission — floor applies',
                    fmt(data.gross_before_vacation),
                    true,
                  )}
                </>
              )}

              {data.pay_type === 'hourly' && (
                <>
                  {section('Pay')}
                  {row('Hourly pay', fmt(data.hourly_floor_amount), true)}
                </>
              )}

              {data.pay_type === 'salary' && (
                <>
                  {section('Pay')}
                  {row('Monthly salary', fmt(data.gross_before_vacation), true)}
                </>
              )}

              {section('Vacation Pay')}
              {row(`${data.vacation_pct}% of ${fmt(data.gross_before_vacation)}`, fmt(data.vacation_pay))}

              <tr className="border-t-2 border-foreground/20">
                <td className="py-3 text-sm font-semibold">Gross pay</td>
                <td className="py-3 text-sm font-semibold text-right">{fmt(data.gross_pay)}</td>
              </tr>
            </tbody>
          </table>

          <div className="bg-muted/20 px-4 py-2 border-t">
            <p className="text-[10px] text-muted-foreground">
              Hours from scheduled calendar. Service revenue from completed sales in this period.
              Retail attributed to sales containing this provider's service items.
              Gross pay is before statutory deductions (CPP, EI, income tax).
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Add Provider Dialog ───────────────────────────────────────────────────────

function AddProviderDialog({ onClose, onCreated }: { onClose: () => void; onCreated: (id: string) => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    display_name: '',
    provider_type: 'stylist',
    job_title: '',
    booking_order: '0',
  })

  function set(field: string, value: string) {
    setForm(f => {
      const next = { ...f, [field]: value }
      if (field === 'first_name' || field === 'last_name') {
        next.display_name = [next.first_name, next.last_name].filter(Boolean).join(' ')
      }
      return next
    })
  }

  const mutation = useMutation({
    mutationFn: () => createProvider({
      first_name: form.first_name,
      last_name: form.last_name,
      display_name: form.display_name || [form.first_name, form.last_name].filter(Boolean).join(' '),
      provider_type: form.provider_type,
      job_title: form.job_title || null,
      booking_order: parseInt(form.booking_order) || 0,
    }),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: ['providers-all'] })
      onCreated(created.id)
      onClose()
    },
  })

  const valid = form.first_name.trim() && form.display_name.trim()

  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Staff Member</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>First name *</Label>
              <Input value={form.first_name} onChange={e => set('first_name', e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Last name</Label>
              <Input value={form.last_name} onChange={e => set('last_name', e.target.value)} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Display name *</Label>
            <Input value={form.display_name} onChange={e => set('display_name', e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>Job title</Label>
            <Input value={form.job_title} onChange={e => set('job_title', e.target.value)} placeholder="e.g. Senior Stylist" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Type *</Label>
              <select
                value={form.provider_type}
                onChange={e => set('provider_type', e.target.value)}
                className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
              >
                <option value="stylist">Stylist</option>
                <option value="colourist">Colourist</option>
                <option value="dualist">Dualist</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label>Booking order</Label>
              <Input type="number" value={form.booking_order} onChange={e => set('booking_order', e.target.value)} />
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={() => mutation.mutate()} disabled={!valid || mutation.isPending}>
            {mutation.isPending ? 'Creating…' : 'Create'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function StaffManagementPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('profile')
  const [showAdd, setShowAdd] = useState(false)
  const [confirmDeactivate, setConfirmDeactivate] = useState(false)
  const qc = useQueryClient()

  const { data: providers = [], isLoading } = useQuery({
    queryKey: ['providers-all'],
    queryFn: listAllProviders,
  })

  const selected = providers.find(p => p.id === selectedId) ?? null

  function selectProvider(id: string) {
    setSelectedId(id)
    setTab('profile')
  }

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateProvider(selectedId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['providers-all'] })
      setConfirmDeactivate(false)
    },
  })

  const reactivateMutation = useMutation({
    mutationFn: () => updateProvider(selectedId!, { is_active: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers-all'] }),
  })

  const TABS: { key: Tab; label: string }[] = [
    { key: 'profile', label: 'Profile' },
    { key: 'compensation', label: 'Compensation' },
    { key: 'hr', label: 'HR & Banking' },
    { key: 'schedule', label: 'Schedule' },
    { key: 'payroll', label: 'Payroll' },
  ]

  return (
    <div className="flex h-screen bg-muted/30">
      {/* Provider List */}
      <div className="w-64 flex-shrink-0 bg-white border-r flex flex-col">
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <h1 className="font-semibold text-sm">Staff</h1>
          <Button size="sm" variant="ghost" onClick={() => setShowAdd(true)}>
            <Plus size={15} />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {isLoading && <p className="px-4 py-2 text-xs text-muted-foreground">Loading…</p>}
          {providers.map(p => (
            <button
              key={p.id}
              onClick={() => selectProvider(p.id)}
              className={`w-full text-left px-4 py-2.5 flex items-start gap-2.5 hover:bg-muted/50 transition-colors ${
                p.id === selectedId ? 'bg-muted' : ''
              }`}
            >
              <UserCircle2 size={28} className={`flex-shrink-0 mt-0.5 ${p.is_active ? 'text-muted-foreground' : 'text-muted-foreground/40'}`} />
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={`text-sm font-medium truncate ${!p.is_active ? 'text-muted-foreground line-through' : ''}`}>
                    {p.display_name}
                  </span>
                  {p.is_active
                    ? <CheckCircle2 size={12} className="text-emerald-500 flex-shrink-0" />
                    : <XCircle size={12} className="text-muted-foreground/40 flex-shrink-0" />
                  }
                </div>
                <div className="flex items-center gap-1 mt-0.5">
                  {typeBadge(p.provider_type)}
                  {p.job_title && <span className="text-[10px] text-muted-foreground truncate">{p.job_title}</span>}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Detail Panel */}
      {selected ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-white border-b px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold text-base">{selected.display_name}</h2>
                  {typeBadge(selected.provider_type)}
                  {selected.is_owner && (
                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">Owner</span>
                  )}
                </div>
                {selected.job_title && <p className="text-xs text-muted-foreground">{selected.job_title}</p>}
              </div>
            </div>
            {selected.is_active ? (
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-destructive"
                onClick={() => setConfirmDeactivate(true)}
              >
                Deactivate
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                className="text-emerald-600 hover:text-emerald-700"
                onClick={() => reactivateMutation.mutate()}
                disabled={reactivateMutation.isPending}
              >
                {reactivateMutation.isPending ? 'Reactivating…' : 'Reactivate'}
              </Button>
            )}
          </div>

          {/* Tabs */}
          <div className="bg-white border-b px-6">
            <div className="flex gap-0">
              {TABS.map(t => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`px-4 py-2.5 text-sm border-b-2 transition-colors ${
                    tab === t.key
                      ? 'border-foreground text-foreground font-medium'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-6">
            {tab === 'profile' && <ProfileTab key={selected.id} provider={selected} />}
            {tab === 'compensation' && <CompensationTab key={selected.id} provider={selected} />}
            {tab === 'hr' && <HRBankingTab key={selected.id} provider={selected} />}
            {tab === 'schedule' && <ScheduleTab key={selected.id} providerId={selected.id} />}
            {tab === 'payroll' && <PayrollTab key={selected.id} provider={selected} />}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
          Select a staff member
        </div>
      )}

      {/* Dialogs */}
      {showAdd && (
        <AddProviderDialog
          onClose={() => setShowAdd(false)}
          onCreated={id => { setSelectedId(id); setTab('profile') }}
        />
      )}

      {confirmDeactivate && selected && (
        <Dialog open onOpenChange={open => { if (!open) setConfirmDeactivate(false) }}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Deactivate {selected.display_name}?</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-muted-foreground py-2">
              They will be hidden from booking and scheduling. This cannot be done if they have upcoming confirmed appointments.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setConfirmDeactivate(false)}>Cancel</Button>
              <Button
                variant="ghost"
                className="text-destructive hover:text-destructive"
                onClick={() => deactivateMutation.mutate()}
                disabled={deactivateMutation.isPending}
              >
                {deactivateMutation.isPending ? 'Deactivating…' : 'Deactivate'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
