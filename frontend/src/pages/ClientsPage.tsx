import { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  type Visit,
  type ColourNote,
  searchClients,
  getClient,
  getClientHistory,
  listColourNotes,
  createColourNote,
  updateClientNotes,
  deleteClient,
} from '@/api/clients'
import { updateAppointmentStatus } from '@/api/appointments'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Star, ChevronRight } from 'lucide-react'

// ── Client list ───────────────────────────────────────────────────────────────

function ClientList({
  selectedId,
  onSelect,
}: {
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const [query, setQuery] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setDebouncedQ(query), 200)
  }, [query])

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ['clients', debouncedQ],
    queryFn: () => searchClients(debouncedQ),
  })

  return (
    <div className="flex flex-col h-full border-r bg-white">
      <div className="p-3 border-b">
        <input
          type="search"
          placeholder="Search clients…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full border border-input rounded-md px-3 py-1.5 text-sm bg-background"
        />
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <p className="p-4 text-sm text-muted-foreground">Loading…</p>
        ) : clients.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">
            {debouncedQ ? 'No clients found.' : 'No clients yet.'}
          </p>
        ) : (
          <ul>
            {clients.map(c => (
              <li key={c.id}>
                <button
                  onClick={() => onSelect(c.id)}
                  className={`w-full text-left px-4 py-3 flex items-center gap-2 hover:bg-muted/40 transition-colors border-b border-muted/60
                    ${selectedId === c.id ? 'bg-muted/60' : ''}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-medium truncate">
                        {c.last_name}, {c.first_name}
                      </span>
                      {c.is_vip && <Star size={11} className="text-amber-500 fill-amber-500 flex-shrink-0" />}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {[c.cell_phone, c.email].filter(Boolean).join(' · ') || 'No contact info'}
                    </p>
                  </div>
                  {(c.no_show_count > 0 || c.late_cancellation_count > 0) && (
                    <span className="text-xs text-destructive flex-shrink-0">
                      {c.no_show_count > 0 && `${c.no_show_count} NS`}
                      {c.no_show_count > 0 && c.late_cancellation_count > 0 && ' · '}
                      {c.late_cancellation_count > 0 && `${c.late_cancellation_count} LC`}
                    </span>
                  )}
                  <ChevronRight size={14} className="text-muted-foreground flex-shrink-0" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

// ── Colour notes ──────────────────────────────────────────────────────────────

function ColourNotes({ clientId }: { clientId: string }) {
  const qc = useQueryClient()
  const [newDate, setNewDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [newText, setNewText] = useState('')
  const [adding, setAdding] = useState(false)

  const { data: notes = [] } = useQuery({
    queryKey: ['colour-notes', clientId],
    queryFn: () => listColourNotes(clientId),
  })

  const { mutate, isPending } = useMutation({
    mutationFn: () => createColourNote(clientId, newDate, newText.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['colour-notes', clientId] })
      setNewText('')
      setAdding(false)
    },
  })

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Colour notes</h3>
        {!adding && (
          <Button size="sm" variant="outline" onClick={() => setAdding(true)}>
            Add note
          </Button>
        )}
      </div>

      {adding && (
        <div className="rounded-md border p-3 space-y-2">
          <input
            type="date"
            value={newDate}
            onChange={e => setNewDate(e.target.value)}
            className="border border-input rounded-md px-2 py-1 text-sm bg-background"
          />
          <textarea
            value={newText}
            onChange={e => setNewText(e.target.value)}
            placeholder="Formula, developer, timing…"
            rows={3}
            className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => mutate()}
              disabled={!newText.trim() || isPending}
            >
              {isPending ? 'Saving…' : 'Save'}
            </Button>
            <Button size="sm" variant="outline" onClick={() => setAdding(false)} disabled={isPending}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {notes.length === 0 && !adding ? (
        <p className="text-sm text-muted-foreground">No colour notes yet.</p>
      ) : (
        <ul className="space-y-2">
          {notes.map((n: ColourNote) => (
            <li key={n.id} className="rounded-md border p-3 text-sm space-y-1">
              <p className="text-xs text-muted-foreground font-medium">
                {new Date(n.note_date + 'T00:00:00').toLocaleDateString('en-CA', {
                  year: 'numeric', month: 'short', day: 'numeric',
                })}
              </p>
              <p className="whitespace-pre-wrap">{n.note_text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Visit history ─────────────────────────────────────────────────────────────

const VISIT_STATUS_LABEL: Record<string, string> = {
  confirmed: 'Confirmed',
  completed: 'Completed',
  cancelled: 'Cancelled',
  no_show: 'No-show',
  in_progress: 'In progress',
}

function VisitRow({ visit, onCancel }: { visit: Visit; onCancel?: (id: string) => void }) {
  const todayStr = new Date().toISOString().slice(0, 10)
  const isUpcoming = visit.date >= todayStr
  return (
    <li className="rounded-md border p-3 text-sm space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">
          {new Date(visit.date + 'T00:00:00').toLocaleDateString('en-CA', {
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
          })}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {VISIT_STATUS_LABEL[visit.status] ?? visit.status}
          </span>
          {isUpcoming && visit.status === 'confirmed' && onCancel && (
            <button
              onClick={() => onCancel(visit.appointment_id)}
              className="text-xs text-destructive hover:underline"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
      <ul className="space-y-0.5">
        {visit.items.map((item, i) => (
          <li key={i} className="text-muted-foreground text-xs">
            <span className="tabular-nums text-foreground">
              {new Date(item.start_time).toLocaleTimeString('en-CA', {
                hour: 'numeric', minute: '2-digit', hour12: true,
              })}
            </span>
            {' · '}{item.service_name} — {item.provider_name}
            {' · '}${item.price.toFixed(2)}
          </li>
        ))}
      </ul>
      {visit.items.length > 0 && (
        <p className="text-xs font-medium pt-0.5">
          Total: ${visit.items.reduce((sum, i) => sum + i.price, 0).toFixed(2)}
        </p>
      )}
    </li>
  )
}

function VisitHistory({ clientId }: { clientId: string }) {
  const qc = useQueryClient()
  const todayStr = new Date().toISOString().slice(0, 10)

  const { data: visits = [], isLoading } = useQuery({
    queryKey: ['client-history', clientId],
    queryFn: () => getClientHistory(clientId),
  })

  const { mutate: cancelAppt } = useMutation({
    mutationFn: (appointmentId: string) => updateAppointmentStatus(appointmentId, 'cancelled'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['client-history', clientId] }),
  })

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>
  if (visits.length === 0) return <p className="text-sm text-muted-foreground">No visits yet.</p>

  const upcoming = visits.filter(v => v.date >= todayStr).reverse()
  const past = visits.filter(v => v.date < todayStr)

  return (
    <div className="space-y-5">
      {upcoming.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Upcoming</h3>
          <ul className="space-y-2">
            {upcoming.map(v => <VisitRow key={v.appointment_id} visit={v} onCancel={id => cancelAppt(id)} />)}
          </ul>
        </div>
      )}
      {past.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">History</h3>
          <ul className="space-y-2">
            {past.map(v => <VisitRow key={v.appointment_id} visit={v} />)}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Client detail panel ───────────────────────────────────────────────────────

type Tab = 'history' | 'colour' | 'notes'

function ClientDetail({ clientId, onDeleted }: { clientId: string; onDeleted: () => void }) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('history')
  const [editingNotes, setEditingNotes] = useState(false)
  const [notesText, setNotesText] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: client, isLoading } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => getClient(clientId),
  })

  useEffect(() => {
    if (client) setNotesText(client.special_instructions ?? '')
  }, [client?.id])

  const { mutate: saveNotes, isPending: savingNotes } = useMutation({
    mutationFn: () => updateClientNotes(clientId, notesText.trim() || null),
    onSuccess: updated => {
      qc.setQueryData(['client', clientId], updated)
      setEditingNotes(false)
    },
  })

  const { mutate: doDelete, isPending: deleting } = useMutation({
    mutationFn: () => deleteClient(clientId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] })
      onDeleted()
    },
    onError: (e: Error) => {
      setDeleteError(e.message || 'Could not delete client')
      setConfirmDelete(false)
    },
  })

  if (isLoading || !client) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>
  }

  const TABS: { id: Tab; label: string }[] = [
    { id: 'history', label: 'Visit history' },
    { id: 'colour', label: 'Colour notes' },
    { id: 'notes', label: 'Special instructions' },
  ]

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-4 border-b bg-white flex-shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold">
                {client.first_name} {client.last_name}
              </h2>
              {client.is_vip && (
                <Badge variant="outline" className="text-amber-600 border-amber-400 text-xs">VIP</Badge>
              )}
              {client.pronouns && (
                <span className="text-xs text-muted-foreground">{client.pronouns}</span>
              )}
            </div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-sm text-muted-foreground">
              {client.cell_phone && <span>{client.cell_phone}</span>}
              {client.email && <span>{client.email}</span>}
            </div>
          </div>
          <div className="flex items-start gap-4 flex-shrink-0">
            <div className="flex gap-3 text-xs text-right">
              {client.no_show_count > 0 && (
                <div className="text-destructive">
                  <div className="font-semibold text-base leading-none">{client.no_show_count}</div>
                  <div>no-shows</div>
                </div>
              )}
              {client.late_cancellation_count > 0 && (
                <div className="text-amber-600">
                  <div className="font-semibold text-base leading-none">{client.late_cancellation_count}</div>
                  <div>late cancel</div>
                </div>
              )}
            </div>
            {confirmDelete ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-destructive">Delete this client?</span>
                <Button size="sm" variant="destructive" onClick={() => doDelete()} disabled={deleting}>
                  {deleting ? 'Deleting…' : 'Confirm'}
                </Button>
                <Button size="sm" variant="outline" onClick={() => { setConfirmDelete(false); setDeleteError(null) }} disabled={deleting}>
                  Cancel
                </Button>
              </div>
            ) : (
              <Button size="sm" variant="ghost" className="text-muted-foreground hover:text-destructive" onClick={() => { setDeleteError(null); setConfirmDelete(true) }}>
                Delete
              </Button>
            )}
          </div>
        </div>
        {deleteError && (
          <p className="mt-2 text-xs text-destructive">{deleteError}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b bg-white flex-shrink-0 px-6">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`py-2.5 px-1 mr-5 text-sm border-b-2 transition-colors
              ${tab === t.id
                ? 'border-primary text-foreground font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-auto p-6">
        {tab === 'history' && <VisitHistory clientId={clientId} />}
        {tab === 'colour' && <ColourNotes clientId={clientId} />}
        {tab === 'notes' && (
          <div className="space-y-3 max-w-lg">
            <h3 className="text-sm font-medium">Special instructions</h3>
            {editingNotes ? (
              <>
                <textarea
                  value={notesText}
                  onChange={e => setNotesText(e.target.value)}
                  rows={5}
                  placeholder="Allergies, preferences, access needs…"
                  className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => saveNotes()} disabled={savingNotes}>
                    {savingNotes ? 'Saving…' : 'Save'}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => {
                    setNotesText(client.special_instructions ?? '')
                    setEditingNotes(false)
                  }} disabled={savingNotes}>
                    Cancel
                  </Button>
                </div>
              </>
            ) : (
              <div
                onClick={() => setEditingNotes(true)}
                className="min-h-[80px] rounded-md border border-dashed px-3 py-2 text-sm cursor-pointer hover:bg-muted/30 transition-colors"
              >
                {client.special_instructions ? (
                  <p className="whitespace-pre-wrap">{client.special_instructions}</p>
                ) : (
                  <p className="text-muted-foreground">Click to add instructions…</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ClientsPage() {
  const [searchParams] = useSearchParams()
  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get('id'))

  return (
    <div className="flex h-full overflow-hidden bg-muted/30">
      <div className="w-72 flex-shrink-0 h-full">
        <ClientList selectedId={selectedId} onSelect={setSelectedId} />
      </div>

      <div className="flex-1 min-w-0 h-full overflow-hidden bg-white">
        {selectedId ? (
          <ClientDetail key={selectedId} clientId={selectedId} onDeleted={() => setSelectedId(null)} />
        ) : (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            Select a client to view their profile.
          </div>
        )}
      </div>
    </div>
  )
}
