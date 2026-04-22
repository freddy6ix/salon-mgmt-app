import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchClients, createClient, type Client } from '@/api/clients'
import { listServices } from '@/api/services'
import { listProviders } from '@/api/providers'
import { type AppointmentRequest, convertRequest } from '@/api/appointmentRequests'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

interface ItemFormState {
  requestItemId: string
  serviceId: string
  providerId: string
  startTime: string
  durationMinutes: number
  price: string
  notes: string
}

interface Props {
  request: AppointmentRequest | null
  onClose: () => void
  onConverted: (appointmentDate: string) => void
}

export default function ConvertRequestDialog({ request, onClose, onConverted }: Props) {
  const qc = useQueryClient()

  const [clientMode, setClientMode] = useState<'new' | 'existing'>('new')
  const [newFirst, setNewFirst] = useState('')
  const [newLast, setNewLast] = useState('')
  const [newPhone, setNewPhone] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [clientQuery, setClientQuery] = useState('')
  const [selectedClient, setSelectedClient] = useState<Client | null>(null)
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const [appointmentDate, setAppointmentDate] = useState('')
  const [apptNotes, setApptNotes] = useState('')
  const [items, setItems] = useState<ItemFormState[]>([])
  const [error, setError] = useState<string | null>(null)

  const { data: services = [] } = useQuery({ queryKey: ['services'], queryFn: listServices })
  const { data: providers = [] } = useQuery({ queryKey: ['providers'], queryFn: listProviders })
  const { data: clientResults = [] } = useQuery({
    queryKey: ['clients', debouncedQuery],
    queryFn: () => searchClients(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
  })

  useEffect(() => {
    if (!request) return
    setClientMode('new')
    setNewFirst(request.first_name)
    setNewLast(request.last_name)
    setNewEmail(request.email)
    setNewPhone('')
    setSelectedClient(null)
    setClientQuery('')
    setAppointmentDate(request.desired_date)
    setApptNotes('')
    setError(null)
    setItems(request.items.map(ri => ({
      requestItemId: ri.id,
      serviceId: '',
      providerId: '',
      startTime: '09:00',
      durationMinutes: 60,
      price: '',
      notes: '',
    })))
  }, [request?.id])

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => setDebouncedQuery(clientQuery), 250)
  }, [clientQuery])

  function updateItem(idx: number, patch: Partial<ItemFormState>) {
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, ...patch } : it))
  }

  function handleServiceChange(idx: number, serviceId: string) {
    const svc = services.find(s => s.id === serviceId)
    updateItem(idx, {
      serviceId,
      durationMinutes: svc?.duration_minutes ?? 60,
      price: svc?.default_price != null ? String(svc.default_price) : '',
    })
  }

  const { mutateAsync, isPending } = useMutation({
    mutationFn: async () => {
      if (!request) return

      let clientId: string | undefined
      if (clientMode === 'existing') {
        if (!selectedClient) throw new Error('Select an existing client')
        clientId = selectedClient.id
      } else {
        if (!newFirst.trim() || !newLast.trim()) throw new Error('First and last name required')
        const created = await createClient({
          first_name: newFirst.trim(),
          last_name: newLast.trim(),
          cell_phone: newPhone.trim() || undefined,
          email: newEmail.trim() || undefined,
        })
        clientId = created.id
      }

      for (const item of items) {
        if (!item.serviceId) throw new Error('Select a service for each item')
        if (!item.providerId) throw new Error('Select a provider for each item')
      }

      return convertRequest(request.id, {
        client_id: clientId,
        appointment_date: appointmentDate,
        notes: apptNotes.trim() || undefined,
        items: items.map((it, idx) => ({
          request_item_id: it.requestItemId,
          service_id: it.serviceId,
          provider_id: it.providerId,
          sequence: idx + 1,
          start_time: `${appointmentDate}T${it.startTime}:00`,
          duration_minutes: it.durationMinutes,
          price: parseFloat(it.price) || 0,
          notes: it.notes.trim() || undefined,
        })),
      })
    },
    onSuccess: result => {
      if (result) {
        qc.invalidateQueries({ queryKey: ['all-requests'] })
        qc.invalidateQueries({ queryKey: ['appointments', result.appointment_date] })
        onConverted(result.appointment_date)
      }
    },
  })

  async function handleSubmit() {
    setError(null)
    try {
      await mutateAsync()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed')
    }
  }

  const clientReady = clientMode === 'new'
    ? newFirst.trim().length > 0 && newLast.trim().length > 0
    : selectedClient !== null
  const isValid = clientReady &&
    appointmentDate.length > 0 &&
    items.length > 0 &&
    items.every(it => it.serviceId && it.providerId)

  const serviceCategories = Array.from(new Set(services.map(s => s.category_name)))
  const activeProviders = providers.filter(p => p.has_appointments)

  return (
    <Dialog open={!!request} onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Convert to appointment</DialogTitle>
        </DialogHeader>

        {request && (
          <div className="space-y-5 py-1">

            {/* Request summary */}
            <div className="rounded-md bg-muted px-4 py-3 text-sm space-y-1">
              <p className="font-medium">{request.first_name} {request.last_name} · {request.email}</p>
              <p className="text-muted-foreground">
                Requested:{' '}
                {new Date(request.desired_date + 'T00:00:00').toLocaleDateString('en-CA', {
                  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                })}
                {request.desired_time_note && ` · ${request.desired_time_note}`}
              </p>
              {request.special_note && (
                <p className="text-muted-foreground italic">"{request.special_note}"</p>
              )}
            </div>

            {/* Client */}
            <div className="space-y-2">
              <Label>Client</Label>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={clientMode === 'new' ? 'default' : 'outline'}
                  onClick={() => setClientMode('new')}
                >
                  Create new
                </Button>
                <Button
                  size="sm"
                  variant={clientMode === 'existing' ? 'default' : 'outline'}
                  onClick={() => setClientMode('existing')}
                >
                  Link existing
                </Button>
              </div>

              {clientMode === 'new' && (
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <input
                    placeholder="First name *"
                    value={newFirst}
                    onChange={e => setNewFirst(e.target.value)}
                    className="border border-input rounded-md px-3 py-1.5 text-sm bg-background"
                  />
                  <input
                    placeholder="Last name *"
                    value={newLast}
                    onChange={e => setNewLast(e.target.value)}
                    className="border border-input rounded-md px-3 py-1.5 text-sm bg-background"
                  />
                  <input
                    placeholder="Cell phone"
                    value={newPhone}
                    onChange={e => setNewPhone(e.target.value)}
                    className="border border-input rounded-md px-3 py-1.5 text-sm bg-background"
                  />
                  <input
                    placeholder="Email"
                    value={newEmail}
                    onChange={e => setNewEmail(e.target.value)}
                    className="border border-input rounded-md px-3 py-1.5 text-sm bg-background"
                  />
                </div>
              )}

              {clientMode === 'existing' && (
                <div className="space-y-1 pt-1">
                  {selectedClient ? (
                    <div className="flex items-center justify-between rounded-md border px-3 py-2 bg-muted/40">
                      <span className="text-sm font-medium">
                        {selectedClient.first_name} {selectedClient.last_name}
                        {selectedClient.cell_phone && (
                          <span className="text-muted-foreground font-normal ml-2">
                            {selectedClient.cell_phone}
                          </span>
                        )}
                      </span>
                      <button
                        onClick={() => setSelectedClient(null)}
                        className="text-xs text-muted-foreground hover:text-foreground"
                      >
                        change
                      </button>
                    </div>
                  ) : (
                    <>
                      <input
                        placeholder="Search by name, phone, or email…"
                        value={clientQuery}
                        onChange={e => setClientQuery(e.target.value)}
                        className="w-full border border-input rounded-md px-3 py-1.5 text-sm bg-background"
                      />
                      {debouncedQuery.length >= 1 && (
                        <ul className="border rounded-md divide-y max-h-40 overflow-auto">
                          {clientResults.length === 0 ? (
                            <li className="px-3 py-2 text-sm text-muted-foreground">No clients found</li>
                          ) : (
                            clientResults.map(c => (
                              <li key={c.id}>
                                <button
                                  className="w-full text-left px-3 py-2 text-sm hover:bg-muted/40"
                                  onClick={() => { setSelectedClient(c); setClientQuery('') }}
                                >
                                  <span className="font-medium">{c.first_name} {c.last_name}</span>
                                  {c.cell_phone && (
                                    <span className="text-muted-foreground ml-2">{c.cell_phone}</span>
                                  )}
                                </button>
                              </li>
                            ))
                          )}
                        </ul>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Appointment date */}
            <div className="space-y-1.5">
              <Label>Appointment date</Label>
              <input
                type="date"
                value={appointmentDate}
                onChange={e => setAppointmentDate(e.target.value)}
                className="border border-input rounded-md px-3 py-1.5 text-sm bg-background"
              />
            </div>

            {/* Service items */}
            <div className="space-y-3">
              <Label>Services</Label>
              {items.map((item, idx) => {
                const reqItem = request.items[idx]
                return (
                  <div key={item.requestItemId} className="rounded-md border p-3 space-y-2">
                    <p className="text-xs text-muted-foreground">
                      Requested:{' '}
                      <span className="font-medium text-foreground">{reqItem.service_name}</span>
                      {' '}—{' '}{reqItem.preferred_provider_name}
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs text-muted-foreground">Service</label>
                        <select
                          value={item.serviceId}
                          onChange={e => handleServiceChange(idx, e.target.value)}
                          className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                        >
                          <option value="">— select —</option>
                          {serviceCategories.map(cat => (
                            <optgroup key={cat} label={cat}>
                              {services.filter(s => s.category_name === cat).map(s => (
                                <option key={s.id} value={s.id}>
                                  {s.name} ({s.duration_minutes}m)
                                </option>
                              ))}
                            </optgroup>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Provider</label>
                        <select
                          value={item.providerId}
                          onChange={e => updateItem(idx, { providerId: e.target.value })}
                          className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                        >
                          <option value="">— select —</option>
                          {activeProviders.map(p => (
                            <option key={p.id} value={p.id}>{p.display_name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Start time</label>
                        <input
                          type="time"
                          value={item.startTime}
                          onChange={e => updateItem(idx, { startTime: e.target.value })}
                          className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Duration (min)</label>
                        <input
                          type="number"
                          min="5"
                          step="5"
                          value={item.durationMinutes}
                          onChange={e => updateItem(idx, { durationMinutes: parseInt(e.target.value) || 60 })}
                          className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Price ($)</label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.price}
                          onChange={e => updateItem(idx, { price: e.target.value })}
                          placeholder="0.00"
                          className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Notes</label>
                        <input
                          type="text"
                          value={item.notes}
                          onChange={e => updateItem(idx, { notes: e.target.value })}
                          placeholder="Optional…"
                          className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Appointment notes */}
            <div className="space-y-1.5">
              <Label htmlFor="appt-notes">Appointment notes</Label>
              <textarea
                id="appt-notes"
                value={apptNotes}
                onChange={e => setApptNotes(e.target.value)}
                rows={2}
                placeholder="Optional…"
                className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!isValid || isPending}>
            {isPending ? 'Creating…' : 'Create appointment'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
