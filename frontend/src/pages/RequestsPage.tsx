import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import {
  type AppointmentRequest,
  listAllRequests,
  reviewRequest,
} from '@/api/appointmentRequests'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const STATUS_LABELS: Record<AppointmentRequest['status'], string> = {
  new: 'New',
  reviewed: 'Under review',
  converted: 'Confirmed',
  declined: 'Declined',
}

const STATUS_VARIANT: Record<
  AppointmentRequest['status'],
  'default' | 'secondary' | 'outline' | 'destructive'
> = {
  new: 'secondary',
  reviewed: 'default',
  converted: 'outline',
  declined: 'destructive',
}

// ── Review dialog ─────────────────────────────────────────────────────────────

function ReviewDialog({
  request,
  onClose,
  onSave,
}: {
  request: AppointmentRequest | null
  onClose: () => void
  onSave: (id: string, status: AppointmentRequest['status'], notes: string) => Promise<void>
}) {
  const [newStatus, setNewStatus] = useState<AppointmentRequest['status']>('reviewed')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSave() {
    if (!request) return
    setSaving(true)
    setError(null)
    try {
      await onSave(request.id, newStatus, notes)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={!!request} onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Review request</DialogTitle>
        </DialogHeader>

        {request && (
          <div className="space-y-4 py-2">
            <div className="rounded-md bg-muted px-4 py-3 space-y-1 text-sm">
              <p className="font-medium">{request.first_name} {request.last_name}</p>
              <p className="text-muted-foreground">{request.email}</p>
              <p className="mt-1">
                {new Date(request.desired_date + 'T00:00:00').toLocaleDateString('en-CA', {
                  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                })}
                {request.desired_time_note && ` · ${request.desired_time_note}`}
              </p>
              <ul className="mt-1 space-y-0.5">
                {request.items.map(item => (
                  <li key={item.id} className="text-muted-foreground">
                    • {item.service_name} — {item.preferred_provider_name}
                  </li>
                ))}
              </ul>
              {request.special_note && (
                <p className="mt-1 italic text-muted-foreground">"{request.special_note}"</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Update status</Label>
              <Select
                value={newStatus}
                onValueChange={v => v && setNewStatus(v as AppointmentRequest['status'])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="reviewed">Under review</SelectItem>
                  <SelectItem value="converted">Confirmed (book manually on schedule)</SelectItem>
                  <SelectItem value="declined">Declined</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="staff-notes">
                Staff notes <span className="text-muted-foreground text-xs">(shown to client if declined)</span>
              </Label>
              <textarea
                id="staff-notes"
                className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[80px] resize-none"
                placeholder="Optional notes…"
                value={notes}
                onChange={e => setNotes(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

const FILTER_OPTIONS = [
  { value: '', label: 'All' },
  { value: 'new', label: 'New' },
  { value: 'reviewed', label: 'Under review' },
  { value: 'converted', label: 'Confirmed' },
  { value: 'declined', label: 'Declined' },
]

export default function RequestsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [filter, setFilter] = useState('')
  const [reviewing, setReviewing] = useState<AppointmentRequest | null>(null)

  const { data: requests = [], isLoading } = useQuery({
    queryKey: ['all-requests', filter],
    queryFn: () => listAllRequests(filter || undefined),
  })

  const { mutateAsync: doReview } = useMutation({
    mutationFn: ({ id, status, notes }: { id: string; status: AppointmentRequest['status']; notes: string }) =>
      reviewRequest(id, { status, staff_notes: notes || undefined }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['all-requests'] }),
  })

  async function handleSave(id: string, status: AppointmentRequest['status'], notes: string) {
    await doReview({ id, status, notes })
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="border-b bg-background px-4 py-2 flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
          <ChevronLeft className="h-4 w-4 mr-1" />
          Schedule
        </Button>
        <span className="font-semibold">Appointment Requests</span>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2">
          {FILTER_OPTIONS.map(opt => (
            <Button
              key={opt.value}
              variant={filter === opt.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(opt.value)}
            >
              {opt.label}
            </Button>
          ))}
        </div>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">Loading…</p>
        ) : requests.length === 0 ? (
          <p className="text-muted-foreground text-sm py-8 text-center">No requests found.</p>
        ) : (
          <div className="space-y-3">
            {requests.map(req => (
              <Card key={req.id} className="cursor-pointer hover:border-foreground/30 transition-colors"
                onClick={() => setReviewing(req)}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base">
                      {req.first_name} {req.last_name}
                    </CardTitle>
                    <Badge variant={STATUS_VARIANT[req.status]}>
                      {STATUS_LABELS[req.status]}
                    </Badge>
                  </div>
                  <CardDescription className="text-xs">
                    {new Date(req.desired_date + 'T00:00:00').toLocaleDateString('en-CA', {
                      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
                    })}
                    {req.desired_time_note && ` · ${req.desired_time_note}`}
                    {' · '}submitted {new Date(req.submitted_at).toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <ul className="text-sm space-y-0.5">
                    {req.items.map(item => (
                      <li key={item.id} className="text-muted-foreground">
                        • {item.service_name} — {item.preferred_provider_name}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      <ReviewDialog
        request={reviewing}
        onClose={() => setReviewing(null)}
        onSave={handleSave}
      />
    </div>
  )
}
