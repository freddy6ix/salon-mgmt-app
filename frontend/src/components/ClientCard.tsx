import { useState } from 'react'
import { format, parseISO, isToday, isFuture } from 'date-fns'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getClient, getClientHistory, updateClientNotes } from '@/api/clients'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

type Tab = 'profile' | 'appointments' | 'notes'

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

  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const upcoming = visits.filter(v =>
    (v.status === 'confirmed' || v.status === 'in_progress') && v.date >= todayStr
  ).reverse()
  const past = visits.filter(v => v.date < todayStr || v.status === 'completed' || v.status === 'cancelled' || v.status === 'no_show')

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
          {(['profile', 'appointments', 'notes'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-2 text-sm capitalize border-b-2 -mb-px transition-colors ${
                tab === t
                  ? 'border-foreground font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {t === 'notes' ? 'Notes' : t === 'appointments' ? 'Appointments' : 'Profile'}
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
                  </div>

                  {(client.no_show_count > 0 || client.late_cancellation_count > 0) && (
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

                  {client.special_instructions && (
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
                        <VisitRow key={visit.appointment_id} visit={visit} />
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

function VisitRow({ visit }: { visit: { appointment_id: string; date: string; status: string; items: { service_name: string; provider_name: string; price: number }[] } }) {
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
