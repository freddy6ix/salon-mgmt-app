import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createTimeBlock, updateTimeBlock, deleteTimeBlock, type TimeBlock } from '@/api/timeBlocks'
import type { Provider } from '@/api/providers'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

interface Props {
  block: TimeBlock | null  // when set: edit
  creating: { time: string; providerId: string } | null  // when set: create
  date: string
  providers: Provider[]
  onClose: () => void
}

function timeFromIso(iso: string): string {
  const tail = iso.split('T')[1] ?? iso
  const [h, m] = tail.split(':')
  return `${h}:${m}`
}

export default function TimeBlockEditDialog({ block, creating, date, providers, onClose }: Props) {
  const open = block !== null || creating !== null
  const isEdit = block !== null
  const qc = useQueryClient()

  const [providerId, setProviderId] = useState('')
  const [time, setTime] = useState('09:00')
  const [duration, setDuration] = useState('30')
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (block) {
      setProviderId(block.provider_id)
      setTime(timeFromIso(block.start_time))
      setDuration(String(block.duration_minutes))
      setNote(block.note ?? '')
    } else if (creating) {
      setProviderId(creating.providerId)
      setTime(creating.time)
      setDuration('30')
      setNote('')
    }
    setError(null)
  }, [block?.id, creating?.time, creating?.providerId])

  const refresh = () => qc.invalidateQueries({ queryKey: ['time-blocks', date] })

  const saveMut = useMutation({
    mutationFn: () => {
      const startIso = `${date}T${time}:00`
      const dur = parseInt(duration, 10)
      const trimmedNote = note.trim() || null
      if (isEdit && block) {
        return updateTimeBlock(block.id, {
          provider_id: providerId,
          start_time: startIso,
          duration_minutes: dur,
          note: trimmedNote,
        })
      }
      return createTimeBlock({
        provider_id: providerId,
        start_time: startIso,
        duration_minutes: dur,
        note: trimmedNote,
      })
    },
    onSuccess: () => { refresh(); onClose() },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Save failed'),
  })

  const deleteMut = useMutation({
    mutationFn: () => deleteTimeBlock(block!.id),
    onSuccess: () => { refresh(); onClose() },
  })

  function submit() {
    if (!providerId) { setError('Pick a provider'); return }
    const dur = parseInt(duration, 10)
    if (!dur || dur < 5) { setError('Duration must be at least 5 minutes'); return }
    setError(null)
    saveMut.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit time block' : 'New time block'}</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <Label>Provider</Label>
            <select
              value={providerId}
              onChange={e => setProviderId(e.target.value)}
              className="w-full mt-1 border border-input rounded-md px-2 py-1.5 text-sm bg-background"
            >
              <option value="">Select…</option>
              {providers.map(p => (
                <option key={p.id} value={p.id}>{p.display_name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Start time</Label>
              <input
                type="time"
                value={time}
                onChange={e => setTime(e.target.value)}
                className="w-full mt-1 border border-input rounded-md px-2 py-1.5 text-sm bg-background"
              />
            </div>
            <div>
              <Label>Duration (min)</Label>
              <input
                type="number" min={5}
                value={duration}
                onChange={e => setDuration(e.target.value)}
                className="w-full mt-1 border border-input rounded-md px-2 py-1.5 text-sm bg-background"
              />
            </div>
          </div>

          <div>
            <Label>Note <span className="text-muted-foreground font-normal">— shown on the grid</span></Label>
            <textarea
              rows={2}
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Lunch, training, sick…"
              className="w-full mt-1 border border-input rounded-md px-2 py-1.5 text-sm bg-background resize-none"
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex gap-2 pt-2 border-t">
            <Button onClick={submit} disabled={saveMut.isPending} className="flex-1">
              {saveMut.isPending ? 'Saving…' : isEdit ? 'Save' : 'Create block'}
            </Button>
            {isEdit && (
              <Button
                variant="outline"
                onClick={() => deleteMut.mutate()}
                disabled={deleteMut.isPending}
              >
                Delete
              </Button>
            )}
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
