import { useEffect, useRef, useMemo, useCallback, useState } from 'react'
import { format } from 'date-fns'
import { useQueryClient } from '@tanstack/react-query'
import type { Appointment, AppointmentItem } from '@/api/appointments'
import { patchAppointmentItem } from '@/api/appointments'
import type { Provider } from '@/api/providers'
import type { ProviderWorkStatus } from '@/api/schedules'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

// Grid config
const START_HOUR = 8
const END_HOUR = 21
const SLOT_HEIGHT = 20   // px per slot
const HEADER_HEIGHT = 40 // px


function minutesFromGridStart(isoTime: string): number {
  // Parse HH:MM directly from the ISO string to avoid browser UTC→local conversion.
  // start_time is stored as wall-clock time with no timezone offset.
  const timePart = isoTime.split('T')[1] ?? isoTime
  const [h, m] = timePart.split(':').map(Number)
  return (h - START_HOUR) * 60 + m
}

const APPT_STATUS_COLOR: Record<string, string> = {
  confirmed: 'bg-blue-100 border-blue-400 text-blue-900',
  in_progress: 'bg-green-100 border-green-500 text-green-900',
  completed: 'bg-gray-200 border-gray-400 text-gray-500',
  cancelled: 'bg-gray-100 border-gray-300 text-gray-400 line-through opacity-60',
}

interface AppointmentBlock {
  item: AppointmentItem
  appointment: Appointment
  topPx: number
  heightPx: number
}

interface DragState {
  type: 'move' | 'resize'
  appointmentId: string
  itemId: string
  originalTop: number
  originalHeight: number
  originalProviderIdx: number
  startY: number
  startX: number
  currentTop: number
  currentHeight: number
  currentProviderIdx: number
  label: string
}

interface Props {
  providers: Provider[]
  appointments: Appointment[]
  date: string
  slotMinutes: number
  providerHours?: ProviderWorkStatus[]
  onItemClick?: (item: AppointmentItem, appointment: Appointment) => void
  onSlotClick?: (time: string, providerId: string) => void
  onClientClick?: (clientId: string) => void
}

export default function TimeGrid({ providers, appointments, date, slotMinutes, providerHours = [], onItemClick, onSlotClick, onClientClick }: Props) {
  const qc = useQueryClient()
  const scrollRef = useRef<HTMLDivElement>(null)
  const gridRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef<DragState | null>(null)
  const didDragRef = useRef(false)
  const [drag, setDrag] = useState<DragState | null>(null)
  const [nowPx, setNowPx] = useState<number | null>(null)

  type PendingPatch = {
    appointmentId: string
    itemId: string
    patch: Parameters<typeof patchAppointmentItem>[2]
    providerName: string
  }
  const [pendingPatch, setPendingPatch] = useState<PendingPatch | null>(null)

  const SLOT_MINUTES = slotMinutes
  const TOTAL_SLOTS = ((END_HOUR - START_HOUR) * 60) / SLOT_MINUTES
  const TOTAL_HEIGHT = TOTAL_SLOTS * SLOT_HEIGHT

  const activeProviders = providers.filter((p) => p.has_appointments)

  // Current time indicator — only shown when viewing today
  useEffect(() => {
    const todayStr = format(new Date(), 'yyyy-MM-dd')
    if (date !== todayStr) {
      setNowPx(null)
      return
    }
    function update() {
      const now = new Date()
      const mins = (now.getHours() - START_HOUR) * 60 + now.getMinutes()
      if (mins >= 0 && mins <= (END_HOUR - START_HOUR) * 60) {
        setNowPx((mins / SLOT_MINUTES) * SLOT_HEIGHT)
      } else {
        setNowPx(null)
      }
    }
    update()
    const id = setInterval(update, 60_000)
    return () => clearInterval(id)
  }, [SLOT_MINUTES, date])

  const blocksByProvider = useMemo(() => {
    const map = new Map<string, AppointmentBlock[]>()
    for (const p of activeProviders) map.set(p.id, [])
    for (const appt of appointments) {
      for (const item of appt.items) {
        const list = map.get(item.provider.id)
        if (!list) continue
        const offsetMins = minutesFromGridStart(item.start_time)
        const effectiveDuration = item.duration_override_minutes ?? item.duration_minutes
        list.push({
          item, appointment: appt,
          topPx: (offsetMins / SLOT_MINUTES) * SLOT_HEIGHT,
          heightPx: (effectiveDuration / SLOT_MINUTES) * SLOT_HEIGHT,
        })
      }
    }
    return map
  }, [activeProviders, appointments, SLOT_MINUTES])

  const timeLabels = useMemo(() => {
    const labels: { label: string; topPx: number }[] = []
    for (let slot = 0; slot < TOTAL_SLOTS; slot++) {
      const totalMins = START_HOUR * 60 + slot * SLOT_MINUTES
      if (totalMins % 60 === 0) {
        const d = new Date(2000, 0, 1, Math.floor(totalMins / 60), 0)
        labels.push({ label: format(d, 'h a'), topPx: slot * SLOT_HEIGHT })
      }
    }
    return labels
  }, [SLOT_MINUTES, TOTAL_SLOTS])

  const hourLines = useMemo(() => timeLabels.map((l) => l.topPx), [timeLabels])

  const hoursMap = useMemo(() => {
    const m = new Map<string, { startPx: number; endPx: number }>()
    for (const s of providerHours) {
      if (!s.start_time || !s.end_time) continue
      const [sh, sm] = s.start_time.split(':').map(Number)
      const [eh, em] = s.end_time.split(':').map(Number)
      const startMins = (sh - START_HOUR) * 60 + sm
      const endMins = (eh - START_HOUR) * 60 + em
      m.set(s.provider_id, {
        startPx: (startMins / SLOT_MINUTES) * SLOT_HEIGHT,
        endPx: (endMins / SLOT_MINUTES) * SLOT_HEIGHT,
      })
    }
    return m
  }, [providerHours, SLOT_MINUTES])

  // ── Column width helper ──────────────────────────────────────────────────
  function getColumnRects(): DOMRect[] {
    if (!gridRef.current) return []
    return Array.from(gridRef.current.querySelectorAll<HTMLElement>('[data-provider-col]'))
      .map((el) => el.getBoundingClientRect())
  }

  function providerIdxFromX(x: number): number {
    const rects = getColumnRects()
    for (let i = 0; i < rects.length; i++) {
      if (x >= rects[i].left && x <= rects[i].right) return i
    }
    return -1
  }

  // ── Snap helpers ─────────────────────────────────────────────────────────
  function snapToSlot(px: number): number {
    return Math.round(px / SLOT_HEIGHT) * SLOT_HEIGHT
  }

  function pxToLocalTime(topPx: number): string {
    const totalMins = START_HOUR * 60 + (topPx / SLOT_HEIGHT) * SLOT_MINUTES
    const h = Math.floor(totalMins / 60)
    const m = totalMins % 60
    return `${date}T${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00`
  }

  function pxToDuration(heightPx: number): number {
    return Math.max(SLOT_MINUTES, Math.round(heightPx / SLOT_HEIGHT) * SLOT_MINUTES)
  }

  // ── Pointer handlers ─────────────────────────────────────────────────────
  const onMovePointerDown = useCallback((
    e: React.PointerEvent,
    item: AppointmentItem,
    appointment: Appointment,
    topPx: number,
    heightPx: number,
    providerIdx: number,
  ) => {
    if (appointment.status === 'completed' || appointment.status === 'cancelled') return
    e.stopPropagation()
    e.currentTarget.setPointerCapture(e.pointerId)
    const state: DragState = {
      type: 'move',
      appointmentId: appointment.id,
      itemId: item.id,
      originalTop: topPx,
      originalHeight: heightPx,
      originalProviderIdx: providerIdx,
      startY: e.clientY,
      startX: e.clientX,
      currentTop: topPx,
      currentHeight: heightPx,
      currentProviderIdx: providerIdx,
      label: `${appointment.client.first_name} ${appointment.client.last_name} · ${item.service.name}`,
    }
    dragRef.current = state
    didDragRef.current = false
    setDrag({ ...state })
  }, [])

  const onResizePointerDown = useCallback((
    e: React.PointerEvent,
    item: AppointmentItem,
    appointment: Appointment,
    topPx: number,
    heightPx: number,
    providerIdx: number,
  ) => {
    if (appointment.status === 'completed' || appointment.status === 'cancelled') return
    e.stopPropagation()
    e.currentTarget.setPointerCapture(e.pointerId)
    const state: DragState = {
      type: 'resize',
      appointmentId: appointment.id,
      itemId: item.id,
      originalTop: topPx,
      originalHeight: heightPx,
      originalProviderIdx: providerIdx,
      startY: e.clientY,
      startX: e.clientX,
      currentTop: topPx,
      currentHeight: heightPx,
      currentProviderIdx: providerIdx,
      label: `${appointment.client.first_name} ${appointment.client.last_name} · ${item.service.name}`,
    }
    dragRef.current = state
    setDrag({ ...state })
  }, [])

  useEffect(() => {
    function onPointerMove(e: PointerEvent) {
      const d = dragRef.current
      if (!d) return
      didDragRef.current = true
      const deltaY = e.clientY - d.startY

      if (d.type === 'move') {
        const rawTop = d.originalTop + deltaY
        const snapped = Math.max(0, Math.min(snapToSlot(rawTop), TOTAL_HEIGHT - d.originalHeight))
        const colIdx = providerIdxFromX(e.clientX)
        dragRef.current = {
          ...d,
          currentTop: snapped,
          currentProviderIdx: colIdx >= 0 ? colIdx : d.currentProviderIdx,
        }
      } else {
        const rawHeight = d.originalHeight + deltaY
        const snapped = Math.max(SLOT_HEIGHT, snapToSlot(rawHeight))
        dragRef.current = { ...d, currentHeight: snapped }
      }
      setDrag({ ...dragRef.current! })
    }

    async function onPointerUp() {
      const d = dragRef.current
      if (!d) return
      dragRef.current = null
      setDrag(null)
      // Leave didDragRef.current = true briefly so the grid onClick can see it,
      // then clear it after the click event has fired.
      setTimeout(() => { didDragRef.current = false }, 50)

      const moved = d.type === 'move'
        ? d.currentTop !== d.originalTop || d.currentProviderIdx !== d.originalProviderIdx
        : d.currentHeight !== d.originalHeight

      if (!moved) return

      const patch: Parameters<typeof patchAppointmentItem>[2] = {}
      if (d.type === 'move') {
        patch.start_time = pxToLocalTime(d.currentTop)
        if (d.currentProviderIdx !== d.originalProviderIdx) {
          patch.provider_id = activeProviders[d.currentProviderIdx]?.id
        }
      } else {
        patch.duration_override_minutes = pxToDuration(d.currentHeight)
      }

      const targetProviderIdx = d.type === 'move' ? d.currentProviderIdx : d.originalProviderIdx
      const targetProvider = activeProviders[targetProviderIdx]
      const hours = targetProvider ? hoursMap.get(targetProvider.id) : undefined

      let outsideHours = false
      if (hours) {
        const startPx = d.type === 'move' ? d.currentTop : d.originalTop
        const endPx = d.type === 'move'
          ? d.currentTop + d.originalHeight
          : d.originalTop + d.currentHeight
        outsideHours = startPx < hours.startPx || endPx > hours.endPx
      }

      if (outsideHours && targetProvider) {
        setPendingPatch({ appointmentId: d.appointmentId, itemId: d.itemId, patch, providerName: targetProvider.display_name })
        return
      }

      try {
        await patchAppointmentItem(d.appointmentId, d.itemId, patch)
        qc.invalidateQueries({ queryKey: ['appointments', date] })
      } catch (err) {
        console.error('Patch failed', err)
      }
    }

    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
    }
  }, [activeProviders, date, qc, hoursMap])

  // ── Render ───────────────────────────────────────────────────────────────
  if (activeProviders.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border rounded-lg bg-white text-muted-foreground text-sm">
        Salon closed — no providers scheduled for this day.
      </div>
    )
  }

  return (
    <>
    <div
      ref={scrollRef}
      className="flex overflow-auto border rounded-lg bg-white select-none"
      style={{ maxHeight: 'calc(100vh - 80px)' }}
    >
      {/* Time gutter */}
      <div className="sticky left-0 z-20 bg-white w-14 flex-shrink-0 relative">
        {/* Explicit-height right border — same fix as column separators; border-r stops at
            the flex-constrained viewport height, not the full 1600px grid */}
        <div
          className="absolute right-0 top-0 w-px bg-gray-300 pointer-events-none"
          style={{ height: TOTAL_HEIGHT + HEADER_HEIGHT, zIndex: 1 }}
        />
        <div style={{ height: HEADER_HEIGHT }} />
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
      <div ref={gridRef} className="flex flex-1 min-w-0 relative">
        {/* Current time indicator — single overlay spanning all columns */}
        {nowPx !== null && (
          <div
            className="absolute left-0 right-0 z-20 pointer-events-none flex items-center"
            style={{ top: nowPx + HEADER_HEIGHT }}
          >
            <div className="w-2 h-2 rounded-full bg-red-500 -ml-1 flex-shrink-0" />
            <div className="flex-1 h-px bg-red-500" />
          </div>
        )}
        {activeProviders.map((provider, providerIdx) => (
          <div
            key={provider.id}
            data-provider-col={provider.id}
            className="flex-1 min-w-32 relative"
          >
            {/* Vertical column separator — explicit height because column div is flex-constrained
                to viewport height, so bottom:0 would stop at the viewport, not the grid bottom */}
            {providerIdx < activeProviders.length - 1 && (
              <div
                className="absolute right-0 top-0 w-px bg-gray-300 pointer-events-none"
                style={{ height: TOTAL_HEIGHT + HEADER_HEIGHT, zIndex: 11 }}
              />
            )}
            {/* Header */}
            <div
              style={{ height: HEADER_HEIGHT }}
              className="border-b flex items-center justify-center sticky top-0 z-10 bg-white"
            >
              <span className="text-sm font-medium truncate px-2">{provider.display_name}</span>
            </div>

            {/* Grid body */}
            <div
              className="relative"
              style={{ height: TOTAL_HEIGHT }}
              onDoubleClick={(e) => {
                if (!onSlotClick || dragRef.current || didDragRef.current) return
                const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect()
                const offsetY = e.clientY - rect.top
                const totalMins = START_HOUR * 60 + Math.floor(offsetY / SLOT_HEIGHT) * SLOT_MINUTES
                const h = Math.floor(totalMins / 60)
                const m = totalMins % 60
                onSlotClick(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`, provider.id)
              }}
            >
              {/* Off-hours shading */}
              {((_h) => _h && (
                <>
                  {_h.startPx > 0 && <div className="absolute inset-x-0 top-0 bg-gray-100 pointer-events-none z-[1]" style={{ height: _h.startPx }} />}
                  {_h.endPx < TOTAL_HEIGHT && <div className="absolute inset-x-0 bg-gray-100 pointer-events-none z-[1]" style={{ top: _h.endPx, bottom: 0 }} />}
                </>
              ))(hoursMap.get(provider.id))}

              {/* Hour lines — skip the very first one (top: 0) to avoid bleeding into gutter border */}
              {hourLines.filter((topPx) => topPx > 0).map((topPx) => (
                <div key={topPx} className="absolute left-0 right-0 border-t border-gray-100" style={{ top: topPx }} />
              ))}


              {/* Drag ghost in this column */}
              {drag && drag.type === 'move' && drag.currentProviderIdx === providerIdx && (
                <div
                  className="absolute left-1 right-1 rounded border-2 border-dashed border-blue-400 bg-blue-50 opacity-70 pointer-events-none z-20 flex items-start px-1.5 py-0.5"
                  style={{ top: drag.currentTop + 1, height: Math.max(drag.originalHeight - 2, 18) }}
                >
                  <p className="text-xs font-medium truncate text-blue-700">{drag.label}</p>
                </div>
              )}
              {drag && drag.type === 'resize' && drag.originalProviderIdx === providerIdx && (
                <div
                  className="absolute left-1 right-1 rounded border-2 border-dashed border-blue-400 bg-blue-50 opacity-70 pointer-events-none z-20"
                  style={{ top: drag.originalTop + 1, height: Math.max(drag.currentHeight - 2, 18) }}
                />
              )}

              {/* Appointment blocks */}
              {(blocksByProvider.get(provider.id) ?? []).map(({ item, appointment, topPx, heightPx }) => {
                const isDragging = drag?.itemId === item.id
                const colorClass = APPT_STATUS_COLOR[appointment.status] ?? APPT_STATUS_COLOR.confirmed
                return (
                  <div
                    key={item.id}
                    className={`absolute left-1 right-1 rounded border text-left overflow-hidden flex flex-col z-[2]
                      ${colorClass}
                      ${isDragging ? 'opacity-30' : 'hover:opacity-90'}
                      ${appointment.status === 'completed' || appointment.status === 'cancelled' ? '' : 'cursor-grab active:cursor-grabbing'}
                    `}
                    style={{ top: topPx + 1, height: Math.max(heightPx - 2, 18) }}
                  >
                    {/* Main click / drag area */}
                    <div
                      className="flex-1 px-1.5 py-0.5 overflow-hidden"
                      onClick={(e) => { if (!didDragRef.current) { e.stopPropagation(); onItemClick?.(item, appointment) } }}
                      onPointerDown={(e) => onMovePointerDown(e, item, appointment, topPx, heightPx, providerIdx)}
                    >
                      <p className="text-xs font-medium truncate leading-tight">
                        <span
                          onPointerDown={e => e.stopPropagation()}
                          onClick={e => { e.stopPropagation(); if (!didDragRef.current) onClientClick?.(appointment.client.id) }}
                          className={onClientClick ? 'hover:underline cursor-pointer' : ''}
                        >
                          {appointment.client.first_name} {appointment.client.last_name}
                        </span>
                      </p>
                      {heightPx >= 36 && (
                        <p className="text-xs truncate leading-tight opacity-75">{item.service.name}</p>
                      )}
                    </div>

                    {/* Resize handle — bottom strip */}
                    {appointment.status !== 'completed' && appointment.status !== 'cancelled' && heightPx >= 24 && (
                      <div
                        className="h-2 cursor-ns-resize flex-shrink-0 flex items-center justify-center"
                        onPointerDown={(e) => onResizePointerDown(e, item, appointment, topPx, heightPx, providerIdx)}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="w-6 h-0.5 rounded bg-current opacity-30" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Outside-hours confirmation dialog */}
    <Dialog open={pendingPatch !== null} onOpenChange={(open) => { if (!open) setPendingPatch(null) }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Outside scheduled hours</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          This appointment falls outside {pendingPatch?.providerName}'s scheduled working hours. Book anyway?
        </p>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => setPendingPatch(null)}>Cancel</Button>
          <Button
            onClick={async () => {
              if (!pendingPatch) return
              const { appointmentId, itemId, patch } = pendingPatch
              setPendingPatch(null)
              try {
                await patchAppointmentItem(appointmentId, itemId, patch)
                qc.invalidateQueries({ queryKey: ['appointments', date] })
              } catch (err) {
                console.error('Patch failed', err)
              }
            }}
          >
            Book anyway
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  )
}
