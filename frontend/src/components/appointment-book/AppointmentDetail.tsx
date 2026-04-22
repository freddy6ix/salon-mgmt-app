import { format, parseISO } from 'date-fns'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import type { Appointment, AppointmentItem } from '@/api/appointments'
import { updateAppointmentStatus, addAppointmentItem, removeAppointmentItem } from '@/api/appointments'
import { getClientHistory, updateClientNotes } from '@/api/clients'
import { listServices } from '@/api/services'
import { listProviders } from '@/api/providers'
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

interface AddItemForm {
  serviceId: string
  providerId: string
  startTime: string
  durationMinutes: number
  price: string
}

export default function AppointmentDetail({ item, appointment, date, onClose }: Props) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('appointment')
  const [notesValue, setNotesValue] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [addForm, setAddForm] = useState<AddItemForm>({
    serviceId: '',
    providerId: '',
    startTime: '09:00',
    durationMinutes: 60,
    price: '',
  })
  const [addError, setAddError] = useState<string | null>(null)

  const clientId = appointment?.client.id ?? null

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['client-history', clientId],
    queryFn: () => getClientHistory(clientId!),
    enabled: !!clientId && tab === 'history',
  })

  const { data: services = [] } = useQuery({
    queryKey: ['services'],
    queryFn: listServices,
    enabled: showAddForm,
  })

  const { data: providers = [] } = useQuery({
    queryKey: ['providers'],
    queryFn: listProviders,
    enabled: showAddForm,
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
    mutationFn: (notes: string | null) => updateClientNotes(clientId!, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments', date] })
      setNotesValue(null)
    },
  })

  const removeMutation = useMutation({
    mutationFn: (itemId: string) => removeAppointmentItem(appointment!.id, itemId),
    onSuccess: (updated) => {
      qc.setQueryData(['appointments', date], (old: Appointment[] | undefined) =>
        old?.map(a => a.id === updated.id ? updated : a)
      )
    },
  })

  const addMutation = useMutation({
    mutationFn: () => {
      if (!appointment) throw new Error('No appointment')
      const apptDate = appointment.appointment_date.split('T')[0]
      return addAppointmentItem(appointment.id, {
        service_id: addForm.serviceId,
        provider_id: addForm.providerId,
        start_time: `${apptDate}T${addForm.startTime}:00`,
        duration_minutes: addForm.durationMinutes,
        price: parseFloat(addForm.price),
        sequence: (appointment.items.length ?? 0) + 1,
      })
    },
    onSuccess: (updated) => {
      qc.setQueryData(['appointments', date], (old: Appointment[] | undefined) =>
        old?.map(a => a.id === updated.id ? updated : a)
      )
      setShowAddForm(false)
      setAddForm({ serviceId: '', providerId: '', startTime: '09:00', durationMinutes: 60, price: '' })
      setAddError(null)
    },
    onError: (e) => setAddError(e instanceof Error ? e.message : 'Failed to add service'),
  })

  function handleOpenChange(isOpen: boolean) {
    if (!isOpen) { setTab('appointment'); setNotesValue(null); setShowAddForm(false); onClose() }
  }

  function handleServiceChange(serviceId: string) {
    const svc = services.find(s => s.id === serviceId)
    setAddForm(f => ({
      ...f,
      serviceId,
      durationMinutes: svc?.duration_minutes ?? 60,
      price: svc?.default_price != null ? String(svc.default_price) : f.price,
    }))
  }

  function handleAddSubmit() {
    if (!addForm.serviceId) { setAddError('Select a service'); return }
    if (!addForm.providerId) { setAddError('Select a provider'); return }
    if (!addForm.price || isNaN(parseFloat(addForm.price))) { setAddError('Enter a price'); return }
    setAddError(null)
    addMutation.mutate()
  }

  if (!item || !appointment) return null

  const apptStatus = appointment.status
  const client = appointment.client
  const canEdit = apptStatus === 'confirmed'
  const currentNotes = notesValue !== null ? notesValue : (client.special_instructions ?? '')

  // Sort items by start time
  const sortedItems = [...appointment.items].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

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

            {/* All items */}
            <div className="space-y-2">
              {sortedItems.map(apptItem => {
                const startTime = new Date(apptItem.start_time)
                const effectiveDuration = apptItem.duration_override_minutes ?? apptItem.duration_minutes
                const endTime = new Date(startTime.getTime() + effectiveDuration * 60000)
                const isClicked = apptItem.id === item.id
                return (
                  <div
                    key={apptItem.id}
                    className={`rounded-md border px-3 py-2 ${isClicked ? 'border-foreground/30 bg-muted/30' : ''}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-medium text-sm">{apptItem.service.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {format(startTime, 'h:mm a')} – {format(endTime, 'h:mm a')} · {effectiveDuration} min
                        </p>
                        <p className="text-xs text-muted-foreground">
                          with {apptItem.provider.display_name}
                          {apptItem.second_provider ? ` & ${apptItem.second_provider.display_name}` : ''}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-1">
                          {canEdit && sortedItems.length > 1 && (
                            <button
                              onClick={() => removeMutation.mutate(apptItem.id)}
                              disabled={removeMutation.isPending}
                              className="text-muted-foreground hover:text-destructive transition-colors"
                              title="Remove service"
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          )}
                          <Badge variant={STATUS_VARIANT[apptItem.status]}>
                            {apptItem.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <span className="text-sm font-medium">${apptItem.price.toFixed(2)}</span>
                      </div>
                    </div>
                    {apptItem.notes && (
                      <p className="text-xs text-muted-foreground italic mt-1">{apptItem.notes}</p>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Add service form */}
            {canEdit && (
              showAddForm ? (
                <div className="rounded-md border p-3 space-y-2 bg-muted/20">
                  <p className="text-xs font-medium text-muted-foreground">Add service</p>
                  <select
                    value={addForm.serviceId}
                    onChange={e => handleServiceChange(e.target.value)}
                    className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background"
                  >
                    <option value="">Select service…</option>
                    {services.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                  <select
                    value={addForm.providerId}
                    onChange={e => setAddForm(f => ({ ...f, providerId: e.target.value }))}
                    className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background"
                  >
                    <option value="">Select provider…</option>
                    {providers.map(p => (
                      <option key={p.id} value={p.id}>{p.display_name}</option>
                    ))}
                  </select>
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <p className="text-xs text-muted-foreground mb-1">Start time</p>
                      <input
                        type="time"
                        value={addForm.startTime}
                        onChange={e => setAddForm(f => ({ ...f, startTime: e.target.value }))}
                        className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background"
                      />
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-muted-foreground mb-1">Price ($)</p>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={addForm.price}
                        onChange={e => setAddForm(f => ({ ...f, price: e.target.value }))}
                        placeholder="0.00"
                        className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background"
                      />
                    </div>
                  </div>
                  {addError && <p className="text-xs text-destructive">{addError}</p>}
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1" onClick={handleAddSubmit} disabled={addMutation.isPending}>
                      {addMutation.isPending ? 'Adding…' : 'Add service'}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => { setShowAddForm(false); setAddError(null) }}>
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Button variant="outline" size="sm" className="w-full" onClick={() => setShowAddForm(true)}>
                  + Add service
                </Button>
              )
            )}

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
