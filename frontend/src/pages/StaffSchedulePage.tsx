import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWeeklySchedules, setWeeklySchedule, type ProviderWeeklyHours, type DayHours } from '@/api/schedules'
import { getOperatingHours, type OperatingHoursDay } from '@/api/settings'
import { Button } from '@/components/ui/button'

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

interface RowProps {
  provider: ProviderWeeklyHours
  salonHours: SalonHoursMap
  onSave: (provider_id: string, days: DayHours[], effective_from: string) => void
  saving: boolean
}

function ProviderRow({ provider, salonHours, onSave, saving }: RowProps) {
  const [days, setDays] = useState<DayHours[]>(() =>
    provider.days.map((d) => ({ ...d }))
  )
  const [dirty, setDirty] = useState(false)
  const [effectiveFrom, setEffectiveFrom] = useState(TODAY)

  function updateDay(dow: number, patch: Partial<DayHours>) {
    setDays((prev) => prev.map((d) => d.day_of_week === dow ? { ...d, ...patch } : d))
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

  return (
    <tr className="border-b last:border-0">
      <td className="py-3 pr-4 font-medium text-sm w-28 align-middle">{provider.display_name}</td>
      {days.map((day) => {
        const salon = salonHours[day.day_of_week]
        const salonClosed = salon === null
        return (
          <td key={day.day_of_week} className="px-2 py-2 align-middle">
            {salonClosed ? (
              <span className="text-xs text-muted-foreground">Closed</span>
            ) : (
              <div className="flex flex-col gap-1 min-w-[110px]">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={day.is_working}
                    onChange={(e) => toggleWorking(day.day_of_week, e.target.checked)}
                    className="accent-primary"
                  />
                  <span className="text-xs">{day.is_working ? 'Working' : 'Off'}</span>
                </label>
                {day.is_working && (
                  <div className="flex items-center gap-1">
                    <input
                      type="time"
                      value={day.start_time ?? ''}
                      min={salon.open}
                      max={day.end_time ?? salon.close}
                      onChange={(e) =>
                        updateDay(day.day_of_week, {
                          start_time: clamp(e.target.value, salon.open, day.end_time ?? salon.close),
                        })
                      }
                      className="text-xs border border-input rounded px-1 py-0.5 w-[72px] bg-background"
                    />
                    <span className="text-xs text-muted-foreground">–</span>
                    <input
                      type="time"
                      value={day.end_time ?? ''}
                      min={day.start_time ?? salon.open}
                      max={salon.close}
                      onChange={(e) =>
                        updateDay(day.day_of_week, {
                          end_time: clamp(e.target.value, day.start_time ?? salon.open, salon.close),
                        })
                      }
                      className="text-xs border border-input rounded px-1 py-0.5 w-[72px] bg-background"
                    />
                  </div>
                )}
              </div>
            )}
          </td>
        )
      })}
      <td className="pl-4 align-middle">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-muted-foreground whitespace-nowrap">From</label>
            <input
              type="date"
              value={effectiveFrom}
              min={TODAY}
              onChange={e => { setEffectiveFrom(e.target.value); setDirty(true) }}
              className="text-xs border border-input rounded px-1 py-0.5 bg-background"
            />
          </div>
          <Button
            size="sm"
            disabled={!dirty || saving}
            onClick={() => { onSave(provider.provider_id, days, effectiveFrom); setDirty(false) }}
          >
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </td>
    </tr>
  )
}

export default function StaffSchedulePage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [savingId, setSavingId] = useState<string | null>(null)

  const { data: providers = [], isLoading } = useQuery({
    queryKey: ['schedules-weekly'],
    queryFn: getWeeklySchedules,
  })

  const { data: operatingHours = [], isLoading: hoursLoading } = useQuery({
    queryKey: ['operating-hours'],
    queryFn: getOperatingHours,
  })

  const salonHours = buildSalonHours(operatingHours)

  const mutation = useMutation({
    mutationFn: ({ provider_id, days, effective_from }: { provider_id: string; days: DayHours[]; effective_from: string }) =>
      setWeeklySchedule(provider_id, days, effective_from),
    onMutate: ({ provider_id }) => setSavingId(provider_id),
    onSettled: () => {
      setSavingId(null)
      qc.invalidateQueries({ queryKey: ['schedules-weekly'] })
      qc.invalidateQueries({ queryKey: ['schedules'] })
    },
  })

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="flex items-center gap-4 px-6 py-3 bg-white border-b">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>← Back</Button>
        <h1 className="font-semibold text-base">Staff Schedules</h1>
      </header>

      <main className="p-6">
        <div className="bg-white border rounded-lg overflow-auto">
          {isLoading || hoursLoading ? (
            <p className="p-6 text-sm text-muted-foreground">Loading…</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/30">
                  <th className="py-2 pr-4 text-left font-medium text-xs text-muted-foreground w-28">Provider</th>
                  {DAY_NAMES.map((d) => (
                    <th key={d} className="px-2 py-2 text-left font-medium text-xs text-muted-foreground">{d}</th>
                  ))}
                  <th className="pl-4" />
                </tr>
              </thead>
              <tbody>
                {providers.map((p) => (
                  <ProviderRow
                    key={p.provider_id}
                    provider={p}
                    salonHours={salonHours}
                    saving={savingId === p.provider_id}
                    onSave={(id, days, effective_from) => mutation.mutate({ provider_id: id, days, effective_from })}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Provider hours must fall within salon hours. Salon hours are configured under Settings → Scheduling.
          Use the "From" date to schedule a change in advance — past schedules are locked and preserved as history.
        </p>
      </main>
    </div>
  )
}
