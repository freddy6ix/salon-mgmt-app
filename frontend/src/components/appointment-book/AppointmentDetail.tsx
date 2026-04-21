import { format, parseISO } from 'date-fns'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Appointment, AppointmentItem } from '@/api/appointments'
import { updateAppointmentStatus } from '@/api/appointments'
import { getClientHistory, updateClientNotes } from '@/api/clients'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  in_progress: 'default',
  completed: 'outline',
  cancelled: 'destructive',
}

const VISIT_STATUS_COLOR: Record<string, string> = {
  confirmed: 'text-blue-600',
  in_progress: 'text-green-600',
  completed: 'text-muted-foreground',
  cancelled: 'text-destructive',
}

type Tab = 'appointment' | 'history' | 'notes'

interface Props {
  item: AppointmentItem | null
  appointment: Appointment | null
  date: string
  onClose: () => void
}

export default function AppointmentDetail({ item, appointment, date, onClose }: Props) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('appointment')
  const [notesValue, setNotesValue] = useState<string | null>(null)

  const clientId = appointment?.client.id ?? null

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['client-history', clientId],
    queryFn: () => getClientHistory(clientId!),
    enabled: !!clientId && tab === 'history',
  })

  const statusMutation = useMutation({
    mutationFn: (newStatus: Appointment['status']) =>
      updateAppointmentStatus(appointment!.id, newStatus),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments', date] })
      onClose()
    },
  })

  const notesMutation = useMutation({
    mutationFn: (notes: string | null) =>
      updateClientNotes(clientId!, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments', date] })
      setNotesValue(null)
    },
  })

  function handleOpenChange(isOpen: boolean) {
    if (!isOpen) { setTab('appointment'); setNotesValue(null); onClose() }
  }

  if (!item || !appointment) return null

  const startTime = new Date(item.start_time)
  const effectiveDuration = item.duration_override_minutes ?? item.duration_minutes
  const endTime = new Date(startTime.getTime() + effectiveDuration * 60000)
  const apptStatus = appointment.status
  const client = appointment.client

  // Notes editing — initialise from client when tab first opens
  const currentNotes = notesValue !== null ? notesValue : (client.special_instructions ?? '')

  return (
    <Dialog open onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {client.first_name} {client.last_name}
          </DialogTitle>
        </DialogHeader>

        {client.cell_phone && (
          <p className="text-sm text-muted-foreground -mt-2">{client.cell_phone}</p>
        )}

        {/* Tabs */}
        <div className="flex gap-1 border-b">
          {(['appointment', 'history', 'notes'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 text-sm capitalize border-b-2 -mb-px transition-colors ${
                tab === t
                  ? 'border-foreground font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {t === 'notes' ? 'Client notes' : t === 'history' ? 'History' : 'Appointment'}
            </button>
          ))}
        </div>

        {/* ── Appointment tab ── */}
        {tab === 'appointment' && (
          <div className="space-y-4">
            {client.special_instructions && (
              <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800">
                {client.special_instructions}
              </div>
            )}

            <div className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-sm">{item.service.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {format(startTime, 'h:mm a')} – {format(endTime, 'h:mm a')} · {effectiveDuration} min
                  </p>
                  <p className="text-xs text-muted-foreground">
                    with {item.provider.display_name}
                    {item.second_provider ? ` & ${item.second_provider.display_name}` : ''}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge variant={STATUS_VARIANT[item.status]}>{item.status.replace('_', ' ')}</Badge>
                  <span className="text-sm font-medium">${item.price.toFixed(2)}</span>
                </div>
              </div>

              {item.notes && (
                <p className="text-xs text-muted-foreground italic">{item.notes}</p>
              )}

              {item.service.processing_duration_minutes > 0 && (
                <p className="text-xs text-muted-foreground">
                  Processing: {item.service.processing_duration_minutes} min
                  (starts at {format(new Date(startTime.getTime() + item.service.processing_offset_minutes * 60000), 'h:mm a')})
                </p>
              )}
            </div>

            {appointment.notes && (
              <>
                <Separator />
                <p className="text-xs text-muted-foreground">{appointment.notes}</p>
              </>
            )}

            {statusMutation.isError && (
              <p className="text-xs text-destructive">
                {statusMutation.error instanceof Error ? statusMutation.error.message : 'Update failed'}
              </p>
            )}

            {apptStatus === 'confirmed' && (
              <div className="flex gap-2 pt-1">
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate('in_progress')}
                >
                  Client arrived
                </Button>
                <Button
                  variant="destructive"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate('cancelled')}
                >
                  Cancel
                </Button>
              </div>
            )}

            {apptStatus === 'in_progress' && (
              <div className="flex gap-2 pt-1">
                <Button
                  className="flex-1"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate('completed')}
                >
                  Check out
                </Button>
                <Button
                  variant="destructive"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate('cancelled')}
                >
                  Cancel
                </Button>
              </div>
            )}

            {apptStatus === 'completed' && (
              <p className="text-xs text-muted-foreground text-center pt-1">Checked out</p>
            )}
            {apptStatus === 'cancelled' && (
              <p className="text-xs text-destructive text-center pt-1">Cancelled</p>
            )}
          </div>
        )}

        {/* ── History tab ── */}
        {tab === 'history' && (
          <div className="space-y-2 max-h-80 overflow-auto">
            {historyLoading ? (
              <p className="text-sm text-muted-foreground py-4 text-center">Loading…</p>
            ) : history.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">No previous visits</p>
            ) : (
              history.map((visit) => (
                <div key={visit.appointment_id} className="border rounded-md px-3 py-2 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {format(parseISO(visit.date), 'MMM d, yyyy')}
                    </span>
                    <span className={`text-xs capitalize ${VISIT_STATUS_COLOR[visit.status] ?? ''}`}>
                      {visit.status.replace('_', ' ')}
                    </span>
                  </div>
                  {visit.items.map((vi, i) => (
                    <p key={i} className="text-xs text-muted-foreground">
                      {vi.service_name} · {vi.provider_name}
                      <span className="ml-1 text-foreground">${vi.price.toFixed(2)}</span>
                    </p>
                  ))}
                </div>
              ))
            )}
          </div>
        )}

        {/* ── Notes tab ── */}
        {tab === 'notes' && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              Standing notes shown whenever this client has an appointment.
            </p>
            <textarea
              rows={5}
              value={currentNotes}
              onChange={(e) => setNotesValue(e.target.value)}
              placeholder="Allergies, preferences, standing instructions…"
              className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
            />
            {notesMutation.isError && (
              <p className="text-xs text-destructive">Save failed</p>
            )}
            <Button
              className="w-full"
              disabled={notesMutation.isPending || currentNotes === (client.special_instructions ?? '')}
              onClick={() => notesMutation.mutate(currentNotes || null)}
            >
              {notesMutation.isPending ? 'Saving…' : 'Save notes'}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
