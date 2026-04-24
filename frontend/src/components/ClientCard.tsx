import { useState } from 'react'
import { format, parseISO, isToday } from 'date-fns'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getClient, getClientHistory, updateClient, updateClientNotes, listColourNotes, createColourNote } from '@/api/clients'
import { updateAppointmentStatus } from '@/api/appointments'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

type Tab = 'profile' | 'appointments' | 'colour' | 'notes'

interface Props {
  clientId: string | null
  onClose: () => void
}

const VISIT_STATUS_LABEL: Record<string, string> = {
  confirmed: 'Upcoming',
  in_progress: 'In progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  no_show: 'No show',
}

const VISIT_STATUS_COLOR: Record<string, string> = {
  confirmed: 'text-blue-600',
  in_progress: 'text-green-600',
  completed: 'text-muted-foreground',
  cancelled: 'text-destructive',
  no_show: 'text-orange-600',
}

export default function ClientCard({ clientId, onClose }: Props) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('profile')
  const [notesValue, setNotesValue] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editFirst, setEditFirst] = useState('')
  const [editLast, setEditLast] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editPhone, setEditPhone] = useState('')
  const [editError, setEditError] = useState<string | null>(null)
  const [newNoteText, setNewNoteText] = useState('')
  const [newNoteDate, setNewNoteDate] = useState(format(new Date(), 'yyyy-MM-dd'))

  const { data: client, isLoading: clientLoading } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => getClient(clientId!),
    enabled: !!clientId,
  })

  const { data: visits = [], isLoading: historyLoading } = useQuery({
    queryKey: ['client-history', clientId],
    queryFn: () => getClientHistory(clientId!),
    enabled: !!clientId && tab === 'appointments',
  })

  const notesMutation = useMutation({
    mutationFn: (notes: string | null) => updateClientNotes(clientId!, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', clientId] })
      qc.invalidateQueries({ queryKey: ['appointments'] })
      setNotesValue(null)
    },
  })

  const updateMutation = useMutation({
    mutationFn: () => updateClient(clientId!, {
      first_name: editFirst.trim(),
      last_name: editLast.trim(),
      email: editEmail.trim() || null,
      cell_phone: editPhone.trim() || null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', clientId] })
      qc.invalidateQueries({ queryKey: ['clients'] })
      setEditing(false)
      setEditError(null)
    },
    onError: (err: unknown) => setEditError((err as Error).message ?? 'Save failed'),
  })

  function startEdit() {
    if (!client) return
    setEditFirst(client.first_name)
    setEditLast(client.last_name)
    setEditEmail(client.email ?? '')
    setEditPhone(client.cell_phone ?? '')
    setEditError(null)
    setEditing(true)
  }

  const { data: colourNotes = [], isLoading: colourLoading } = useQuery({
    queryKey: ['client-colour-notes', clientId],
    queryFn: () => listColourNotes(clientId!),
    enabled: !!clientId && tab === 'colour',
  })

  const addColourNote = useMutation({
    mutationFn: () => createColourNote(clientId!, newNoteDate, newNoteText),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client-colour-notes', clientId] })
      setNewNoteText('')
      setNewNoteDate(format(new Date(), 'yyyy-MM-dd'))
    },
  })

  const cancelAppt = useMutation({
    mutationFn: (appointmentId: string) => updateAppointmentStatus(appointmentId, 'cancelled'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['client-history', clientId] }),
  })

  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const upcoming = visits.filter(v => v.date >= todayStr).reverse()
  const past = visits.filter(v => v.date < todayStr)

  const currentNotes = notesValue !== null ? notesValue : (client?.special_instructions ?? '')

  if (!clientId) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />

      <div className="relative w-[440px] bg-white h-full flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between px-5 pt-5 pb-3 border-b flex-shrink-0">
          {clientLoading ? (
            <div className="h-6 w-40 bg-muted animate-pulse rounded" />
          ) : client ? (
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold">
                  {client.first_name} {client.last_name}
                </h2>
                {client.is_vip && (
                  <Badge variant="default" className="text-xs">VIP</Badge>
                )}
              </div>
              {client.pronouns && (
                <p className="text-xs text-muted-foreground mt-0.5">{client.pronouns}</p>
              )}
            </div>
          ) : (
            <span className="text-muted-foreground text-sm">Client not found</span>
          )}
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-xl leading-none mt-0.5 ml-4"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b flex-shrink-0 px-5">
          {(['profile', 'appointments', 'colour', 'notes'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-2 text-sm capitalize border-b-2 -mb-px transition-colors ${
                tab === t
                  ? 'border-foreground font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {t === 'profile' ? 'Profile' : t === 'appointments' ? 'Appointments' : t === 'colour' ? 'Colour' : 'Notes'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">

          {/* ── Profile tab ── */}
          {tab === 'profile' && (
            <div className="p-5 space-y-4">
              {clientLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-4 bg-muted animate-pulse rounded" />
                  ))}
                </div>
              ) : client ? (
                <>
                  {editing ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs">First name</Label>
                          <Input value={editFirst} onChange={e => setEditFirst(e.target.value)} />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Last name</Label>
                          <Input value={editLast} onChange={e => setEditLast(e.target.value)} />
                        </div>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Email</Label>
                        <Input type="email" value={editEmail} onChange={e => setEditEmail(e.target.value)} placeholder="optional" />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Phone</Label>
                        <Input type="tel" value={editPhone} onChange={e => setEditPhone(e.target.value)} placeholder="optional" />
                      </div>
                      {editError && <p className="text-xs text-destructive">{editError}</p>}
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          className="flex-1"
                          disabled={updateMutation.isPending || !editFirst.trim() || !editLast.trim()}
                          onClick={() => updateMutation.mutate()}
                        >
                          {updateMutation.isPending ? 'Saving…' : 'Save'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditing(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-2">
                        {client.email && (
                          <div className="flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground w-16 shrink-0">Email</span>
                            <a href={`mailto:${client.email}`} className="hover:underline truncate">
                              {client.email}
                            </a>
                          </div>
                        )}
                        {client.cell_phone && (
                          <div className="flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground w-16 shrink-0">Phone</span>
                            <a href={`tel:${client.cell_phone}`} className="hover:underline">
                              {client.cell_phone}
                            </a>
                          </div>
                        )}
                        {!client.email && !client.cell_phone && (
                          <p className="text-sm text-muted-foreground">No contact info on file.</p>
                        )}
                      </div>
                      <Button size="sm" variant="outline" onClick={startEdit}>
                        Edit profile
                      </Button>
                    </>
                  )}

                  {(client.no_show_count > 0 || client.late_cancellation_count > 0) && !editing && (
                    <>
                      <Separator />
                      <div className="space-y-1.5">
                        {client.no_show_count > 0 && (
                          <div className="flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground w-32 shrink-0">No-shows</span>
                            <span className="font-medium text-orange-600">{client.no_show_count}</span>
                          </div>
                        )}
                        {client.late_cancellation_count > 0 && (
                          <div className="flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground w-32 shrink-0">Late cancellations</span>
                            <span className="font-medium text-orange-600">{client.late_cancellation_count}</span>
                          </div>
                        )}
                      </div>
                    </>
                  )}

                  {client.special_instructions && !editing && (
                    <>
                      <Separator />
                      <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800">
                        {client.special_instructions}
                      </div>
                    </>
                  )}
                </>
              ) : null}
            </div>
          )}

          {/* ── Appointments tab ── */}
          {tab === 'appointments' && (
            <div className="p-5 space-y-5">
              {historyLoading ? (
                <p className="text-sm text-muted-foreground text-center py-8">Loading…</p>
              ) : (
                <>
                  {upcoming.length > 0 && (
                    <div className="space-y-2">
                      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Upcoming
                      </h3>
                      {upcoming.map(visit => (
                        <VisitRow key={visit.appointment_id} visit={visit} onCancel={id => cancelAppt.mutate(id)} />
                      ))}
                    </div>
                  )}

                  {upcoming.length > 0 && past.length > 0 && <Separator />}

                  {past.length > 0 && (
                    <div className="space-y-2">
                      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        History
                      </h3>
                      {past.map(visit => (
                        <VisitRow key={visit.appointment_id} visit={visit} />
                      ))}
                    </div>
                  )}

                  {upcoming.length === 0 && past.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-8">No appointments on record</p>
                  )}
                </>
              )}
            </div>
          )}

          {/* ── Colour tab ── */}
          {tab === 'colour' && (
            <div className="p-5 space-y-4">
              {/* Add new note */}
              <div className="rounded-md border p-3 space-y-2 bg-muted/20">
                <p className="text-xs font-medium text-muted-foreground">New formula / service note</p>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={newNoteDate}
                    onChange={e => setNewNoteDate(e.target.value)}
                    className="border border-input rounded-md px-2 py-1.5 text-sm bg-background"
                  />
                </div>
                <textarea
                  rows={4}
                  value={newNoteText}
                  onChange={e => setNewNoteText(e.target.value)}
                  placeholder="e.g. 7N + 20vol, foils, 35min..."
                  className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
                />
                {addColourNote.isError && (
                  <p className="text-xs text-destructive">Save failed</p>
                )}
                <Button
                  size="sm"
                  className="w-full"
                  disabled={!newNoteText.trim() || addColourNote.isPending}
                  onClick={() => addColourNote.mutate()}
                >
                  {addColourNote.isPending ? 'Saving…' : 'Save formula'}
                </Button>
              </div>

              {/* Existing notes */}
              {colourLoading ? (
                <p className="text-sm text-muted-foreground text-center py-4">Loading…</p>
              ) : colourNotes.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No colour notes yet</p>
              ) : (
                <div className="space-y-3">
                  {colourNotes.map(note => (
                    <div key={note.id} className="border rounded-md px-3 py-2 space-y-1">
                      <p className="text-xs text-muted-foreground">
                        {format(parseISO(note.note_date + 'T12:00:00'), 'MMM d, yyyy')}
                      </p>
                      <p className="text-sm whitespace-pre-wrap">{note.note_text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Notes tab ── */}
          {tab === 'notes' && (
            <div className="p-5 space-y-3">
              <p className="text-xs text-muted-foreground">
                Shown as an alert whenever this client has an appointment.
              </p>
              {clientLoading ? (
                <div className="h-24 bg-muted animate-pulse rounded" />
              ) : (
                <>
                  <textarea
                    rows={6}
                    value={currentNotes}
                    onChange={e => setNotesValue(e.target.value)}
                    placeholder="Allergies, preferences, standing instructions…"
                    className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
                  />
                  {notesMutation.isError && (
                    <p className="text-xs text-destructive">Save failed</p>
                  )}
                  <Button
                    className="w-full"
                    disabled={notesMutation.isPending || currentNotes === (client?.special_instructions ?? '')}
                    onClick={() => notesMutation.mutate(currentNotes || null)}
                  >
                    {notesMutation.isPending ? 'Saving…' : 'Save notes'}
                  </Button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function VisitRow({ visit, onCancel }: {
  visit: { appointment_id: string; date: string; status: string; items: { service_name: string; provider_name: string; price: number }[] }
  onCancel?: (id: string) => void
}) {
  const dateObj = parseISO(visit.date + 'T12:00:00')
  const total = visit.items.reduce((sum, i) => sum + i.price, 0)
  return (
    <div className="border rounded-md px-3 py-2 space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium">
          {isToday(dateObj) ? 'Today' : format(dateObj, 'MMM d, yyyy')}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">${total.toFixed(2)}</span>
          <span className={`text-xs ${VISIT_STATUS_COLOR[visit.status] ?? ''}`}>
            {VISIT_STATUS_LABEL[visit.status] ?? visit.status}
          </span>
          {onCancel && visit.status === 'confirmed' && (
            <button
              onClick={() => onCancel(visit.appointment_id)}
              className="text-xs text-destructive hover:underline"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
      {visit.items.map((item, i) => (
        <p key={i} className="text-xs text-muted-foreground">
          {item.service_name} · {item.provider_name}
        </p>
      ))}
    </div>
  )
}
