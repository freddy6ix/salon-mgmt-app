import { useEffect, useRef, useMemo } from 'react'
import { format } from 'date-fns'
import type { Appointment, AppointmentItem } from '@/api/appointments'
import type { Provider } from '@/api/providers'

// Grid config
const START_HOUR = 8      // 8:00 AM
const END_HOUR = 21       // 9:00 PM
const SLOT_MINUTES = 15   // 15-minute slots
const SLOT_HEIGHT = 20    // px per slot

const TOTAL_SLOTS = ((END_HOUR - START_HOUR) * 60) / SLOT_MINUTES
const TOTAL_HEIGHT = TOTAL_SLOTS * SLOT_HEIGHT

function minutesFromGridStart(isoTime: string): number {
  const d = new Date(isoTime)
  const hours = d.getHours()
  const mins = d.getMinutes()
  return (hours - START_HOUR) * 60 + mins
}

function durationToSlots(minutes: number): number {
  return minutes / SLOT_MINUTES
}

const STATUS_COLORS: Record<string, string> = {
  // item-level
  pending: 'bg-blue-100 border-blue-400 text-blue-900',
  in_progress: 'bg-amber-100 border-amber-400 text-amber-900',
  completed: 'bg-gray-200 border-gray-400 text-gray-500',
  cancelled: 'bg-gray-100 border-gray-300 text-gray-400 line-through opacity-60',
  // appointment-level overrides rendered via appt.status
  arrived: 'bg-green-100 border-green-500 text-green-900',
}

interface AppointmentBlock {
  item: AppointmentItem
  appointment: Appointment
  topPx: number
  heightPx: number
}

interface Props {
  providers: Provider[]
  appointments: Appointment[]
  onItemClick?: (item: AppointmentItem, appointment: Appointment) => void
  onSlotClick?: (time: string, providerId: string) => void
}

export default function TimeGrid({ providers, appointments, onItemClick, onSlotClick }: Props) {
  // Build provider -> items map
  const blocksByProvider = useMemo(() => {
    const map = new Map<string, AppointmentBlock[]>()
    for (const provider of providers) {
      map.set(provider.id, [])
    }
    for (const appt of appointments) {
      for (const item of appt.items) {
        const list = map.get(item.provider.id)
        if (!list) continue
        const offsetMins = minutesFromGridStart(item.start_time)
        const effectiveDuration = item.duration_override_minutes ?? item.duration_minutes
        list.push({
          item,
          appointment: appt,
          topPx: (offsetMins / SLOT_MINUTES) * SLOT_HEIGHT,
          heightPx: durationToSlots(effectiveDuration) * SLOT_HEIGHT,
        })
      }
    }
    return map
  }, [providers, appointments])

  // Time labels on the left
  const timeLabels = useMemo(() => {
    const labels: { label: string; topPx: number }[] = []
    for (let slot = 0; slot < TOTAL_SLOTS; slot++) {
      const totalMins = START_HOUR * 60 + slot * SLOT_MINUTES
      const h = Math.floor(totalMins / 60)
      const m = totalMins % 60
      if (m === 0) {
        const d = new Date(2000, 0, 1, h, 0)
        labels.push({ label: format(d, 'h a'), topPx: slot * SLOT_HEIGHT })
      }
    }
    return labels
  }, [])

  const hourLines = useMemo(() => {
    return timeLabels.map((l) => l.topPx)
  }, [timeLabels])

  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (scrollRef.current) {
      // Scroll to 8 AM minus a small offset so there's context above
      scrollRef.current.scrollTop = 0
    }
  }, [])

  return (
    <div ref={scrollRef} className="flex overflow-auto border rounded-lg bg-white" style={{ maxHeight: 'calc(100vh - 80px)' }}>
      {/* Time gutter */}
      <div className="sticky left-0 z-20 bg-white border-r w-14 flex-shrink-0">
        <div className="h-10 border-b" /> {/* header spacer */}
        <div className="relative" style={{ height: TOTAL_HEIGHT }}>
          {timeLabels.map(({ label, topPx }) => (
            <span
              key={label}
              className="absolute right-2 text-xs text-muted-foreground -translate-y-1/2"
              style={{ top: topPx }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Provider columns */}
      <div className="flex flex-1 min-w-0">
        {providers.map((provider) => (
          <div key={provider.id} className="flex-1 min-w-32 border-r last:border-r-0">
            {/* Provider header */}
            <div className="h-10 border-b flex items-center justify-center sticky top-0 z-10 bg-white">
              <span className="text-sm font-medium truncate px-2">{provider.display_name}</span>
            </div>

            {/* Grid body */}
            <div
              className="relative"
              style={{ height: TOTAL_HEIGHT }}
              onClick={(e) => {
                if (!onSlotClick) return
                const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect()
                const offsetY = e.clientY - rect.top
                const totalMins = START_HOUR * 60 + Math.floor(offsetY / SLOT_HEIGHT) * SLOT_MINUTES
                const h = Math.floor(totalMins / 60)
                const m = totalMins % 60
                onSlotClick(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`, provider.id)
              }}
            >
              {/* Hour grid lines */}
              {hourLines.map((topPx) => (
                <div
                  key={topPx}
                  className="absolute left-0 right-0 border-t border-gray-100"
                  style={{ top: topPx }}
                />
              ))}

              {/* Appointment blocks */}
              {(blocksByProvider.get(provider.id) ?? []).map(({ item, appointment, topPx, heightPx }) => {
                const colorKey =
                  appointment.status === 'in_progress' ? 'arrived' :
                  appointment.status === 'completed' ? 'completed' :
                  appointment.status === 'cancelled' ? 'cancelled' :
                  item.status
                return (
                <button
                  key={item.id}
                  onClick={(e) => { e.stopPropagation(); onItemClick?.(item, appointment) }}
                  className={`absolute left-1 right-1 rounded border text-left overflow-hidden px-1.5 py-0.5 hover:opacity-80 transition-opacity ${STATUS_COLORS[colorKey]}`}
                  style={{ top: topPx + 1, height: Math.max(heightPx - 2, 18) }}
                >
                  <p className="text-xs font-medium truncate leading-tight">
                    {appointment.client.first_name} {appointment.client.last_name}
                  </p>
                  {heightPx >= 36 && (
                    <p className="text-xs truncate leading-tight opacity-75">{item.service.name}</p>
                  )}
                </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
